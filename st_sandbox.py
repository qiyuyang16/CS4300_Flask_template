import streamlit as st
from stqdm import stqdm
import numpy as np
import pandas as pd
import pdfplumber as pdf
import preprocessing
import cosine
import plotly.express as px

from pdfstructure.hierarchy.parser import HierarchyParser
from pdfstructure.source import FileSource
from pdfstructure.printer import JsonFilePrinter
import pathlib
import json

def text_on_page(dict_var, id_json, list_res, page):
    if type(dict_var) is dict:
        for k, v in dict_var.items():
            if k == id_json and v == page:
                if v > page: return list_res
                list_res.append(dict_var["text"])
            elif isinstance(v, dict):
                text_on_page(v, id_json, list_res, page)   
            elif isinstance(v, list):
                for item in v:
                    text_on_page(item, id_json, list_res, page)
    return list_res

def get_page(data, page):
    lines = []
    for chunk in data["elements"]:
        lines.extend(text_on_page(chunk, "page", [], page))             
    return lines

def get_histogram(docs, top = 20):
    tokens = []
    for s in docs.values():
        tokens += s.split()
    uniques, counts = np.unique(tokens, return_counts = True)
    sorted_inds = np.argsort(counts)
    uniques_sorted = uniques[sorted_inds[-top:]][::-1]
    counts_sorted = counts[sorted_inds[-top:]][::-1]
    return (uniques_sorted, counts_sorted)

file = st.file_uploader("test", type="pdf", key=2)
start = 1
max_val = 1000
end = 25
slider_val = st.slider('Page range:', min_value = start, max_value = max_val, value = (1,end), step = 1)


if file is not None:
    file_details = {"FileName":file.name,"FileType":file.type,"FileSize":str(file.size/1000000)+'mb'}
    data_load_state = st.text('Loading data... Thank you for waiting 😊')

    st.write(file_details)
    parser = HierarchyParser()
    source = FileSource(file, page_numbers=list(range(start, end)))
    document = parser.parse_pdf(source)
    printer = JsonFilePrinter()
    file_path = pathlib.Path('pdf.json')
    printer.print(document, file_path=str(file_path.absolute()))
    with open('pdf.json') as file:
        data = json.load(file)
    pages = {i: ' '.join(get_page(data,i)) for i in range(end)}
    
    doc_size = 0.25
    (formatted_docs, paragraph_page_idx) = preprocessing.get_formatted_docs(pages, doc_size)
    preprocessed_docs = preprocessing.get_preprocessed_docs(formatted_docs)
    data_load_state.text("Done!")
    st.subheader('First page in the selected range')
    {"page 1": pages[0]}
    st.subheader('Page range word distribution')
    (uniques, counts) = get_histogram(preprocessed_docs)
    fig = px.bar(x = uniques, y = counts)
    st.plotly_chart(fig)

    tfidf_vectorizer = cosine.get_tfidf_vectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(list(preprocessed_docs.values())).toarray()
    query = st.text_input("Search:")
    if query:
        q = cosine.get_query_vector(query, tfidf_vectorizer)
        cos_sims = cosine.get_cosine_sim(q, tfidf_matrix)
        (rankings, scores) = cosine.get_rankings(cos_sims)

        idx = rankings[0]
        score = scores[0]
        page_num = paragraph_page_idx[idx]+1
        doc = formatted_docs[idx]
        if score>0.0:   
            st.subheader("Similarity: " + str(score))
            {"page "+str(page_num):str(doc)}
        else:
            st.subheader("No matches found.")

st.subheader('made with ❤️ by:')
st.markdown('[Vince Bartle](https://bartle.io) (vb344) | [Dubem Ogwulumba](https://www.linkedin.com/in/dubem-ogwulumba/) (dao52) | [Erik Ossner](https://erikossner.com/) (eco9) | [Qiyu Yang](https://github.com/qiyuyang16/) (qy35) | [Youhan Yuan](https://github.com/nukenukenukelol) (yy435)')