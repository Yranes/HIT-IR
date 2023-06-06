import os
import pickle
from util import *
from BM25 import BM25
from tqdm import tqdm

class DocSearch:
    def __init__(self, doc_path = PASS_PATH, stp_path = STOP_WORDS_PATH, index_path = INDEX_PATH, segdoc_path = SEGDOC_PATH):
        self.docs = read_json(doc_path)
        self.stpwds = read_stp_word(stp_path)
        if os.path.exists(segdoc_path):
            self.segdocs = read_json(segdoc_path)
        else:
            seg_docs = []
            for pdoc in tqdm(self.docs):
                doc = pdoc['document']
                seg_doc_sent = seg_doc(doc, self.stpwds)
                seg_doc_word = [word for sentence in seg_doc_sent for word in sentence]
                seg_docs.append({"pid": pdoc['pid'], "document": seg_doc_word})
            self.segdocs = seg_docs
            write_json(segdoc_path, seg_docs)
        
        docs_list = []
        for psegdoc in self.segdocs:
            docs_list.append(psegdoc['document'])
        self.docs_list = docs_list
        self.search_model = BM25(self.docs_list)

        if os.path.exists(index_path):
            with open(index_path, 'rb') as f:
                self.word2id = pickle.load(f)
                self.word2doc = pickle.load(f)
        else:
            self.word2id = {}
            words_set = set()
            for pdoc in self.segdocs:
                for word in pdoc['document']:
                    words_set.add(word)
            for i, word in enumerate(words_set):
                self.word2id[word] = i
            self.word2doc = [{} for i in range(len(words_set))]
            for pdoc in tqdm(self.segdocs):
                pid, segdoc = pdoc['pid'], pdoc['document']
                for word in segdoc:
                    self.word2doc[self.word2id[word]][pid] = self.word2doc[self.word2id[word]].get(pid, 0) + 1
            with open(index_path, 'wb') as f:
                pickle.dump(self.word2id, f)
                pickle.dump(self.word2doc, f)
    
    def search(self, query):   
        def intersection(lst1, lst2):
            lst3 = [value for value in lst1 if value in lst2]
            return lst3
        
        def union(lst1, lst2):
            final_list = set(lst1 + lst2)
            return list(final_list)

        flag = 0
        if '&&' in query:
            flag = 1
            word_list = query.split('&&')
        elif '||' in query:
            flag = 2
            word_list = query.split('||')
        else: word_list = [query]

        doc_list = []
        for i, word in enumerate(word_list):
            doc_list.append([])
            word_ = word.strip()
            for key in self.word2doc[self.word2id[word_]]:
                doc_list[i].append(key)
        result = doc_list[0]
        if flag == 1:
            for i in range(1, len(word_list)):
                result = intersection(result, doc_list[i])
        elif flag == 2:
            for i in range(1, len(word_list)):
                result = union(result, doc_list[i])
        return result
    
    def model_search(self, query):
        return self.search_model.doc_sort(query)

    def Print(self, word):
        print(self.word2id[word])
        print(self.word2doc[self.word2id[word]])

def _main():
    s = DocSearch()
    Q = read_json('./data/segtest.json')
    stp = read_stp_word(STOP_WORDS_PATH)

    res = []
    for i, q in enumerate(Q):
        X = {}
        X['qid'] = q['qid']
        X['question'] = q['question']
        q_word = remove_stop_word(q['question'].split(), stp)
        X['pid'] = s.search_model.search_one_doc(q_word)
        res.append(X)

    write_json('./preprocessed/segtest.json', res)

if __name__ == '__main__':
    _main()