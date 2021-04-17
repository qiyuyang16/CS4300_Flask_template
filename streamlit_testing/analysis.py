import streamlit as st
import pandas as pd
import numpy as np
import pdfplumber as pdf
from stqdm import stqdm
import re
import string
import matplotlib.pyplot as plt

# file = './Nurse.pdf'
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
