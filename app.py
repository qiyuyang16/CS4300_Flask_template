import streamlit as st
from stqdm import stqdm
import numpy as np
import pdfplumber as pdf
import matplotlib.pyplot as plt
import preprocessing
import cosine


# TODO: SWITCH TO PDFTOTEXT FOR SPEED. This requires understanding how 
# st.file_uploader works though, there is an error where open(file) only 
# accepts a path, not an uploaded file object.
file = st.file_uploader("Uploaded Files", type='pdf')
if file is not None:
    file_details = {"FileName":file.name,"FileType":file.type,"FileSize":str(file.size/1000000)+'mb'}
    st.write(file_details)
    with pdf.open(file) as raw:
        length = len(raw.pages)
    raw.close()
    global slider_val
    slider_val = st.slider('number of pages', min_value = 1, max_value = length, value = (1, 1), step = 1)


@st.cache(suppress_st_warning=True)
def get_pages(file, slider_val, full=False):
    '''
    Extract text from pdf pages
    return:
        Dict{page_num: page_text_string}
    '''
    pages = {}
    with pdf.open(file) as raw:
        for i in stqdm(range(slider_val[0],slider_val[1]+1), desc="Thank you for waiting :).", mininterval=2):
            pages[i] = raw.pages[i-1].extract_text()
    raw.close()
    return pages


def get_histogram(formatted_docs, top = 20):
    tokens = []
    for s in formatted_docs.values():
        tokens += s.split()
    uniques, counts = np.unique(tokens, return_counts = True)
    sorted_inds = np.argsort(counts)
    uniques_sorted = np.flip(uniques[sorted_inds[-top:]])
    counts_sorted = np.flip(counts[sorted_inds[-top:]])
    return (uniques_sorted, counts_sorted)


if file is not None:
    data_load_state = st.text('Loading data...')
    pages = get_pages(file, slider_val)
    doc_size = 0.33
    (formatted_docs, paragraph_page_idx) = preprocessing.get_formatted_docs(pages, doc_size)
    preprocessed_docs = preprocessing.get_preprocessed_docs(formatted_docs)
    data_load_state.text("Done!")
    st.subheader('First page of the pdf: ')
    first_page = ' '.join(list(formatted_docs.values())[:int(np.ceil(1/doc_size))])
    st.write(first_page)

    (uniques, counts) = get_histogram(formatted_docs)
    fig, ax = plt.subplots()
    ax.bar(uniques, counts)
    plt.setp(ax.get_xticklabels(), rotation='vertical')
    st.pyplot(fig)

    tfidf_vectorizer = cosine.get_tfidf_vectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(list(preprocessed_docs.values())).toarray()
    
    query = 'many years ago the nursing profession' # TODO allow user input
    
    q = cosine.get_query_vector(query, tfidf_vectorizer)
    cos_sims = cosine.get_cosine_sim(q, tfidf_matrix)
    (rankings, scores) = cosine.get_rankings(cos_sims)

    # TODO display a ranked list not just the top result
    idx = rankings[0]
    score = scores[0]
    page_num = paragraph_page_idx[idx]
    doc = formatted_docs[idx]
    st.subheader("query: " + query)
    st.subheader("similarity score: " + str(score))
    st.subheader("page: " + str(page_num))
    st.subheader("text: ")
    st.markdown(str(doc))