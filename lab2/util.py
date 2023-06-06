
PASS_PATH = './data/passages_multi_sentences.json'
TEST_PATH = './data/test.json'
TRAIN_PATH = './data/train.json'
STOP_WORDS_PATH = './data/stopwords.txt'

QUES_TEST_PATH = './question_classification/test_questions.txt'
QUES_TRAIN_PATH = './question_classification/trian_questions.txt'

INDEX_PATH = './data/index.pickle'
SEGDOC_PATH = './data/segpassage.json'

import json
from ltp import LTP

ltp = LTP()

def read_json(file_path):
    ans_list = []
    with open(file_path, 'r', encoding = 'utf-8') as f:
        json_list = f.readlines()
        for line_json in json_list:
            tmp = json.loads(line_json)
            ans_list.append(tmp)
    return ans_list

def read_stp_word(file_path):
    with open(file_path, 'r', encoding = 'utf-8') as f:
        stp_list = f.read().split('\n')
    return stp_list

def write_json(file_path, res):
    with open(file_path, 'w', encoding='utf-8') as f:   
        for page in res:
            json.dump(page, f, ensure_ascii=False)
            f.write('\n')

def handle(s):
    return ''.join(x for x in s if x.isprintable())

def remove_stop_word(seg_sentence, stp_words_list):
    return [handle(word.strip(' ')) for word in seg_sentence if word not in stp_words_list]

def seg_doc(doc, stp_words_list):
    sents = ltp.pipeline(doc, tasks = ['cws']).cws
    print(type(sents[0]))
    assert type(sents[0]) == type([])
    tt = []
    for sent in sents:
        tt.append(remove_stop_word(sent, stp_words_list))
    return tt

def seg_sent(sent, stp_words_list = None):
    assert type(sent[0]) == type('a')
    if stp_words_list is None:
        return ltp.pipeline(sent, tasks = ['cws']).cws
    else:
        return remove_stop_word(ltp.pipeline(sent, tasks = ['cws']).cws, stp_words_list)

def pos_sent(sent): #863词性标注集
    return ltp.pipeline(sent, tasks=['pos']).pos

def ner_sent(sent):
    return ltp.pipeline(sent, tasks=['ner']).ner

def _main():
    X = read_json(TEST_PATH)
    Q = []
    for pdoc in X:
        passage = {}
        ques = pdoc['question']
        dc = list(ltp.pipeline(ques, tasks = ['cws']).cws)
        passage['qid'] = pdoc['qid']
        passage['question'] = ' '.join(dc)
        Q.append(passage)
    write_json('./data/segtest.json', Q) 

if __name__ == '__main__':
    _main()