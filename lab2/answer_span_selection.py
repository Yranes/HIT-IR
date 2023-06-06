import re
import os
from util import *
import numpy as np
from tqdm import tqdm

from question_classification import Question_classifier

SEG_TEST_PATH = './answer_sentence_selection/segtest.json'
SEG_TRAIN_PATH = './data/segtrain.json'

def dev_answer_span(save_path, test_file_path = SEG_TRAIN_PATH):
    test_doc, res = read_json(test_file_path), []
    Qc = Question_classifier(fine=False, mode = 'predict')
    for q in tqdm(test_doc):
        qid, question, pid, sents, flag = q['qid'], q['question'], q['pid'], [q['answer_sentence']], 0
        q_class = Qc.predict(question)[0].split('_')
        answer = None
        for i, sent in enumerate(sents):
            c_sent = sent.replace(' ', '')
            word_lst = sent.split()
            pos_words = pos_sent(word_lst)
            if ':' in sent or '：' in sent:
                answer = solve_mh1(c_sent)
            elif q_class[0] == 'DES':
                answer = ''.join(word_lst)
            elif q_class[0] == 'HUM':
                answer = span_ans(word_lst, pos_words, ['ni', 'nh', 'nt'])
            elif q_class[0] == 'LOC':
                answer = span_ans(word_lst, pos_words, ['nl', 'ns'])
            elif q_class[0] == 'NUM':
                answer = span_ans(word_lst, pos_words, ['m'])
            elif q_class[0] == 'TIME':
                answer = solve_time(q_class, c_sent)
            else:
                answer = ''.join(c_sent)
            if i >= 6:
                break
            if answer is None or len(answer) == 0:
                 continue
            break
        if answer is None or len(answer) == 0:
            answer = ''.join(sents[0].replace(' ', ''))
        res.append(
            {
                'qid': qid,
                'question': question.replace(' ', ''),
                'answer_pid': pid,
                'answer': answer
            }
        )
    write_json(save_path, res)

def span_ans(sent, pos_words, target_pos):
    ans = []
    for word, pos in zip(sent, pos_words):
        if pos in target_pos:
            ans.append(word)
    if len(ans):
        return ''.join(ans)

def solve_time(q_class, sent):
    if q_class[1] == 'YEAR':
        ans_lst = re.findall('\d{1,4}年', sent)
    elif q_class[1] == 'MONTH':
        ans_lst = re.findall('\d{1,2}月', sent)
    elif q_class[1] == 'DAY':
        ans_lst = re.findall('\d{1,2}[日天]', sent)
    elif q_class[1] == 'WEEK':
        ans_lst = re.findall('((周|星期|礼拜)[1-7一二三四五六日])', sent)
    elif q_class[1] == 'RANGE':
        ans_lst = re.findall('\d{2,4}[年]?[-到至]\d{2,4}[年]?', sent)
    else:
        ans_lst = re.findall('\d{1,4}[年/-]\d{1,2}[月/-]\d{1,2}[日号]?', sent)
    if len(ans_lst) == 0:
        ans_lst = re.findall('\d{1,4}[年/-]\d{1,2}月?', sent)
    if len(ans_lst) == 0:
        ans_lst = re.findall('\d{1,2}[月/-]\d{1,2}[日号]?', sent)
    if len(ans_lst) == 0:
        ans_lst = re.findall('\d{2,4}年', sent)
    if len(ans_lst) == 0:
        ans_lst = re.findall('\d{1,2}月', sent)
    if len(ans_lst):
        try:
            return ''.join(ans_lst)
        except:
            print(ans_lst)
            return ''.join(ans_lst[0][0])
 
def solve_mh1(sent):
    aa = ''
    begin = sent.index('：') if '：' in sent else sent.index(':') 
    for i in range(begin + 1, len(sent)):
        if sent[i] in ['。', '！', '？']:
            break
        aa += sent[i]
    return aa


def answer_span(save_path, test_file_path = SEG_TEST_PATH):
    test_doc, res = read_json(test_file_path), []
    for q in tqdm(test_doc):
        qid, question, pid, sents, flag = q['qid'], q['question'], q['pid'], q['sentence_chosen_by_model'], 0
        q_class = q['q_class'].split('_')
        answer = None
        for i, sent in enumerate(sents):
            c_sent = sent.replace(' ', '')
            word_lst = sent.split()
            pos_words = pos_sent(word_lst)
            if ':' in sent or '：' in sent:
                answer = solve_mh1(c_sent)
            elif q_class[0] == 'DES':
                answer = ''.join(word_lst)
            elif q_class[0] == 'HUM':
                answer = span_ans(word_lst, pos_words, ['ni', 'nh', 'nt'])
            elif q_class[0] == 'LOC':
                answer = span_ans(word_lst, pos_words, ['nl', 'ns'])
            elif q_class[0] == 'NUM':
                answer = span_ans(word_lst, pos_words, ['m'])
            elif q_class[0] == 'TIME':
                answer = solve_time(q_class, ''.join(word_lst))
            else:
                answer = ''.join(c_sent)
            if i >= 6:
                break
            if answer is None or len(answer) == 0:
                 continue
            break
        if answer is None or len(answer) == 0:
            answer = ''.join(sents[0].replace(' ', ''))
        res.append(
            {
                'qid': qid,
                'question': question.replace(' ', ''),
                'answer_pid': [pid],
                'answer': answer
            }
        )
    write_json(save_path, res)

def main():
    #dev_answer_span('./dev_answer.json')
    answer_span('./test_answer.json')

if __name__ == '__main__':
    main()
    #only span BLEU1=0.4761837530826148
    #四模块结合BLEU1=0.247 from train