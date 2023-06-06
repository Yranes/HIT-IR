import numpy as np
from sklearn import svm
from util import *
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer, TfidfVectorizer
import joblib
import os
from sklearn.model_selection import GridSearchCV

QUES_MODEL_PATH = './question_classification/svm.pkl'
QUES_TFIDF_PATH = './question_classification/tfidf.pkl'

def loader(file_path, mode):
    assert mode in ['train', 'test']

    if mode == 'train':
        label_list, seg_query_list = [], []
        with open(file_path, 'r', encoding = 'utf-8') as f:
            for line in f:
                label_q = line.strip().split('\t')
                label = label_q[0]
                label_list.append(label)
                query = label_q[1]
                seg_query = seg_sent(query)
                s = ""
                for word in seg_query:
                    s += word + ' '
                seg_query_list.append(s.strip())
        return label_list, seg_query_list
    else:
        seg_query_list = []
        with open(file_path, 'r', encoding = 'utf-8') as f:
            for line in f:
                query = line.strip('\n ')
                seg_query = seg_sent(query)
                s = ""
                for word in seg_query:
                    s += word + ' '
                seg_query_list.append(s.strip())
        return seg_query_list

class Question_classifier:
    def __init__(self, fine, train_file_path = QUES_TRAIN_PATH, model_path = QUES_MODEL_PATH, tfidf_path = QUES_TFIDF_PATH, mode = 'train'):
        assert mode in ['train', 'predict']
        if mode == 'train':
            self.train_labels, self.train_ques = loader(train_file_path, 'train')
        self.model_path = model_path
        self.tfidf_path = tfidf_path
        if fine == False and os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            self.model = svm.SVC(C = 100.0, gamma = 0.01)
        if fine == False and os.path.exists(tfidf_path):
            self.tf_idf = joblib.load(tfidf_path)
        else:
            self.tf_idf = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")

    def train(self):
        X = self.tf_idf.fit_transform(self.train_ques)
        self.model.fit(X, np.array(self.train_labels))
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.tf_idf, self.tfidf_path)

    def Test(self, vali_file_path = QUES_TEST_PATH):
        test_labels, test_ques = loader(vali_file_path, 'train')
        X = self.tf_idf.transform(test_ques)
        Y = self.model.predict(X)
        score = self.model.score(X, test_labels)
        print(f'Mode On Testdata SCORE: {score}')

    def predict(self, seg_query):
        X = self.tf_idf.transform([seg_query])
        return self.model.predict(X)

    def dev_fine(self, vali_file_path = QUES_TRAIN_PATH):
        test_labels, test_ques = loader(vali_file_path, 'train')
        X = self.tf_idf.transform(test_ques)
        param_grid = [{'C': [50, 75, 100, 125], 'gamma': [0.5, 0.1, 0.05, 0.01], 'kernel': ['rbf']}]
        svm_model = svm.SVC()
        clf = GridSearchCV(svm_model, param_grid, cv=5)
        clf.fit(X, np.array(test_labels))
        print(clf.best_params_)

    def __save(self, labels, ques, save_path):
        assert len(labels) == len(ques)
        with open(save_path, 'w', encoding='utf-8') as f:
            for q, label in zip(ques, label):
                f.write(label + '\t' + q.replace(' ', '') + '\n')

if __name__ == '__main__':
    Qc = Question_classifier(fine = False, mode = 'predict')
    #Qc.train()
    #Qc.Test()
    #0.782509505703422
    print(Qc.predict("迎春门 有 多少 年 的 历史 ？"))