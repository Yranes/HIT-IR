import math
import numpy as np

def cal_doc_tf(doc):
    tf = {}
    for word in doc:
        tf[word] = tf.get(word, 0) + 1
    return tf

class BM25:
    def __init__(self, docs, k1 = 1.5, k3 = 1.2, b = 0.75):
        self.N = len(docs)
        self.avg_dl = sum([len(doc) + 0.0 for doc in docs]) / self.N
        self.docs = docs

        self.f, self.df, self.idf = [], {}, {}
        self.k1, self.k3, self.b = k1, k3, b
        self.cal_idf()

    def cal_idf(self):
        for doc in self.docs:
            doc_tf = cal_doc_tf(doc)
            self.f.append(doc_tf)
            for k in doc_tf.keys():
                self.df[k] = self.df.get(k, 0) + 1
        for k, v in self.df.items():
            self.idf[k] = math.log(self.N + 1) - math.log(v + 1)

    def get_rsv(self, query, index):
        query_tf = cal_doc_tf(query)
        rsv = 0
        for word in query:
            if word not in self.f[index]:
                continue
            d = len(self.docs[index])
            tf_td = self.f[index][word]
            tf_tq = query_tf[word]
            rsv += (self.idf[word] * tf_td * (self.k1 + 1) * tf_tq * (self.k3 + 1)
                    / (tf_td + self.k1 * (1 - self.b + self.b * d / self.avg_dl)) * (self.k3 + tf_tq))
        return rsv

    def doc_sort(self, query):
        scores = []
        for i in range(len(self.docs)):
            rsv = self.get_rsv(query, i)
            scores.append((i, rsv))
        scores.sort(key = lambda x:x[1], reverse = True)
        return scores
    
    def search_one_doc(self, query):
        scores = self.doc_sort(query)
        return scores[0][0]


if __name__ == '__main__':
    pass