import pymongo
import csv
from simhash import Simhash

def cal_simhash_similarity(a, b):
    """
    计算文本相似度
    :param a: 文本A
    :param b: 文本B
    :return:
    """
    a_simhash = Simhash(a)
    b_simhash = Simhash(b)
    a = float(a_simhash.value)
    b = float(b_simhash.value)
    if a > b:
        similar = b / a
    else:
        similar = a / b
    return similar


def cal_simhash_similarity2(a, b):
    """
    计算文本相似度
    :param a: 文本A
    :param b: 文本B
    :return:
    """
    if a == b:
        return 1
    if a in b:
        return 1
    if b in a:
        return 1
    return cal_simhash_similarity(a, b)


def collect(start, end):
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    database = client['mongodb_db']
    collections = database["a360"]
    mydoc = collections.find({"app_no":{"$gte": start, "$lt": end}})
    m = {}
    for x in mydoc:
        app_no = x["app_no"]
        if app_no in m.keys():
            m[app_no].append(x)
        else:
            m[app_no] = [x]
    return m


if __name__ == "__main__":
    lista = []
    for i in range(0, 1000):
        start = i * 10
        end = i * 10 + 10
        print(start, end)
        m = collect(start, end)
        for k, v in m.items():
            max_similar = 0
            last_item = None
            for i in v:
                if i['app_name'] == "":
                    continue
                similar = cal_simhash_similarity2(i['keyword'], i['app_name'])
                if similar > max_similar:
                    max_similar = similar
                    last_item = i
            if max_similar >= 1:
                lista.append([last_item['_id'], last_item['app_no'], max_similar, last_item['keyword'], last_item['app_name'], last_item['download_num'], last_item['source'], last_item['link'], last_item['size'], last_item['download_url']])
    header = ['_id', 'app_no', 'similar', 'keyword', 'app_name', 'download_num', 'source', 'link', 'size', 'download_url']
    with open("360.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(lista)