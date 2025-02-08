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