from ltp import LTP
import json

res = []
ltp = LTP("LTP/small")

def handle(s):
    return ''.join(x for x in s if x.isprintable())

def seg(stop_words = './stopwords.txt', craw_file = './craw.json'):
    with open(stop_words, 'r', encoding='utf-8') as stp_file, open(craw_file, 'r', encoding='utf-8') as crw_file:
        stop_words_list = stp_file.read().split('\n')
        cr = crw_file.readlines()
        line_no = len(cr)
        for idx, line in enumerate(cr):
            print(f'NOW LOADING {idx} / {line_no}')
            line_json = json.loads(line)
            title = line_json['title']
            para = line_json['paragraghs']
            outpt = ltp.pipeline(title, tasks=["cws"])
            title_list = [handle(word.strip(' ')) for word in outpt.cws if word not in stop_words_list]
            outpt = ltp.pipeline(para, tasks=["cws"])
            para_list = [handle(word.strip(' ')) for word in outpt.cws if word not in stop_words_list]

            crw = {'url':line_json['url'], 'segmented_title':title_list, 'segmented_paragraphs':para_list, 'file_name': line_json['file_name']}
            res.append(crw)

            if idx >= 9:
                break

def write_json(json_name):
    with open('./' + json_name, 'w', encoding='utf-8') as f:   
        for page in res:
            json.dump(page, f, ensure_ascii=False)
            f.write('\n')

def main():
    seg()
    write_json('preprocessed.json')

if __name__ == '__main__':
    main()