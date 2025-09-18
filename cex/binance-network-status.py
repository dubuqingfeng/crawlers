import requests
import json
import schedule
import time
from difflib import unified_diff
import logging
import os

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别
    format="%(asctime)s - %(levelname)s - %(message)s",  # 日志格式，包括时间、日志级别和消息
    datefmt="%Y-%m-%d %H:%M:%S",  # 时间格式
    handlers=[
        logging.FileHandler("./logs/binance_network_status.log"),  # 将日志写入文件
        logging.StreamHandler()  # 同时输出到控制台
    ]
)

jsonfile = "./json/binance_network_status_api_data.json"

# pip install requests schedule
# https://www.binance.com/zh-CN/network
# 存储上一次的API返回值
last_response = None
# 从文件里尝试读取上一次的API返回值
try:
    with open(jsonfile, "r") as file:
        last_response = json.load(file)
except FileNotFoundError:
    logging.warning("未找到上一次的API返回值")
except json.JSONDecodeError:
    logging.warning("上一次的API返回值无效")

coin_network_deposit_status = {}
coin_network_withdraw_status = {}

def _build_card(title, message, parsed):
    overview_lines = []
    elements = []
    if parsed:
        total = len(parsed)
        deposit_changes = sum(1 for x in parsed if x.get('field') == 'deposit')
        withdraw_changes = sum(1 for x in parsed if x.get('field') == 'withdraw')
        added = sum(1 for x in parsed if x.get('type') == 'added')
        closed = sum(1 for x in parsed if x.get('type') == 'closed')
        overview_lines.append(f"变更: {total} · 充值变更: {deposit_changes} · 提现变更: {withdraw_changes} · 新增: {added} · 关闭: {closed}")
        elements.append({
            "tag": "note",
            "elements": [{"tag": "plain_text", "content": " | ".join(overview_lines)}]
        })
        for item in parsed:
            tag_text = '变更'
            if item.get('type') == 'added': tag_text = '新增'
            if item.get('type') == 'closed': tag_text = '关闭'
            label = item.get('label', '')
            field = '充值' if item.get('field') == 'deposit' else ('提现' if item.get('field') == 'withdraw' else '')
            before = item.get('before'); after = item.get('after'); reason = item.get('reason')
            line = f"[{tag_text}] {label}"
            if field: line += f" · {field}"
            if before is not None and after is not None: line += f" {before} -> {after}"
            if reason: line += f" · 因素: {reason}"
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": line}})
        elements.append({
            "tag": "hr"
        })
    # fallback / details
    # 兼容旧卡片：不使用不可用的折叠组件，改为截断展示
    # 不再附带原始详情，保持卡片简洁
    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "elements": elements,
            "header": {"title": {"tag": "plain_text", "content": title}}
        }
    }

def _parse_logs(logs):
    parsed = []
    try:
        for line in (logs if isinstance(logs, list) else str(logs).splitlines()):
            s = str(line)
            item = {}
            if '新增' in s:
                item['type'] = 'added'
            elif '关闭' in s:
                item['type'] = 'closed'
            elif '变化' in s:
                item['type'] = 'changed'
            # field
            if '充值' in s:
                item['field'] = 'deposit'
            elif '提现' in s:
                item['field'] = 'withdraw'
            # before/after pattern like "False -> True"
            if '->' in s:
                try:
                    seg = s.split('->')
                    item['before'] = seg[0].strip()[-5:].strip().strip(':').split()[-1]
                    item['after'] = seg[1].strip().split()[0]
                except Exception:
                    pass
            # label after prefix "symbol:" or general prefix
            if 'symbol:' in s or 'name:' in s or 'network:' in s:
                item['label'] = s.split('reason:')[0].strip()
            # reason
            if 'reason:' in s:
                item['reason'] = s.split('reason:')[-1].strip()
            parsed.append(item)
    except Exception:
        return []
    return parsed

def send_webhook(logs):
    # 从环境变量读取 Lark Webhook 地址
    webhook_url = os.getenv("LARK_WEBHOOK_URL")
    if not webhook_url:
        logging.warning("未配置 LARK_WEBHOOK_URL 环境变量，跳过发送 webhook")
        return
    try:
        message = "\n".join(logs) if isinstance(logs, list) else str(logs)
        payload = _build_card("Binance 网络状态变更", message, _parse_logs(logs))
        result = requests.post(webhook_url, json=payload)
        result.raise_for_status()  # 检查 HTTP 错误
        logging.info(f"发送 webhook 成功: {result.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"发送 webhook 失败: {str(e)}")

# 定义API爬取函数
def fetch_and_compare():
    global last_response
    # API接口地址
    api_url = "https://www.binance.com/bapi/capital/v2/public/capital/getNetworkCoinAll?lang=zh-CN&ignoreDex=true"
    logging.info("开始请求 binance API...")
    try:
        # 发起GET请求
        response = requests.get(api_url)
        response.raise_for_status()  # 检查请求是否成功
        current_response = response.json()  # 解析JSON返回值
        logging.info("请求成功")
        hasdiff = False
        logs = []
        # 如果有上一次的返回值，进行比对
        if last_response is not None:
            if current_response == last_response:
                logging.info("数据没有变化")
            else:
                logging.info("数据发生变化！差异如下：")
                hasdiff = True
                # 比对差异（如果是JSON字符串）
                diff = unified_diff(
                    json.dumps(last_response, indent=4).splitlines(),
                    json.dumps(current_response, indent=4).splitlines(),
                    lineterm=""
                )
                logging.info("\n".join(diff))

        if hasdiff or last_response is None:
            coins = current_response["data"]
            for coin in coins:
                symbol = coin["coin"]
                name = coin["name"]
                depositAllEnable = coin["depositAllEnable"]
                withdrawAllEnable = coin["withdrawAllEnable"]
                for network in coin["networkList"]:
                    network_name = network["network"]
                    depositEnable = network["depositEnable"]
                    withdrawEnable = network["withdrawEnable"]
                    depositMsgCategoryDesc = network["depositMsgCategoryDesc"]
                    withdrawMsgCategoryDesc = network["withdrawMsgCategoryDesc"]
                    label = f"symbol: {symbol} - name: {name} - network: {network_name}"
                    if label in coin_network_deposit_status and coin_network_deposit_status[label] != depositEnable:
                        logs += [f"{label} 充值状态发生变化！ {coin_network_deposit_status[label]} -> {depositEnable} reason: {depositMsgCategoryDesc}"]
                    if label in coin_network_withdraw_status and coin_network_withdraw_status[label] != withdrawEnable:
                        logs += [f"{label} 提现状态发生变化！{label} {coin_network_withdraw_status[label]} -> {withdrawEnable} reason: {withdrawMsgCategoryDesc}"]
                    if label not in coin_network_deposit_status and last_response is not None:
                        logs += [f"{label} 新增充值状态：{depositEnable} reason: {depositMsgCategoryDesc}"]
                    if label not in coin_network_withdraw_status and last_response is not None:
                        logs += [f"{label} 新增提现状态：{withdrawEnable} reason: {withdrawMsgCategoryDesc}"]
                    if not withdrawAllEnable and last_response is None:
                        logs += [f"{label} 提现关闭原因：{withdrawMsgCategoryDesc}"]
                    if not depositEnable and last_response is None:
                        logs += [f"{label} 充值关闭原因：{depositMsgCategoryDesc}"]
                    coin_network_deposit_status[label] = depositEnable
                    coin_network_withdraw_status[label] = withdrawEnable
                    
        # print logs
        if len(logs) > 0:
            logging.info("\n".join(logs))
            send_webhook(logs)
        # 更新上一次的返回值
        last_response = current_response
        with open(jsonfile, "w") as file:
            json.dump(current_response, file, indent=4)
    except requests.exceptions.RequestException as e:
        logging.error(f"请求失败：{e}")

# 定时任务：每隔1分钟爬取一次
schedule.every(1).minutes.do(fetch_and_compare)

# 主循环
logging.info("开始定时爬取...")
while True:
    schedule.run_pending()
    time.sleep(1)
