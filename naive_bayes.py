# -*- encoding: utf-8 -*-
import logging
import sys
import pickle


handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '[%(levelname)s] %(asctime)s %(name)s: %(message)s')

handler.setFormatter(formatter)

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
LOG.addHandler(handler)


class BagOfWords(object):
    def __init__(self):
        self._bag_of_words = {}
        self._number_of_words = 0

    #不修改原来的词袋
    def __add__(self, other):
        """ Overloading of the "+" operator to join two BagOfWords """
        s = BagOfWords()
        s._number_of_words = self._number_of_words + other._number_of_words
        vocabulary = s._bag_of_words
        for key in self._bag_of_words:
            vocabulary[key] = self._bag_of_words[key]
            if key in other._bag_of_words:
                vocabulary[key] += other.__bag_of_words[key]

        for key in other._bag_of_words:
            if key not in vocabulary:
                vocabulary[key] = other._bag_of_words[key]
        return s

    # 在原来的词袋上新增。
    def merge_other(self, other):
        vocabulary = self._bag_of_words
        self._number_of_words = self._number_of_words + other._number_of_words
        for k in other._bag_of_words:
            if k in self._bag_of_words:
                vocabulary[k] += other._bag_of_words[k]
            else:
                vocabulary[k] = other._bag_of_words[k]

    def add_word(self, word):
        """ A word is added in the dictionary __bag_of_words"""
        self._number_of_words += 1
        if word in self._bag_of_words:
            self._bag_of_words[word] += 1
        else:
            self._bag_of_words[word] = 1

    def Frequecy(self, word):
        """ Returning the frequency of a word """
        if word in self._bag_of_words:
            return self._bag_of_words[word]
        else:
            return 0
    
    @property
    def SumFrequency(self):
        s = 0
        for w in self._bag_of_words:
            s += self._bag_of_words[w]
        return s


    @property
    def Words(self):
        """ Returning a list of the words contained in the object """
        return self._bag_of_words.keys()

    @property
    def BagOfWords(self):
        """ Returning the dictionary, containing the words (keys) with their 
            frequency (values)"""
        return self._bag_of_words

    def __repr__(self):
        words = ",".join([
            "[%s]:%d " % (i[0], i[1]) for i in sorted(
                self._bag_of_words.items(), key=lambda x: x[1], reverse=True)
        ])
        return "{Total: %d Words: {%s} }" % (self._number_of_words, words)


class Document(object):
    def __init__(self):
        self._words_and_freq = BagOfWords()
        self.category = None

    def load(self, tokens, cluster=None):
        for tok in tokens:
            self._words_and_freq.add_word(tok)
        if cluster is not None:
            self.category = cluster

        return self

    @property
    def BagOfWords(self):
        return self._words_and_freq

    @property
    def Words(self):
        return self._words_and_freq.Words

    

class DocumentCluster(object):
    def __init__(self):
        self._number_of_documents = 0
        self._words_and_freq = BagOfWords()

    def add_document(self, doc: Document):
        self._number_of_documents += 1
        self._words_and_freq.merge_other(doc._words_and_freq)

    @property
    def BagOfWords(self):
        return self._words_and_freq


class Pool(object):
    def __init__(self):
        self._vocabulary = BagOfWords()
        self._document_clusters = {}
        self._number_of_documents = 0
        self._cluster_and_freq = {}

        self._category_probs = {}

    def learn(self, documents):
        categories = list(set([doc.category for doc in documents]))
        for cat in categories:
            if cat not in self._document_clusters:
                LOG.debug("document pool new cluster %s", cat)
                self._document_clusters[cat] = DocumentCluster()

        for document in documents:
            if document.category is not None:
                self._document_clusters[document.category].add_document(
                    document)
                self._vocabulary.merge_other(document.BagOfWords)
                self._number_of_documents +=1
                if document.category not in self._cluster_and_freq:
                    self._cluster_and_freq[document.category] = 1
                else:
                    self._cluster_and_freq[document.category] +=1
            else:
                LOG.info("document has no category, learn ignored.")


    def prob(self, doc: Document):
        # 1. 计算先验概率每个类别的概率。
        # 2. 计算每个单词属于某个类别的先验概率.

        # 3. 将所有单词出现在这个类别的概率相乘
        # 4. 将所有单词出现的概率相乘
        # 5. 用 第 3 步的结果除以 4 得到的结果
        # 由于第三步和第四步得到的结果不稳定，需要重新变换，然后求值。

        prior_c_probs = {}
        prior_w_probs  = {}
        for c in self._cluster_and_freq:
            prior_c_probs[c] = float(self._cluster_and_freq[c])/self._number_of_documents

        # for w in doc.Words:
        #     prior_w_probs[w]= {}
        #     for c in self._document_clusters:
        #         p_w_c = (1+ self._document_clusters[c].BagOfWords.Frequecy(w))/(self._vocabulary._number_of_words + self._document_clusters[c].BagOfWords._number_of_words )
        #         LOG.debug("calculating prior prob word %s in cluster %s prob:%s ", w, c, p_w_c)
        #         prior_w_probs[w][c] = p_w_c
        
        LOG.debug("calculated prior probs for categories %s", prior_c_probs)
        # LOG.debug("prior_w_probs %s", prior_w_probs)

        # 参考 公式 https://www.python-course.eu/text_classification_introduction.php 
        for c in self._document_clusters:
            P_c = prior_c_probs[c]
            P_c_r = 0
            for c_i in self._document_clusters:
                P_c_i = prior_c_probs[c]
                P_d_c = 1
                P_c_i_c = P_c_i*1.0/P_c

                for w in doc.Words:
                    P_d_c = P_d_c * \
                    (1+ self._document_clusters[c_i].BagOfWords.Frequecy(w)*(self._vocabulary._number_of_words + self._document_clusters[c].BagOfWords.SumFrequency)*1.0)/(
                    (1+ self._document_clusters[c].BagOfWords.Frequecy(w))*(self._vocabulary._number_of_words + self._document_clusters[c_i].BagOfWords.SumFrequency))
                P_c_r += P_c_i_c * P_d_c

            if P_c_r == 0:
                LOG.warnning("prob zero")
            else:
                r = 1.0/P_c_r
                LOG.info("Document %s category %s prob %s", doc.Words, c, r)
        


# def main():
#     #  Load documents
#     LOG.info("start")
#     p = Pool()
#     a = Document()
#     a.load('aaaaabcdef', cluster="A")
#     b = Document()
#     b.load('bbbbbbcfmn', cluster="B")
#     c = Document()
#     c.load('cccccmnak', cluster= "C")
#     p.learn([a,b,c])

#     n = Document()
#     n.load('aa')
#     p.prob(n)


#     LOG.info("end.")


# if __name__ == '__main__':
#     main()
