from urllib import error, parse, request, response, robotparser
from bs4 import BeautifulSoup
import string
import os
import json

start_url = 'http://jwc.hit.edu.cn'
user_agent = 'HIT_IR_CRAW_ROBOT'
download_path = './file'

page_data = []
tar_num, tar_file_num = 1100, 100
cnt_num, cnt_file_num = 0, 0

Headers = {
    'User-Agent': 'Your Agent',
    'Connection': 'close',
    'Cookie': 'Your Cookie'
}

rp_list, has_rp_url_list = [], []

def is_legal(url):
    if url is None:
        return False
    if url.endswith('xlsx') or url.endswith('docx') or url.endswith('doc') or url.endswith('pdf') or url.endswith('txt') or url.endswith('pptx') or url.endswith('zip') or url.endswith('ppt'):
        return False
    if url.endswith('rar') or url.endswith('xls') or 'redirect' in url:
        return False
    if 'jwc.hit' not in url:
        return False
    result = parse.urlparse(url = url, scheme = 'http', allow_fragments=True)
    index_url = result.scheme + '://' + result[1]
    if index_url not in has_rp_url_list:
        try:
            rp = robotparser.RobotFileParser(index_url + '/robots.txt')
            rp.read()
        except:
            return False
        rp_list.append(rp)
        has_rp_url_list.append(index_url)
        if rp.can_fetch(user_agent, url) == False:
            return False
    else:
        if rp_list[has_rp_url_list.index(index_url)].can_fetch(user_agent, url) == False:
            return False
    return True

def get_url():
    url_list = [start_url]
    for url in url_list:
        try:
            req = request.Request(url = url, headers = Headers)
            resp_web = request.urlopen(req, timeout = 1.0)
            resp_page = resp_web.read()
        except:
            print(f'{url} VISIT ERROR')
        else:
            if len(url_list) >= tar_num:
                print('抓取URL完成')
                break
            else:
                 print(url)
                 print('抓取URL: {}/{}\n'.format(len(url_list), tar_num))
            soup = BeautifulSoup(resp_page, 'html.parser', from_encoding='gb18030')
            link_url_list = soup.find_all('a')
            for link in link_url_list:
                link_url = link.get('href')
                try:
                    if link_url[0] == '/':
                        link_url = start_url + link_url
                except:
                    continue
                if is_legal(link_url) and link_url not in url_list:
                    url_list.append(link_url)
    return url_list

def is_legal_file(x):
    if x is None:
        return False
    return x.endswith('xlsx') or x.endswith('xls') or x.endswith('doc') or x.endswith('docx') or x.endswith('txt')

def craw(url):
    global cnt_file_num, page_data, cnt_num
    try:
        req = request.Request(url = url, headers = Headers)
        resp_web = request.urlopen(req, timeout = 1.0)
    except:
        print(f'{url} VISIT ERROR')
    else:
        soup = BeautifulSoup(resp_web.read(), 'html.parser', from_encoding='gb18030')
        link_url_list = soup.find_all('a')
        file_url_list = list(filter(is_legal_file, map(lambda x:x.get('href'), link_url_list)))
        file_name_list = []

        title = soup.find('title')
        try:
            title = title.get_text()
        except:
            print(f"TITLE None: {url}")
            return 
        para = soup.find(attrs = {"class": "wp_articlecontent"})
        if para is None:
            para = soup.find(attrs = {"class": "news_list"})
        try:
            para = para.get_text()
        except:
            print(f"PARA NONE: {url}")
            return 
        
        cnt_num += 1
        if len(file_url_list):
            cnt_file_num += 1
            
            file_path = os.getcwd() + '\\file'

            for file_url in file_url_list:
                file_name = file_url.split('/')[-1]
                if file_url[0] == '/':
                    file_url = start_url + file_url
                try:
                    request.urlretrieve(file_url, os.path.join(file_path, file_name))
                except:
                    print(f"{file_url} file download err")
                    continue
                file_name_list.append(file_name)

        para = para.replace('\n', '')
        page_data.append({'url':url, 'title':title, 'paragraghs':para, 'file_name':file_name_list})

def write_json(json_name):
    with open('./' + json_name, 'w', encoding='utf-8') as f:   
        for page in page_data:
            json.dump(page, f, ensure_ascii=False)
            f.write('\n')


def main():
    rp = robotparser.RobotFileParser(start_url + '/robots.txt')
    rp.read()
    has_rp_url_list.append(start_url)
    rp_list.append(rp)
    #print(rp.can_fetch(user_agent, start_url))
    
    url_list = get_url()
    
    for url in url_list:
        craw(url)
    
    write_json('craw.json')
    

if __name__ == '__main__':
    main()
