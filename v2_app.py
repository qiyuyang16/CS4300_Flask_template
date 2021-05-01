import streamlit as st
from stqdm import stqdm
import numpy as np
import pandas as pd
import preprocessing
import cosine
import plotly.express as px

from pdfstructure.hierarchy.parser import HierarchyParser
from pdfstructure.source import FileSource
from pdfstructure.printer import JsonFilePrinter
import pathlib
import json

#for db
from google.cloud import firestore
db = firestore.Client.from_service_account_json("serviceAccountKey.json")
def app():
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

        parser = HierarchyParser()
        source = FileSource(file, page_numbers=list(range(start-1, end)))
        @st.cache(suppress_st_warning=True)
        def fetch_doc(source):
            return parser.parse_pdf(source)
        document = fetch_doc(source)
        printer = JsonFilePrinter()
        file_path = pathlib.Path('pdf.json')
        printer.print(document, file_path=str(file_path.absolute()))
        
        with open('pdf.json') as json_file:
            data = json.load(json_file)
        json_file.close()
        pages = {i : get_page(data, i) for i in range(slider_val[0], slider_val[1])}
        
        (formatted_docs, paragraph_page_idx) = preprocessing.get_formatted_docs(pages, max_paragraphs=5)
        preprocessed_docs = preprocessing.get_preprocessed_docs(formatted_docs)
        data_load_state.text("Done!")
        st.write(file_details)
        with st.beta_expander("PDF Extraction details"):
            st.subheader('First paragraphs on page '+str(slider_val[0]))
            if len(pages[slider_val[0]]) >= 5:
                for i in range(5):
                    st.markdown("<u>¶ "+str(i + 1)+"</u>: "+pages[slider_val[0]][i], unsafe_allow_html=True )
            else:
                for i in range(len(pages[slider_val[0]])):
                    st.markdown("<u>¶ "+str(i + 1)+"</u>: "+pages[slider_val[0]][i], unsafe_allow_html=True )

            st.subheader('PDF word distribution')
            (uniques, counts) = get_histogram(preprocessed_docs)
            fig = px.bar(x = uniques, y = counts)
            fig.update_xaxes(title_text='words')
            fig.update_yaxes(title_text='occurances')
            st.plotly_chart(fig)

            st.subheader('Paragraph similarity heatmap')

        tfidf_vectorizer = cosine.get_tfidf_vectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(list(preprocessed_docs.values())).toarray()
        query1 = st.text_input("Cosine-SVD Search")
        if query1:
            q = cosine.get_query_vector(query1, tfidf_vectorizer)
            cos_sims = cosine.get_cosine_sim(q, tfidf_matrix)
            (rankings, scores) = cosine.get_rankings(cos_sims)

            idx = rankings[0]
            score = scores[0]
            page_num = paragraph_page_idx[idx]+1
            doc = formatted_docs[idx]
            if score>0.0:   
                st.subheader("Similarity: " + str(score))
                st.markdown("<u>Match</u>: "+str(doc), unsafe_allow_html=True)
                st.markdown("<u>Page Number</u>: "+str(page_num), unsafe_allow_html=True)

                #write match and query to the db
                doc_ref = db.collection("queries").document()
                doc_ref.set({
                    "query":query1,
                    "topMatch":str(doc),
                    "timeStamp":firestore.SERVER_TIMESTAMP
                })

            else:
                st.subheader("No matches found.")
        query2 = st.text_input("Synonymized Query Search")
        query3 = st.text_input("Verbatim Search")
        
    st.subheader("Recent search results:")
    q_ref = db.collection("queries").order_by(u'timeStamp',direction=firestore.Query.DESCENDING)
    counter = 0
    for doc in q_ref.stream():
        counter += 1
        doc_dict = doc.to_dict()

        # st.markdown("<strong>Query " + str(counter) + "</strong>: \n", unsafe_allow_html=True)
        st.markdown("<u>Query</u>: "+doc_dict["query"]+"\n", unsafe_allow_html=True)
        st.markdown("<u>Top Match</u>: "+doc_dict["topMatch"]+"\n", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        if counter == 5:
            break
            

    st.subheader('made with ❤️ by:')
    st.markdown('[Vince Bartle](https://bartle.io) (vb344) | [Dubem Ogwulumba](https://www.linkedin.com/in/dubem-ogwulumba/) (dao52) | [Erik Ossner](https://erikossner.com/) (eco9) | [Qiyu Yang](https://github.com/qiyuyang16/) (qy35) | [Youhan Yuan](https://github.com/nukenukenukelol) (yy435)')
