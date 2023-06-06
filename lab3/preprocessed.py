import os
import json
import re
import random
import docx
from ltp import LTP
from utils import STOP_WORDS, DATA_DIR, FILE_DIR

ltp = LTP()

def get_stop_words():
    """
    从指定的文件中获取stopwords
    :return: 文件不存在则报错, 存在则返回stopwords列表
    """
    stopwords = []
    path = STOP_WORDS
    if not os.path.exists(path):
        print("No stop words file!")
        return
    for line in open(path, "r", encoding="utf-8"):
        stopwords.append(line.strip())
    return stopwords


def remove_stop_words(stopwords: list,
                      text_words: list):
    """
    对分词结果进行去停用词处理
    :param stopwords: 停用词列表
    :param text_words: 分词列表
    :return: 去掉停用词后的分词结果
    """
    ret = []
    for text_word in text_words:
        if text_word not in stopwords:
            ret.append(text_word)
    return ret

def segment(stopwords):
    """
    分词执行程序, 将会进行分词和去停用词
    :param stopwords: 停用词表
    :param needsegs: 需要分词的json列表
    :param segor: 分词程序
    :return: 列表, 每个元素是一个json格式的数据
    """
    ret = []
    with open(DATA_DIR, "r", encoding="utf-8") as f:
        needsegs = f.readlines()
    for i,data in enumerate(needsegs):
        print(i)
        web = json.loads(data.strip())
        title_words = ltp.pipeline([web["title"]], tasks=['cws']).cws[0]
        web["segmented_title"] = remove_stop_words(stopwords, title_words)
        # para = web["paragraphs"]
        # pattern = re.compile(r"([\n\t])")
        # para = re.sub(pattern, "", para)
        paragraph_words = ltp.pipeline([web["paragraghs"]], tasks=['cws']).cws[0]
        web["segmented_paragraphs"] = remove_stop_words(stopwords, paragraph_words)

        # 保持要求的文件格式
        all_file_name = web["file_name"]
        seg_file_name = []
        seg_file_contents = []
        for file_name in all_file_name:
            if '.doc' not in file_name: # 不处理不是doc/docx格式的文件
                continue
            seg_file_name.append([file_name])
            if '.docx' not in file_name:
                file_name = file_name + 'x' # 读取docx文件
            try:
                file = docx.Document(FILE_DIR  + '\\' + file_name)
                contents = ' '.join([p.text.strip().replace(' ','') for p in file.paragraphs])
                seg_contents = ltp.pipeline([contents], tasks=['cws']).cws[0]
                seg_file_contents.append(remove_stop_words(stopwords, seg_contents))
            except docx.opc.exceptions.PackageNotFoundError:
                continue

        web["segmented_file_name"] = seg_file_name
        web["segmented_file_contents"] = seg_file_contents
        web["authority"] = random.randint(1, 4) # 访问权限
        ret.append(web)
    return ret


def write_result(data: list):
    """
    将结果写入文件
    :param data: 结果
    :return: None
    """
    with open("./data/seg_web.json", "w", encoding="utf-8") as f:
        for line in data:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    stop_words = get_stop_words()
    results = segment(stop_words)
    write_result(results)
    print("Finish!")