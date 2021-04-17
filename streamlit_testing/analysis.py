import streamlit as st
from stqdm import stqdm

import pandas as pd
import numpy as np
import pdfplumber as pdf
import re
import string
import matplotlib.pyplot as plt
from nltk.tokenize import TreebankWordTokenizer


treebank_tokenizer = TreebankWordTokenizer()

# file = './Nurse.pdf'

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
    slider_val = st.slider('number of pages', 0, length, (20,50), 1)

def clean_string(text):
    '''
    Pre-process text
    input: string
    output: string
    '''
    # TODO better cleaning/pre-processing
    sub = ''
    text = text.lower()
    text = re.sub(',', ' ', text)
    text = re.sub('-', ' ', text)
    text = re.sub('\[.*?\]', sub, text) #brackets
    text = re.sub('[%s]' % re.escape(string.punctuation), sub, text) #punctions
    text = re.sub('\w*\d\w*', sub, text) #digits
    text = re.sub('[’’“”…]', sub, text) #quotes
    text = re.sub('\n', ' ', text) #newlines
    text = re.sub('♪', sub, text) #symbols
    text = re.sub('–', sub, text) #dashes
    return text


@st.cache(suppress_st_warning=True)
def load_data(file, slider_val, full=False):
    '''
    Loads raw data as pages into a list.
    '''
    data = []
    with pdf.open(file) as raw:
        for i in stqdm(range(slider_val[0],slider_val[1]), desc="Thank you for waiting :).", mininterval=2):
            data.append((i, raw.pages[i].extract_text()))
    raw.close()
    return data

def process_data(data):
    return [(i[0],clean_string(i[1])) for i in data if i[1] != None]

def pdf_to_listOfDicts(pdf):
    result = []
    for ind,i in enumerate(pdf):
        cleaned_string =  clean_string(i)
        result.append({'page':ind,'text':cleaned_string,'toks':list(set(cleaned_string.split()))})
    return result

def build_inverted_index(data):
    result = {}
    for ind, msg in enumerate(data):
        for token in set(msg['toks']):
            msg_count = msg['toks'].count(token)
            if token not in result.keys():
                result[token] = [(ind, msg_count)]
            else:
                result[token].append((ind, msg_count))
    return result

def boolean_search(query_word,excluded_word, inverted_index): 
    # This is lacking a use.
    return list(set(np.vstack(inverted_index[query_word.lower()])[:,0]).difference(set(np.vstack(inverted_index[excluded_word.lower()])[:,0])))

def compute_idf(inv_idx, n_docs, min_df=15, max_df_ratio=0.90):
    id_frequencies = {}
    for term, documents in inv_idx.items():
        ratio = float(len(documents))/n_docs
        if ratio > max_df_ratio or min_df > len(documents):
            continue
        else:
            id_frequencies[term] = np.log2(n_docs/(len(documents)+1.))
    return id_frequencies

def compute_doc_norms(index, idf, n_docs):
    eq = lambda i, freq: np.square(i * np.array(freq))
    doc_norms = np.zeros(n_docs)
    for term, i in idf.items():
        doc, frequency = zip(*index[term])
        val = eq(i, frequency)
        for j in range(len(doc)):
            doc_norms[doc[j]] += val[j]
    doc_norms = np.sqrt(doc_norms)
    return doc_norms



def index_search(query, index, idf, doc_norms, tokenizer=treebank_tokenizer):
    tokens = tokenizer.tokenize(query.lower())
    q_term_freq = {token: tokens.count(token) for token in set(tokens)}
    norm = 0
    for t, f in q_term_freq.items():
        if t in idf.keys():
            norm = norm+np.square(f*idf[t])
    norm = np.sqrt(norm)
    
    results = np.zeros((np.shape(doc_norms)))
    if norm != 0:
        for t,f in q_term_freq.items():
            if t in idf.keys():
                ID, freq = zip(*index[t])
                num = f * idf[t]**2 * np.array(freq)
                for ind, d in enumerate(ID):
                    results[d] += num[ind]
        results = [r/(norm*doc_norms[ind]) if (r!=0 and doc_norms[ind] != 0) else 0 
                   for ind, r in enumerate(results)]
        results = sorted(list(zip(results, range(len(results)))), key= lambda l:l[0], reverse=True)
        return results
    
    else:
        return list(zip(results, range(len(results))))

# Need to open this up to user input.
query = "many years ago the nursing profession"

def best_page_for(query):
    confidence,page_number = index_search(query, inv_idx, idf_dict, doc_norms)[0]
    text=listOfDicts[page_number]['text']
    return confidence, page_number, text


if file is not None:
    data_load_state = st.text('Loading data...')
    data = process_data(load_data(file, slider_val))
    data_load_state.text("Done! (using st.cache)")
    st.subheader('first page')
    st.write(data[0][1])
    merged_data = ' '.join([i[1] for i in data])
    uniques, counts = np.unique(merged_data.split(), return_counts = True)
    plt.bar(uniques[:20], counts[:20], align='center')
    st.pyplot(plt)

    #Analysis post-histogram stage
    listOfDicts = pdf_to_listOfDicts(np.vstack(data)[:,1])
    inv_idx = build_inverted_index(listOfDicts)
    idf_dict = compute_idf(inv_idx, len(listOfDicts))
    doc_norms = compute_doc_norms(inv_idx, idf_dict, len(listOfDicts))
    ind_search = index_search(query, inv_idx, idf_dict, doc_norms)
    conf, pg, txt = best_page_for(query)

    st.subheader(query)
    st.subheader("confidence: "+str(conf))
    st.subheader("page: " + str(pg))
    st.subheader("text: " + str(txt))

