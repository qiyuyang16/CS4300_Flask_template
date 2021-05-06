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
import pdfplumber
import base64
import nltk
from nltk.corpus import webtext
from nltk.probability import FreqDist
import matplotlib.pyplot as plt
from collections import Counter


'''
for paragraph similarity heatmap: recommend paragraphs to look at based on their scores
e.g. if they're between .6 and .8 in similarity, they might be good matches.

lexical dispersion

add radio button or dropdown for default file selection

pdf stitching and pdf viewer

Should have a more colloquial explanation for what the similarity score means. 
    E.g. What is a 1.3 similarity score?

Question suggestions

t-SNE
'''


#for db
from google.cloud import firestore
db = firestore.Client.from_service_account_json("serviceAccountKey.json")
email_logged_in = ""
word_window = 10
count_words = lambda doc: len(list(''.join(list(doc)).split()))

def app():
    global email_logged_in
    choice = st.sidebar.selectbox("Menu", ["Login", "Sign Up"])
    if email_logged_in == "":
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
                        if st.sidebar.button("Logout"):
                            email_logged_in = ""
                            st.sidebar.success("Logged out! Use the sidebar to sign back in")

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
    else:
        st.sidebar.warning("You are already logged in!")
        if st.sidebar.button("Logout"):
            email_logged_in = ""
            st.sidebar.success("Logged out! Use the sidebar to sign back in")

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

    # def st_display_pdf(pdf_file):
    #     base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
    #     st.write(base64_pdf)
    #     pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    #     st.markdown(pdf_display, unsafe_allow_html=True)

    # Read from fire base if logged in
    counter_queries = 1  
    if not email_logged_in == "":
        
        queries_collection_user = db.collection("queries")
        user_queries = queries_collection_user.where(u'email', u'==', email_logged_in).order_by(u'timeStamp',direction=firestore.Query.DESCENDING).limit(5).stream()
        with st.beta_expander("Your Most Recent Queries:"):
            for doc in user_queries:
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
            if counter_queries == 1: 
                st.write("No queries...yet!")
    file = st.file_uploader("Upload:", type="pdf", key=2)
    file_length = 100
    if file is not None:
        with pdfplumber.open(file) as raw:
            file_length = len(raw.pages)
    if file_length > 20:
        slider_val = st.slider('Page range:', min_value = 1, max_value = file_length, value = (1,int(file_length*.1)), step = 1)
    if file_length <= 20:
        slider_val = st.slider('Page range:', min_value = 1, max_value = file_length, value = (1,file_length), step = 1)



    if slider_val[1]-slider_val[0]>50:
        st.write('Range greater than 50 pages, ‼️ this may run slowly.')
        st.subheader('')
    if file is not None:
        file_details = {"FileName":file.name,"FileType":file.type,"FileSize":str(file.size/1000000)+'mb'}
        data_load_state = st.text('Loading data... Thank you for waiting 😊. ')


        st.write(file_details)
        parser = HierarchyParser()
        source = FileSource(file, page_numbers=list(range(slider_val[0], slider_val[1])))

        @st.cache(suppress_st_warning=True)
        def fetch_pages(source):
            document = parser.parse_pdf(source)
            printer = JsonFilePrinter()
            file_path = pathlib.Path('pdf.json')
            printer.print(document, file_path=str(file_path.absolute()))
            
            with open('pdf.json') as json_file:
                data = json.load(json_file)
            json_file.close()
            pages = {i + 1 : get_page(data, i) for i in range(0, slider_val[1])}

            return pages, file_path
        pages, _ = fetch_pages(source)
        paragraphs = [i for j in [i[1] for i in pages.items()] for i in j]
        windowed_paragraphs = [i for i in list(enumerate(paragraphs)) if count_words(i[1])>word_window]
        text_blob = ' '.join([i[1] for i in windowed_paragraphs])
        word_list = text_blob.split()


        (formatted_docs, paragraph_page_idx) = preprocessing3.get_formatted_docs(pages)
        preprocessed_docs = preprocessing3.get_preprocessed_docs(formatted_docs)
        data_load_state.text("Done! Please note that if you receive an error messages from the server it will likely not impede app functionality.")

        with st.beta_expander('View word distribution.'):
            radio_1 = st.radio("Select 1-word or 2-word distribution.", ("1-word", "2-word", "1-word dispersion"))
            if radio_1 == "1-word":
                (uniques, counts) = get_histogram(preprocessed_docs)
                fig = px.bar(x = uniques, y = counts)
                st.plotly_chart(fig)
            if radio_1 == "2-word":
                bigrams = zip(word_list, word_list[1:])
                counts = Counter(bigrams)
                uniques = [str(i) for i in list(np.vstack(counts.most_common())[:,0][:20])]
                counts = list(np.vstack(counts.most_common())[:,1][:20])
                fig = px.bar(x=uniques,y=counts)
                st.plotly_chart(fig)
            if radio_1 == "1-word dispersion":
                dispersion = st.text_input("Insert words separated by spaces.")
                dispersion_query = (''.join(dispersion)).split()
                wt_words = text_blob.split()
                if dispersion_query:
                    points = [(x, y) for x in range(len(wt_words)) for y in range(len(dispersion_query)) if wt_words[x] == dispersion_query[y]]
                    if points:
                        x, y = zip(*points)
                    else:
                        x = y = ()
                    import plotly.graph_objects as go
                    fig = go.Figure(data=go.Scatter(
                        x = x,
                        y = y,
                        mode="markers",
                    ))

                    fig.update_layout(
                        title="Word occurance at x'th word index in document.",
                        yaxis = dict(
                            tickmode = 'array',
                            tickvals = list(range(max(y)+1)),
                            ticktext = dispersion_query
                        )
                    )
                    st.plotly_chart(fig)
                # fig.show()


        st.subheader('First paragraphs on page '+str(slider_val[0])+":")
        if len(pages[slider_val[0]]) >= 3:
            for i in range(3):
                st.markdown("<u>Paragraph "+str(i + 1)+"</u>: "+pages[slider_val[0]][i], unsafe_allow_html=True )
        else:
            st.markdown("Page "+str(slider_val[0])+ " is empty.")

        tfidf_vectorizer = cosine3.get_tfidf_vectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(list(preprocessed_docs.values())).toarray()
        (_, num_terms) = tfidf_matrix.shape
        query1 = st.text_input("Cosine-SVD Search")
        if query1:
            q = cosine3.get_query_vector(query1, tfidf_vectorizer)
            if num_terms > 1000:
                (doc_mat, weight_mat, term_mat) = cosine3.get_svd(tfidf_matrix)
                cos_sims = cosine3.get_cosine_sim_svd(q, doc_mat, weight_mat, term_mat)
            else:
                cos_sims = cosine3.get_cosine_sim(q, tfidf_matrix)
            (rankings, scores) = cosine3.get_rankings(cos_sims)

            ranking_lengths = []
            for i in range(len(rankings)):
                idx = rankings[i]
                score = scores[i]
                page_num = paragraph_page_idx[idx]
                doc = formatted_docs[idx]
                curr_len = count_words(doc)
                ranking_lengths.append(curr_len)
            global word_window
            word_window = st.slider("Minimum word count", min_value=1, max_value=max(ranking_lengths), value=10)
            for i in range(len(rankings)):
                # there's probably a more efficient way to do this but these are at most 10 loops so sufficient for now.
                idx = rankings[i]
                score = scores[i]
                page_num = paragraph_page_idx[idx]
                doc = formatted_docs[idx]
                curr_len = count_words(doc)
                if curr_len>=word_window:
                    # st.write(curr_len,word_window)
                    break


            if score>0.0:   
                st.subheader("Similarity: " + str(round(score,4)) + ", Ranking: " +str(i+1))
                st.markdown("<u>Match</u>: "+str(doc), unsafe_allow_html=True)
                st.markdown("<u>Page Number</u>: "+str(page_num), unsafe_allow_html=True)

                #columns used to layout the button to ask user to upload the result to db
                uploadCols = st.beta_columns(4)
                #columns used to write thank you message if user click upload
                thankyouCols = st.beta_columns(4)
                if uploadCols[-1].button("Submit Your Search Result for our Study!"):
                    thankyouCols[-1].write("Thank you! We can't get better without your support😃")
                    #write match and query to the db
                    doc_ref = db.collection("queries").document()
                    doc_ref.set({
                        "id":doc_ref.get().id,
                        "query":query1,
                        "topMatch":str(doc),
                        "timeStamp":firestore.SERVER_TIMESTAMP,
                        "upvote":0,
                        "queryType":"Cosine",
                        "email": email_logged_in
                    })
                    cosMultiSub = True

                #columns used to layout explanation of upload button
                explainCols = st.beta_columns(4)
                explainCols[-1].markdown("<i><small>By clicking the submit button you agree with our <a href=\
                    'https://theuniversityfaculty.cornell.edu/dean/academic-integrity/'>terms of service</a></small></i>", unsafe_allow_html=True)

                

            else:
                st.subheader("No matches found.")


        with st.beta_expander('Compare with Verbatim Search:'):
            query3 = st.text_input("Search:")
            verbatim_search = lambda query: [msg for msg in windowed_paragraphs if query in msg[1]]
            if query3:
                v_result = verbatim_search(query3)
                if len(v_result) == 0:
                    st.write("No matches found.")
                else:
                    st.write("Matches found. 🎉")
                    v_slider = st.slider("View at most this many matches:", 1, 100, 3)
                    display_result = v_result[:v_slider]
                    counter = 0
                    for pageNum,text in display_result:
                        counter += 1
                        st.subheader("Result " + str(counter) + ":")
                        st.markdown("&nbsp")
                        st.markdown("<u>Match</u>: "+str(text), unsafe_allow_html=True)
                        st.markdown("<u>Page Number</u>: "+str(pageNum), unsafe_allow_html=True)
                        st.markdown("&nbsp")
                        #columns used to layout the button to ask user to upload the result to db
                        uploadCols = st.beta_columns(4)
                        #columns used to write thank you message if user click upload
                        thankyouCols = st.beta_columns(4)
                        if uploadCols[-1].button("Submit Your Search Result for our Study",key="Verbatim"+str(counter)):
                            thankyouCols[-1].write("Thank you! We can't get better without your support😃")
                            #write match and query to the db
                            doc_ref = db.collection("queries").document()
                            doc_ref.set({
                                "id":doc_ref.get().id,
                                "query":query1,
                                "topMatch":str(doc),
                                "timeStamp":firestore.SERVER_TIMESTAMP,
                                "upvote":0,
                                "queryType":"Verbatim",
                                "email": email_logged_in
                            })

        with st.beta_expander('Explore Paragraph Similarities.'):
            sim_mat = tfidf_matrix@tfidf_matrix.T
            fig1 = px.imshow(sim_mat)
            st.plotly_chart(fig1)
            
            # windowed_paragraphs = [i for i in list(enumerate(paragraphs)) if count_words(i[1])>word_window]
            
            number_query1 = st.number_input("Select 1st paragraph", 0, len(paragraphs))
            number_query2 = st.number_input("Select 2nd paragraph", 0, len(paragraphs))

            st.write(paragraphs[number_query1])
            st.write(paragraphs[number_query2])
        
        # st.subheader('Paragraph similarity heatmap')

    queries_collection_ref = db.collection("queries")
    query = queries_collection_ref.order_by(u'timeStamp',direction=firestore.Query.DESCENDING).limit(5)
    counter = 0
    #helper function to write upvote onto the page
    def writeUpvote(voteCount):
        if voteCount < 0:
                st.markdown("<small>So far " + str(abs(voteCount)) + " people don't think it's a good match.</small>",unsafe_allow_html=True)
        else:
            st.markdown("<small>So far " + str(voteCount) + " people think it's a good match.</small>",unsafe_allow_html=True)
    
    #helper function to update upvote given doc id and queries collection ref. Return the new upvote
    def updateVotes(queries_collection_ref,id,inc):
        doc_ref = queries_collection_ref.document(id)
        latestUpvote = doc_ref.get().to_dict()["upvote"]
        if inc:
            latestUpvote += 1
        else:
            latestUpvote -= 1
        
        doc_ref.update({"upvote":latestUpvote})
        return latestUpvote
        
    with st.beta_expander("Recent Queries We Processed..."):
        for doc in query.stream():
            counter += 1
            doc_dict = doc.to_dict()
            st.markdown("<strong>Query " + str(counter) + "</strong>: \n", unsafe_allow_html=True)
            st.markdown("<u>Query</u>: "+doc_dict["query"]+"\n", unsafe_allow_html=True)
            st.markdown("<u>Top Match</u>: "+doc_dict["topMatch"]+"\n", unsafe_allow_html=True)
            st.markdown("<u>Search Method</u>: "+doc_dict["queryType"]+"\n", unsafe_allow_html=True)
            
            st.markdown("&nbsp")
            
            st.markdown("<i><small>Do you think this is a good match?</small></i>",unsafe_allow_html=True)
            cols = st.beta_columns(12)
            likeButton = cols[0].button("👍",key="YesButton"+str(counter))
            dislikeButton = cols[1].button("👎",key="NoButton"+str(counter))
            newUpvote = doc_dict["upvote"]
            if likeButton:
                newUpvote = updateVotes(queries_collection_ref,doc_dict["id"],True)
                writeUpvote(newUpvote)
            
            elif dislikeButton:
                newUpvote = newUpvote = updateVotes(queries_collection_ref,doc_dict["id"],False)
                writeUpvote(newUpvote)
            else:
                writeUpvote(newUpvote)

            if counter != 5:
                st.markdown("<hr>", unsafe_allow_html=True)
    # if file is not None:
    #     # st.write(file_path)   
    #     st_display_pdf(file)

    st.subheader('made with ❤️ by:')
    st.markdown('[Vince Bartle](https://bartle.io) (vb344) | [Dubem Ogwulumba](https://www.linkedin.com/in/dubem-ogwulumba/) (dao52) | [Erik Ossner](https://erikossner.com/) (eco9) | [Qiyu Yang](https://github.com/qiyuyang16/) (qy35) | [Youhan Yuan](https://github.com/nukenukenukelol) (yy435)')