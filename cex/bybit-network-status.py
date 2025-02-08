# https://api2.bybit.com/v3/private/cht/asset-common/coin-status
# https://www.bybit.com/zh-TW/announcement-info/deposit-withdraw/
import requests
import json
import schedule
import time
from difflib import unified_diff
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("./logs/bybit_network_status.log"),
        logging.StreamHandler(),
    ]
)

jsonfile = "./json/bybit_network_status_api_data.json"

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
    api_url = "https://api2.bybit.com/v3/private/cht/asset-common/coin-status"
    logging.info("开始请求 Bybit API...")
    try:
        # 发起GET请求
        response = requests.get(api_url)
        response.raise_for_status()
        current_response = response.json()
        logging.info("请求成功")

        # 检查返回的结构是否有效
        if current_response.get("ret_code") != 0:
            logging.error(f"API返回错误: {current_response.get('ret_msg', '未知错误')}")
            return

        # 解析返回结果
        current_data = current_response.get("result", {}).get("coins", [])
        has_diff = False
        logs = []

        # 如果有上一次的返回值，进行比对
        if last_response is not None:
            if current_response == last_response:
                logging.info("数据没有变化")
            else:
                logging.info("数据发生变化！差异如下：")
                has_diff = True
                # 比对差异
                diff = unified_diff(
                    json.dumps(last_response, indent=4).splitlines(),
                    json.dumps(current_response, indent=4).splitlines(),
                    lineterm=""
                )
                logging.info("\n".join(diff))

        if has_diff or last_response is None:
            for coin in current_data:
                symbol = coin["coin"]
                deposit_status = coin["depositStatus"]
                withdraw_status = coin["withdrawStatus"]

                for chain_item in coin.get("coinChainStatusItem", []):
                    chain = chain_item["chain"]
                    chain_deposit_status = chain_item["depositStatus"]
                    chain_withdraw_status = chain_item["withdrawStatus"]
                    deposit_congested_status = chain_item["depositCongestedStatus"]
                    withdraw_congested_status = chain_item["withdrawCongestedStatus"]
                    deposit_flag = chain_item["depositFlag"]
                    withdraw_flag = chain_item["withdrawFlag"]

                    label = f"{symbol} - {chain}"
                    if label in coin_network_deposit_status and coin_network_deposit_status[label] != chain_deposit_status:
                        logs.append(f"{label} 充值状态发生变化！{coin_network_deposit_status[label]} -> {chain_deposit_status}")
                    if label in coin_network_withdraw_status and coin_network_withdraw_status[label] != chain_withdraw_status:
                        logs.append(f"{label} 提现状态发生变化！{coin_network_withdraw_status[label]} -> {chain_withdraw_status}")
                    if label not in coin_network_deposit_status and last_response is not None:
                        logs.append(f"{label} 新增充值状态：{chain_deposit_status}")
                    if label not in coin_network_withdraw_status and last_response is not None:
                        logs.append(f"{label} 新增提现状态：{chain_withdraw_status}")
                    if not chain_withdraw_status and last_response is None:
                        logs.append(f"{label} 提现关闭原因：拥堵状态 {withdraw_congested_status}, 标志 {withdraw_flag}")
                    if not chain_deposit_status and last_response is None:
                        logs.append(f"{label} 充值关闭原因：拥堵状态 {deposit_congested_status}, 标志 {deposit_flag}")
                    coin_network_deposit_status[label] = chain_deposit_status
                    coin_network_withdraw_status[label] = chain_withdraw_status

        # 打印日志
        if logs:
            logging.info("\n".join(logs))

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