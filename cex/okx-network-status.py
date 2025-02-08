# https://www.okx.com/zh-hans/status
# https://www.okx.com/v2/asset/currency/status?page=0
import requests
import json
import schedule
import time
from difflib import unified_diff
import logging

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

        # 更新上一次的返回值
        last_response = all_data
        with open(jsonfile, "w") as file:
            json.dump(all_data, file, indent=4)

    except requests.exceptions.RequestException as e:
        logging.error(f"请求失败：{e}")

# 定时任务：每隔1分钟爬取一次
schedule.every(1).minutes.do(fetch_and_compare)

# 主循环
print("开始定时爬取...")
while True:
    schedule.run_pending()
    time.sleep(1)
