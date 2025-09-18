# https://www.okx.com/zh-hans/status
# https://www.okx.com/v2/asset/currency/status?page=0
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
        logging.FileHandler("./logs/okx_network_status.log"),  # 将日志写入文件
        logging.StreamHandler()  # 同时输出到控制台
    ]
)

jsonfile = "./json/okx_network_status_api_data.json"

# pip install requests schedule
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
    elements = []
    if parsed:
        total = len(parsed)
        deposit_changes = sum(1 for x in parsed if x.get('field') == 'deposit')
        withdraw_changes = sum(1 for x in parsed if x.get('field') == 'withdraw')
        added = sum(1 for x in parsed if x.get('type') == 'added')
        closed = sum(1 for x in parsed if x.get('type') == 'closed')
        elements.append({
            "tag": "note",
            "elements": [{"tag": "plain_text", "content": f"变更: {total} | 充值: {deposit_changes} | 提现: {withdraw_changes} | 新增: {added} | 关闭: {closed}"}]
        })
        for item in parsed:
            color = 'orange'; tag_text = '变更'
            if item.get('type') == 'added': color = 'blue'; tag_text = '新增'
            if item.get('type') == 'closed': color = 'red'; tag_text = '关闭'
            label = item.get('label', '')
            field = '充值' if item.get('field') == 'deposit' else ('提现' if item.get('field') == 'withdraw' else '')
            before = item.get('before'); after = item.get('after'); reason = item.get('reason')
            line = f"{label}"
            if field: line += f" · {field}"
            if before is not None and after is not None: line += f" {before} -> {after}"
            if reason: line += f" · 因素: {reason}"
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": line}, "extra": {"tag": "tag", "text": tag_text, "color": color}})
        elements.append({"tag": "hr"})
    detail = message
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": "原始详情"}]})
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"```\n{detail}\n```"}})
    return {"msg_type": "interactive", "card": {"config": {"wide_screen_mode": True}, "elements": elements, "header": {"title": {"tag": "plain_text", "content": title}}}}

def _parse_logs(logs):
    parsed = []
    try:
        for line in (logs if isinstance(logs, list) else str(logs).splitlines()):
            s = str(line)
            item = {}
            if '新增' in s: item['type'] = 'added'
            elif '关闭' in s: item['type'] = 'closed'
            elif '变化' in s: item['type'] = 'changed'
            if '充值' in s: item['field'] = 'deposit'
            elif '提现' in s: item['field'] = 'withdraw'
            if '->' in s:
                try:
                    seg = s.split('->')
                    item['before'] = seg[0].strip().split()[-1]
                    item['after'] = seg[1].strip().split()[0]
                except Exception:
                    pass
            if '原因' in s:
                item['reason'] = s.split('原因')[-1].strip(': ：').strip()
            item['label'] = s.split('原因')[0].strip()
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
        # 如果 logs 是字典，转换为字符串
        if isinstance(logs, dict):
            message = json.dumps(logs, ensure_ascii=False, indent=2)
        # 如果 logs 是列表，用换行符连接
        elif isinstance(logs, list):
            message = "\n".join(str(item) for item in logs)
        # 其他情况直接转为字符串
        else:
            message = str(logs)

        payload = _build_card("OKX 网络状态变更", message, _parse_logs(logs))
        result = requests.post(webhook_url, json=payload)
        result.raise_for_status()  # 检查 HTTP 错误
        logging.info(f"发送 webhook 成功: {result.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"发送 webhook 失败: {str(e)}")


# 定义API爬取函数
def fetch_and_compare():
    global last_response
    page = 0
    all_data = []
    has_next_page = True
    logging.info("开始请求 okx API...")

    try:
        while has_next_page:
            # API接口地址（带分页参数）
            api_url = f"https://www.okx.com/v2/asset/currency/status?page={page}"
            # 发起GET请求
            response = requests.get(api_url)
            response.raise_for_status()  # 检查请求是否成功
            current_response = response.json()  # 解析JSON返回值

            if current_response.get("code") != 0:
                logging.error(f"API返回异常：{current_response}")
                break

            # 合并分页数据
            data = current_response.get("data", [])
            all_data.extend(data)
            has_next_page = len(data) > 0
            page += 1
            logging.info(f"请求成功，当前页码: {page}")
            time.sleep(1)

        logging.info("请求成功")
        hasdiff = False
        logs = []

        # 如果有上一次的返回值，进行比对
        if last_response:
            if all_data == last_response:
                logging.info("数据没有变化")
            else:
                logging.info("数据发生变化！差异如下：")
                hasdiff = True
                # 比对差异（如果是JSON字符串）
                diff = unified_diff(
                    json.dumps(last_response, indent=4).splitlines(),
                    json.dumps(all_data, indent=4).splitlines(),
                    lineterm=""
                )
                logging.info("\n".join(diff))

        if hasdiff or not last_response:
            for coin in all_data:
                symbol = coin["symbol"]
                full_name = coin["fullName"]
                deposit_status = coin["rechargeableStatus"] == 2
                withdraw_status = coin["withdrawableStatus"] == 2

                for sub_currency in coin.get("subCurrencyList", []):
                    sub_symbol = sub_currency["symbol"]
                    deposit_enable = sub_currency["rechargeable"]
                    withdraw_enable = sub_currency["withdrawable"]
                    deposit_remark = sub_currency.get("depositRemark", "无")
                    withdraw_remark = sub_currency.get("withdrawRemark", "无")

                    label = f"symbol: {symbol} - full_name: {full_name} - sub_symbol: {sub_symbol}"
                    if label in coin_network_deposit_status and coin_network_deposit_status[label] != deposit_enable:
                        logs.append(f"{label} 充值状态发生变化！{coin_network_deposit_status[label]} -> {deposit_enable} 原因: {deposit_remark}")
                    if label in coin_network_withdraw_status and coin_network_withdraw_status[label] != withdraw_enable:
                        logs.append(f"{label} 提现状态发生变化！{coin_network_withdraw_status[label]} -> {withdraw_enable} 原因: {withdraw_remark}")
                    if label not in coin_network_deposit_status and last_response is not None:
                        logs.append(f"{label} 新增充值状态：{deposit_enable} 原因: {deposit_remark}")
                    if label not in coin_network_withdraw_status and last_response is not None:
                        logs.append(f"{label} 新增提现状态：{withdraw_enable} 原因: {withdraw_remark}")
                    if not deposit_enable and last_response is None:
                        logs.append(f"{label} 充值关闭原因：{deposit_remark}")
                    if not withdraw_enable and last_response is None:
                        logs.append(f"{label} 提现关闭原因：{withdraw_remark}")

                    # 更新状态
                    coin_network_deposit_status[label] = deposit_enable
                    coin_network_withdraw_status[label] = withdraw_enable

        # 输出日志
        if logs:
            logging.info("\n".join(logs))
            # 把 logs 发送 webhook
            send_webhook(logs)

        # 更新上一次的返回值
        last_response = all_data
        with open(jsonfile, "w") as file:
            json.dump(all_data, file, indent=4)

    except requests.exceptions.RequestException as e:
        logging.error(f"请求失败：{e}")

# 定时任务：每隔1分钟爬取一次
schedule.every(1).minutes.do(fetch_and_compare)

fetch_and_compare()
# 主循环
print("开始定时爬取...")
while True:
    schedule.run_pending()
    time.sleep(1)
