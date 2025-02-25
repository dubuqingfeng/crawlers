import requests
import schedule
import time
import json
import os
import logging

# https://polkachu.com/chain_upgrades
# 定义保存数据的文件
DATA_FILE = "./json/cosmos_last_data.json"

# 设置日志配置
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别
    format="%(asctime)s - %(levelname)s - %(message)s",  # 设置日志格式
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("./logs/app.log")  # 输出到文件
    ]
)

# API 目标 URL
url = "https://polkachu.com/api/v2/chain_upgrades"

def load_last_data():
    """
    从文件中加载上次保存的数据
    """
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as file:
                return json.load(file)
        except Exception as e:
            logging.error(f"无法加载数据文件，错误信息：{e}")
            return None
    return None

def save_last_data(data):
    """
    将数据保存到文件
    """
    try:
        with open(DATA_FILE, "w") as file:
            json.dump(data, file, indent=4)
        logging.info("数据已保存到文件。")
    except Exception as e:
        logging.error(f"保存数据到文件失败，错误信息：{e}")

def get_data():
    """
    获取 API 数据
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logging.warning(f"请求失败，状态码：{response.status_code}")
            return None
    except Exception as e:
        logging.error(f"请求失败，错误信息：{e}")
        return None

def compare_data(new_data, last_data):
    """
    比较新数据和上次的数据
    """
    if last_data is None:
        logging.info("首次请求，未进行比较。")
        # 打印 new_data
        logging.info(f"新数据: {new_data}")
        return new_data  # 更新 last_data
    
    # 是个 for 循环，比较 new_data 和 last_data
    added = []
    removed = []
    updated = []

    # 用 (network, node_version) 作为字典键来存储每个数据项
    last_data_dict = {(item['network'], item['node_version']): item for item in last_data}
    new_data_dict = {(item['network'], item['node_version']): item for item in new_data}

    # 查找新增的项 (new_data 中有，last_data 中没有)
    for new_item in new_data:
        key = (new_item['network'], new_item['node_version'])
        if key not in last_data_dict:
            added.append(new_item)

    # 查找删除的项 (last_data 中有，new_data 中没有)
    for last_item in last_data:
        key = (last_item['network'], last_item['node_version'])
        if key not in new_data_dict:
            removed.append(last_item)

    # 查找更新的项 (network 和 node_version 相同但字段有所变化)
    for new_item in new_data:
        key = (new_item['network'], new_item['node_version'])
        if key in last_data_dict:
            last_item = last_data_dict[key]
            changed_fields = {key: (last_item[key], new_item[key])
                              for key in last_item if last_item[key] != new_item[key]}
            if changed_fields:
                updated.append({
                    'network': new_item['network'],
                    'node_version': new_item['node_version'],
                    'changes': changed_fields
                })

    # 记录日志
    if added:
        logging.info(f"新增的项: {added}")
    if removed:
        logging.info(f"删除的项: {removed}")
    if updated:
        logging.info(f"更新的项: {updated}")
    # 返回最新数据作为 last_data
    return new_data

def job():
    """
    定时任务：获取数据并比较
    """
    try:
        global last_data  # 使用全局变量存储上次的数据
        logging.info("开始执行定时任务...")
        new_data = get_data()
        if new_data:
            last_data = compare_data(new_data, last_data)  # 比较并更新 last_data
            save_last_data(last_data)  # 保存最新数据到文件
        logging.info("定时任务结束。\n")
    except Exception as e:
        logging.error(f"定时任务执行失败，错误信息：{e}")

# 加载上次保存的数据
last_data = load_last_data()

# 使用 schedule 定义任务
schedule.every(1).minutes.do(job)  # 每 1 分钟执行一次任务

# 主线程运行 schedule
logging.info("开始运行定时任务，按 Ctrl+C 停止程序。")
job()  # 立即执行一次任务
while True:
    try:
        schedule.run_pending()  # 运行所有准备好的任务
        time.sleep(1)  # 防止 CPU 占用过高
    except KeyboardInterrupt:
        logging.info("程序已停止。")
        break
    except Exception as e:
        logging.error(f"主线程运行中出现错误，错误信息：{e}")