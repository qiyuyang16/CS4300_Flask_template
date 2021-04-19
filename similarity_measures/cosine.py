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
    # TODO non-binary representation of query vector e.g. using tfidf_vectorizer.idf_
    features = tfidf_vectorizer.get_feature_names()
    inv_idx = {t:i for (i,t) in enumerate(features)}
    query_vec = np.zeros((len(features), ))
    for w in preprocessing.preprocess(query).split(' '):
        try:
            query_vec[inv_idx[w]] = 1
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
    norms_docs = np.linalg.norm(tfidf_matrix, axis = 1)
    dot_prods = np.dot(tfidf_matrix, query_vec)
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


# if __name__ == '__main__':
#     pages = preprocessing.get_pages('../streamlit_testing/pdftotext_result.txt')
#     (formatted_docs, paragraph_page_idx) = preprocessing.get_formatted_docs(pages, 0.33)
#     preprocessed_docs = preprocessing.get_preprocessed_docs(formatted_docs)
#     tfidf_vectorizer = get_tfidf_vectorizer()
#     tfidf_matrix = tfidf_vectorizer.fit_transform(list(preprocessed_docs.values())).toarray()

#     query = 'many years ago the nursing profession'
#     q = get_query_vector(query, tfidf_vectorizer)
#     cos_sims = get_cosine_sim(q, tfidf_matrix)
#     (rankings, scores) = get_rankings(cos_sims)
#     display_rankings(rankings, scores, formatted_docs, paragraph_page_idx)