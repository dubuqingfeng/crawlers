
import csv
import requests

from bs4 import BeautifulSoup

if __name__ == "__main__":
    app_list = []
    # first read the csv into memory
    with open('./app_spider/360.csv', 'r') as f:
        reader = csv.reader(f)
        app_list = list(reader)
    final_list = []
    for app in app_list:
        if app[7] == 'link':
            continue
        url = "http://m.app.so.com" + app[7]
        # request the url
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        author = ''
        if len(soup.select('.app-moreinfo div')) == 0:
            author = ''
        else:
            author = soup.select('.app-moreinfo div')[1].get_text()
        app.append(author)
        final_list.append(app)
        print(app[1], app[4])
    print(final_list)
    # write csv
    # _id,app_no,similar,keyword,app_name,download_num,source,link,size,download_url
    header = ['_id', 'app_no', 'similar', 'keyword', 'app_name', 'download_num', 'source', 'link', 'size', 'download_url', 'author']
    with open('./app_spider/f360.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(final_list)
