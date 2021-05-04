import streamlit as st
from stqdm import stqdm
import numpy as np
import pandas as pd
import preprocessing3
import cosine3
import plotly.express as px
import hashlib
import os
from pdfstructure.hierarchy.parser import HierarchyParser
from pdfstructure.source import FileSource
from pdfstructure.printer import JsonFilePrinter
import pathlib
import json

#for db
from google.cloud import firestore
db = firestore.Client.from_service_account_json("serviceAccountKey.json")
email_logged_in = ""
def app():
    global email_logged_in
    choice = st.sidebar.selectbox("Menu", ["Login", "Sign Up"])
    if choice == "Login":
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Login"):
            # Match from fire base
            check_email = db.collection("users").where(u'email', u'==', email).stream()
            user_dict = dict()
            for user in check_email:
                user_dict = user.to_dict()
                break
            if len(user_dict) > 0:
                salt = user_dict['salt']
                key = user_dict['key']
                new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
                if key == new_key:
                    st.sidebar.success("Logged in as {}".format(email))
                    email_logged_in = email
                    # Read from fire base
                    user_queries = db.collection("queries").where(u'email', u'==', email).stream()
                    counter_queries = 1  
                    for doc in user_queries:
                        if counter_queries == 1: 
                            st.write("Here are your most recent queries: ")
                        doc_dict = doc.to_dict()
                        st.markdown("<strong>Query " + str(counter_queries) + "</strong>: \n", unsafe_allow_html=True)
                        st.markdown("<u>Query</u>: "+doc_dict["query"]+"\n", unsafe_allow_html=True)
                        st.markdown("<u>Top Match</u>: "+doc_dict["topMatch"]+"\n", unsafe_allow_html=True)
                        if doc_dict["upvote"] < 0:
                            st.markdown("<small>So far " + str(abs(doc_dict["upvote"])) + "people don't think it's a good match.</small>",unsafe_allow_html=True)
                        else:
                            st.markdown("<small>So far " + str(doc_dict["upvote"]) + " people think it's a good match.</small>",unsafe_allow_html=True)
                        st.markdown("<hr>", unsafe_allow_html=True)
                        counter_queries += 1
                        if counter_queries > 5: break
                    if counter_queries == 1: 
                        st.write("No queries...yet!")
                else:
                    st.sidebar.warning("Incorrect Password!")
            else:
                st.sidebar.warning("No account with that email exists")
    else:
        new_email = st.sidebar.text_input("New Email")
        new_pass = st.sidebar.text_input("New Password", type='password')
        new_pass_2 = st.sidebar.text_input("Verify Password", type='password')
        if st.sidebar.button("Sign Up"):
            check_email = db.collection("users").where(u'email', u'==', new_email).stream()
            good_email = True
            for e in check_email:
                st.sidebar.warning("An account exists with this email already!")
                good_email = False
                break
            if new_pass == new_pass_2 and good_email:
                st.sidebar.success("Successfully created account! Login from the sidebar")
                #Write to firebase
                salt = os.urandom(32) # A new salt for this user
                key = hashlib.pbkdf2_hmac('sha256', new_pass.encode('utf-8'), salt, 100000)
                login_ref = db.collection("users").document()
                login_ref.set({
                    "email": new_email,
                    "salt": salt,
                    "key": key
                })
            elif good_email:
                st.sidebar.warning("Passwords do not match!")
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
        source = FileSource(file, page_numbers=list(range(start-1, end)))
        document = parser.parse_pdf(source)
        printer = JsonFilePrinter()
        file_path = pathlib.Path('pdf.json')
        printer.print(document, file_path=str(file_path.absolute()))
        
        with open('pdf.json') as json_file:
            data = json.load(json_file)
        json_file.close()
        pages = {i + start : get_page(data, i) for i in range(0, end-start+1)}
        
        (formatted_docs, paragraph_page_idx) = preprocessing3.get_formatted_docs(pages)
        preprocessed_docs = preprocessing3.get_preprocessed_docs(formatted_docs)
        data_load_state.text("Done!")
        st.subheader('First page in the selected range')
        if len(pages[1]) >= 5:
            for i in range(5):
                st.markdown("<u>Paragraph "+str(i + 1)+"</u>: "+pages[1][i], unsafe_allow_html=True )
        else:
            for i in range(len(pages[1])):
                st.markdown("<u>Paragraph "+str(i + 1)+"</u>: "+pages[1][i], unsafe_allow_html=True )
        st.write("........ (only initial paragraphs are shown)")
        st.subheader('Page range word distribution')
        (uniques, counts) = get_histogram(preprocessed_docs)
        fig = px.bar(x = uniques, y = counts)
        st.plotly_chart(fig)
        st.subheader('Paragraph similarity heatmap')


        tfidf_vectorizer = cosine3.get_tfidf_vectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(list(preprocessed_docs.values())).toarray()
        (doc_mat, topics, term_mat) = cosine3.get_svd(tfidf_matrix)
        query1 = st.text_input("Cosine-SVD Search")
        if query1:
            q = cosine3.get_query_vector(query1, tfidf_vectorizer)
            cos_sims = cosine3.get_cosine_sim(q, doc_mat, topics, term_mat)
            (rankings, scores) = cosine3.get_rankings(cos_sims)

            idx = rankings[0]
            score = scores[0]
            page_num = paragraph_page_idx[idx]
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
                    "timeStamp":firestore.SERVER_TIMESTAMP,
                    "upvote":0,
                    "email": email_logged_in
                })

            else:
                st.subheader("No matches found.")
        st.write("Following methods are under construction 😊 Stay tuned!")
        query2 = st.text_input("Synonymized Query Search")
        query3 = st.text_input("Verbatim Search")
        
    st.subheader("Recent search results:")
    q_ref = db.collection("queries").order_by(u'timeStamp',direction=firestore.Query.DESCENDING)
    counter = 0
    yesButtons = []
    noButtons = []
    for doc in q_ref.stream():
        counter += 1
        doc_dict = doc.to_dict()

        st.markdown("<strong>Query " + str(counter) + "</strong>: \n", unsafe_allow_html=True)
        st.markdown("<u>Query</u>: "+doc_dict["query"]+"\n", unsafe_allow_html=True)
        st.markdown("<u>Top Match</u>: "+doc_dict["topMatch"]+"\n", unsafe_allow_html=True)
        if "upvote" in doc_dict:
            if doc_dict["upvote"] < 0:
                st.markdown("<small>So far " + str(abs(doc_dict["upvote"])) + "people don't think it's a good match.</small>",unsafe_allow_html=True)
            else:
                st.markdown("<small>So far " + str(doc_dict["upvote"]) + " people think it's a good match.</small>",unsafe_allow_html=True)
        else:
            st.markdown("<small>So far 0 people think it's a good match.</small>",unsafe_allow_html=True)

        st.markdown("<i><small>Do you think this is a good match?</small></i>",unsafe_allow_html=True)
        yesButtons.append(st.button("👍",key="YesButton"+str(counter)))
        noButtons.append(st.button("👎",key="NoButton"+str(counter)))

        st.markdown("<hr>", unsafe_allow_html=True)

        if counter == 5:
            break
            

    st.subheader('made with ❤️ by:')
    st.markdown('[Vince Bartle](https://bartle.io) (vb344) | [Dubem Ogwulumba](https://www.linkedin.com/in/dubem-ogwulumba/) (dao52) | [Erik Ossner](https://erikossner.com/) (eco9) | [Qiyu Yang](https://github.com/qiyuyang16/) (qy35) | [Youhan Yuan](https://github.com/nukenukenukelol) (yy435)')