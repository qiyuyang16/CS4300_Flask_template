import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import preprocessing


def get_tfidf_vectorizer(max_df = 0.9, min_df = 1, max_features = None):
    """
    return:
        tf-idf vectorizer
    """
    return TfidfVectorizer(max_df = max_df, min_df = min_df, max_features = max_features)


def get_query_vector(query, tfidf_vectorizer):
    """
    [query]: string
    [tfidf_vectorizer]: tfidf vectorizer after fit_transform
    return:
        1d numpy.array of length = num_features(tfidf_vectorizer) representing the query as binary vector
    """
    features = tfidf_vectorizer.get_feature_names()
    inv_idx = {t:i for (i,t) in enumerate(features)}
    query_vec = np.zeros((len(features), ))
    for w in preprocessing.preprocess(query).split(' '):
        try:
            query_vec[inv_idx[w]] = tfidf_vectorizer.idf_[inv_idx[w]]
        except KeyError:
            pass
    if not np.any(query_vec): # query vector is all zeros
        print('invalid query') # TODO better way to notify user
    return query_vec


def get_cosine_sim(query_vec, tfidf_matrix):
    """
    [query_vec]: query vector of shape (num_features, )
    [tfidf_matrix]: tf-idf matrix of shape (num_docs, num_features)
    return:
        1d numpy array of shape (num_docs, ) containing cosine similarity scores for query with each doc
    note: norm(query) is removed from equation since it's constant for all docs
    """
    norms_docs = np.linalg.norm(tfidf_matrix, axis = 1) * np.linalg.norm(query_vec)
    dot_prods = np.dot(tfidf_matrix, query_vec)
    return np.divide(dot_prods, norms_docs, out = np.zeros_like(dot_prods), where = (norms_docs != 0))


def get_svd(A, k_ratio = 0.5):
    """
    A = U @ diag(s) @ Vh

    [A]: numpy array of shape (m, n)
    [k_ratio]: real number between 0 and 1
    return:
        [U]: document matrix, shape (m, k)
        [s]: topic weights, shape (k, )
        [Vh]: transposed term matrix, shape (k, n)
    """
    (m,n) = A.shape
    k = int(min(m,n) * k_ratio)
    (U, s, Vh) = np.linalg.svd(A)
    return (U[:, :k], s[:k], Vh[:k, :])


def get_cosine_sim_svd(query_vector, U, s, Vh):
    """
    [query_vector]: query vector of shape (n, )
    [U]: document matrix, shape (m, k)
    [s]: topic weights, shape (k, )
    [Vh]: transposed term matrix, shape (k, n)
    return:
        1d numpy array of shape (m, ) containing cosine similarity scores for query with each doc
    """
    S1 = np.diag(1/(s + 1e-7))
    q = np.dot(S1 @ Vh, query_vector)
    norms_docs = np.linalg.norm(U, axis = 1) * np.linalg.norm(q)
    dot_prods = np.dot(U, q)
    return np.divide(dot_prods, norms_docs, out = np.zeros_like(dot_prods), where = (norms_docs != 0))


def get_rankings(cos_sims, top = 10):
    """
    [cos_sims]: cosine similarity scores of shape (num_docs, )
    [top]: how many top results are returned
    return:
        [rankings]: ranked list of document indices based on similarity
        [scores]: cosine similarity scores
    """
    rankings = np.argsort(cos_sims)[-top:][::-1]
    scores = cos_sims[rankings]
    return (rankings, scores)


def display_rankings(rankings, scores, formatted_docs, paragraph_page_idx):
    """
    [rankings]: ranked list of document indices based on similarity
    [scores]: cosine similarity scores
    [formatted_docs]: Dict{paragraph_idx: paragraph_text_string}
    [paragraph_page_idx]: Dict{paragraph_idx: page_num}
    """
    for i in range(len(rankings)):
        idx = rankings[i]
        score = scores[i]
        print(str(i+1) + ',   cosine score: ' + str(score) + ',   page: ' + str(paragraph_page_idx[idx]))
        print(formatted_docs[idx])
        print('\n')