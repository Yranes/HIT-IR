from util import *
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer, TfidfVectorizer
from tqdm import tqdm
from BM25 import BM25
import joblib
import os
from scipy.linalg import norm
import Levenshtein
from question_classification import Question_classifier

SEG_PASS_SAVE_SENT_PATH = './data/segpassge_sent_save.json'
SEG_TRAIN_PATH = './data/segtrain.json'
SEG_TEST_PATH = './preprocessed/segtest.json'

TRAIN_FEA_PATH = './data/train_feature.txt'
DEV_FEA_PATH = './data/dev_feature.txt'
TEST_FEA_PATH = './data/test_feature.txt'

def quesload(file_path):
    ques_lst = read_json(file_path)
    ques_lst.sort(key = lambda x: x['qid'])
    train_q, train_a = [], []
    for q in ques_lst:
        qid, query = q['qid'], q['question']
        train_q.append({'qid': qid, 'question': query})
        pid, answer_sentence, answer = q['pid'], q['answer_sentence'], q['answer']
        train_a.append({'pid': pid, 'answer_sentence': answer_sentence, 'answer':answer})
    return train_q, train_a

class AnswerSort():
    def __init__(
            self, train_path = SEG_TRAIN_PATH, train_passage_path = SEG_PASS_SAVE_SENT_PATH, 
            train_feature_path = TRAIN_FEA_PATH, dev_feature_path = DEV_FEA_PATH, 
            test_path = SEG_TEST_PATH, test_feature_path = TEST_FEA_PATH):
        self.train_doc = read_json(train_path)
        self.test_doc = read_json(test_path)
        self.q, self.ans, self.qpid = {}, {}, {}
        self.testqpid, self.testq = {}, {}

        for dic in self.train_doc:
            self.qpid[dic['qid']] = dic['pid']
            self.q[dic['qid']] = dic['question'].replace(' ', '')
            self.ans[dic['qid']] = dic['answer_sentence'].replace(' ', '')
        for dic in self.test_doc:
            self.testqpid[dic['qid']] = dic['pid']
            self.testq[dic['qid']] = dic['question']
        self.seg_passage = read_json(train_passage_path)
        self.train_feature_path = train_feature_path
        self.dev_feature_path = dev_feature_path
        self.test_feature_path = test_feature_path
        self.feature_list, self.test_feature_list = [], []
        self.solve_train_data()

    def build_feature(self, q, sent, cv, tv, bm25_score):
        feature_list = []
        q_word, sent_word = q.split(), sent.split()
        tvector_q = tv.transform([q]).toarray().reshape(-1)
        tvector_sent = tv.transform([sent]).toarray().reshape(-1)
        cvector_q = cv.transform([q]).toarray().reshape(-1)
        cvector_sent = cv.transform([sent]).toarray().reshape(-1)
        norm_c = norm(cvector_q) * norm(cvector_sent)
        norm_t = norm(tvector_q) * norm(tvector_sent)

        feature_list.append(f'1:{len(sent_word)}')
        feature_list.append(f'2:{abs(len(q) - len(sent))}')
        feature_list.append(f'3:{len(set(q_word) & set(sent_word))}')
        feature_list.append(f'4:{len(set(q) & set(sent))}')
        feature_list.append(f'5:{np.dot(cvector_q, cvector_sent) / norm_c if norm_c else 0}')
        feature_list.append(f'6:{np.dot(tvector_q, tvector_sent) / norm_t if norm_t else 0}')
        feature_list.append(f'7:{bm25_score}')
        a = 1 if ':' in sent or '：' in sent else 0
        feature_list.append(f'8:{a}')
        query, sentence = q.replace(' ', ''), sent.replace(' ', '')
        feature_list.append(f'9:{Levenshtein.distance(query, sentence)}')
        return feature_list

    def solve_train_data(self):
        if os.path.exists(self.train_feature_path) and os.path.exists(self.dev_feature_path):
            return 
        for itm in tqdm(self.train_doc):
            features = []
            qid, pid, query, a_sent = itm['qid'], itm['pid'], itm['question'], itm['answer_sentence']
            passage = self.seg_passage[pid]['document']
            corpus = [sent.split() for sent in passage]
            cv = CountVectorizer(token_pattern=r"(?u)\b\w+\b")
            cv.fit_transform(passage)
            tv = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
            tv.fit_transform(passage)
            bm25 = BM25(corpus)
            for index, sent in enumerate(passage):
                label = 1 if sent == a_sent else 0
                feature = ' '.join(self.build_feature(query, sent, cv, tv, bm25.get_rsv(query.split(), index)))
                features.append(f'{label} qid:{qid} ' + feature)
            self.feature_list.append(features)
        self.feature_list.sort(key = lambda x: int(x[0].split()[1][4:]))

        train_features, dev_features = train_test_split(
            self.feature_list, test_size=0.10, shuffle=False, random_state=0
        )
        
        with open(self.train_feature_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join([feature for feature_lst in train_features for feature in feature_lst]))
        with open(self.dev_feature_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join([feature for feature_lst in dev_features for feature in feature_lst]))
            
    def train(self, model_path, dev_predict_path):
            if os.path.exists(model_path) == False:    
                train_cmd = os.getcwd() + f'/ranksvm/svm_rank_learn.exe -c 10 {self.train_feature_path} {model_path}'
                os.system(train_cmd)
            print('-----Train Over----')
            test_cmd = os.getcwd() + f'./ranksvm/svm_rank_classify.exe {self.dev_feature_path} {model_path} {dev_predict_path}'
            os.system(test_cmd)
            print(f'Answer path {dev_predict_path}')
            print('-----Test Over----')

    def evaluate(self, dev_predict_path, result_path):
        assert os.path.exists(dev_predict_path)
        with open(dev_predict_path, 'r', encoding = 'utf-8') as ans_file:
            predictions = [float(line.strip()) for line in ans_file.readlines()]
        with open(self.dev_feature_path, 'r', encoding = 'utf-8') as feature_file:
            qid_list = [int(line.split()[1][4:]) for line in feature_file]
        assert len(predictions) == len(qid_list)
        result_with_id, result = [], [(qid, predic) for predic, qid in zip(predictions, qid_list)]
        lst_qid, now_qid_start_pos = -1, 0
        for idx, (qid, predic) in enumerate(result):
            if qid != lst_qid:
                lst_qid, now_qid_start_pos = qid, idx
            result_with_id.append((qid, predic, idx - now_qid_start_pos))
        result_with_id.sort()
        Sum, Cnt = 0, 0
        lst_qid, readable_result = -1, []    
        for (qid, predic, sent_num) in reversed(result_with_id):
            if qid != lst_qid:
                lst_qid = qid
                Sum += 1
                if self.ans[qid] == self.seg_passage[self.qpid[qid]]['document'][sent_num].replace(' ', ''):
                    Cnt += 1
                readable_result.append(
                    {
                        "qid": qid,
                        "question": self.q[qid],
                        "answer_sentence": self.ans[qid],
                        "sentence_chosen_by_model": self.seg_passage[self.qpid[qid]]['document'][sent_num].replace(' ', '')
                    }
                )
        print(f"acc : {Cnt / Sum}")
        #acc : 0.6026119402985075 <-完美匹配率
        # lst_qid, test_result, X = result_with_id[-1][0], [], []    
        # for (qid, predic, sent_num) in reversed(result_with_id):
        #     if qid != lst_qid:
        #         test_result.append(
        #             {
        #                 "qid": lst_qid,
        #                 "question": self.q[lst_qid],
        #                 "pid": self.qpid[lst_qid],
        #                 "sentence_chosen_by_model": X
        #             }
        #         )
        #         lst_qid = qid
        #         X = []
        #     X.append(self.seg_passage[self.qpid[qid]]['document'][sent_num])
        # qid = result_with_id[0][0]
        # test_result.append(
        #         {
        #             "qid": qid,
        #             "question": self.q[qid],
        #             "pid": self.qpid[qid],
        #             "sentence_chosen_by_model": X
        #         }
        #     )
        # Sum, Cnt = 0, 0
        # for dic in test_result:
        #     qid = dic['qid']
        #     for i, sent in enumerate(dic['sentence_chosen_by_model']):
        #         c_sent = sent.replace(' ', '')
        #         if self.ans[qid] in c_sent:
        #              Sum += 1.0 / (i + 1)
        #     Cnt += 1
        # print(Sum / Cnt)
        #0.7422154106397643 <-MRR
        write_json(result_path, readable_result)
    
    def solve_test_data(self):
        if os.path.exists(self.test_feature_path):
            return 
        for itm in tqdm(self.test_doc):
            features = []
            qid, pid, query = itm['qid'], itm['pid'], itm['question']
            passage = self.seg_passage[pid]['document']
            corpus = [sent.split() for sent in passage]
            cv = CountVectorizer(token_pattern=r"(?u)\b\w+\b")
            cv.fit_transform(passage)
            tv = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
            tv.fit_transform(passage)
            bm25 = BM25(corpus)
            for index, sent in enumerate(passage):
                feature = ' '.join(self.build_feature(query, sent, cv, tv, bm25.get_rsv(query.split(), index)))
                features.append(f'0 qid:{qid} ' + feature)
            self.test_feature_list.append(features)
        self.test_feature_list.sort(key = lambda x: int(x[0].split()[1][4:]))
        with open(self.test_feature_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join([feature for feature_lst in self.test_feature_list for feature in feature_lst]))

    def predict(self, model_path, test_predict_path):
        self.solve_test_data()
        if os.path.exists(model_path) == False:    
            train_cmd = os.getcwd() + f'/ranksvm/svm_rank_learn.exe -c 10 {self.train_feature_path} {model_path}'
            os.system(train_cmd)
        print('-----Train Over----')
        test_cmd = os.getcwd() + f'./ranksvm/svm_rank_classify.exe {self.test_feature_path} {model_path} {test_predict_path}'
        os.system(test_cmd)
        print(f'Answer path {test_predict_path}')
        print('-----Test Over----')

    def Save_segtest(self, test_predict_path, result_path):
        assert os.path.exists(test_predict_path)
        Qc = Question_classifier(fine = False, mode = 'predict')
        with open(test_predict_path, 'r', encoding = 'utf-8') as ans_file:
            predictions = [float(line.strip()) for line in ans_file.readlines()]
        with open(self.test_feature_path, 'r', encoding = 'utf-8') as feature_file:
            qid_list = [int(line.split()[1][4:]) for line in feature_file]
        assert len(predictions) == len(qid_list)
        result_with_id, result = [], [(qid, predic) for predic, qid in zip(predictions, qid_list)]
        lst_qid, now_qid_start_pos = -1, 0
        for idx, (qid, predic) in enumerate(result):
            if qid != lst_qid:
                lst_qid, now_qid_start_pos = qid, idx
            result_with_id.append((qid, predic, idx - now_qid_start_pos))
        result_with_id.sort()
        lst_qid, test_result, X = result_with_id[-1][0], [], []    
        for (qid, predic, sent_num) in reversed(result_with_id):
            if qid != lst_qid:
                test_result.append(
                    {
                        "qid": lst_qid,
                        "question": self.testq[lst_qid],
                        "q_class": Qc.predict(self.testq[lst_qid])[0],
                        "pid": self.testqpid[lst_qid],
                        "sentence_chosen_by_model": X
                    }
                )
                lst_qid = qid
                X = []
            X.append(self.seg_passage[self.testqpid[qid]]['document'][sent_num])
        qid = result_with_id[0][0]
        test_result.append(
                {
                    "qid": qid,
                    "question": self.testq[qid],
                    "q_class": Qc.predict(self.testq[qid])[0],
                    "pid": self.testqpid[qid],
                    "sentence_chosen_by_model": X
                }
            )
        test_result.sort(key = lambda x: x['qid'])
        write_json(result_path, test_result)

if __name__ == '__main__':
    x = AnswerSort()
    #x.train('./sentence_rank/model.dat', './sentence_rank/predict.txt')
    x.evaluate('./sentence_rank/predict.txt', './sentence_rank/readable_prediction.json')
    #x.predict('./sentence_rank/model.dat', './answer_sentence_selection/predict.txt')
    #x.Save_segtest('./answer_sentence_selection/predict.txt', './answer_sentence_selection/segtest.json')