import pdfplumber
import re
import string
import numpy as np
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from flask import send_file
import os
import base64
from io import BytesIO


# extract text and page numbers
def get_pages(pdf_file):
    '''
    Gets list of page text.
    input: path to the pdf file
    output: list of tuples (page #, page text string)
    '''
    # TODO leading characters failed to recognize
    corpus = []
    with pdfplumber.open(pdf_file) as pdf:
        for i, page in enumerate(pdf.pages):
            corpus.append((i, page.extract_text()))
    pdf.close()
    return corpus


def clean_string(s):
    '''
    First stage of pre-processing: cleaning the string text
    input: string
    output: string
    '''
    # TODO more thorough
    # TODO convert accented letters to english
    # TODO non-word char in middle of words eg U.S.A. it's
    text = s.lower()
    text = re.sub('\n', ' ', text) # newline
    text = re.sub('[^0-9a-z]+', ' ', text) # replace non-alphanumeric chars with space
    return text


def tokenize(s):
    '''
    Second stage of pre-processing: tokenize the text
    [s]: string
    output: list of tokens
    '''
    return s.split(' ')


def clean_tokens(tokens):
    '''
    Third stage of pre-processing: remove useless tokens
    [tokens]: list of words
    output: list of words where useless tokens are removed
    '''
    # TODO more thorough
    stopwords_set = set(stopwords.words('english'))
    result = [w for w in tokens if w.isalpha()] # remove non-letter tokens
    result = [w for w in result if len(w) >= 2] # remove tokens below a certain length
    result = [w for w in result if w not in stopwords_set] # remove stopwords
    return result


def get_raw_corpus(pages):
    '''
    Output a "raw corpus", which tokenizes and removes meaningless non-word symbols from pdf text

    [pages]: List<Tuple(page_num, text_string)>
    output: List<Tuple(page_num, list of tokens)>
    '''
    result = [(i, tokenize(clean_string(s)) ) for (i, s) in pages if s]
    result = [(i, arr) for (i, arr) in result if arr] # remove empty pages
    return result


def get_clean_corpus(corpus):
    '''
    Output a "clean corpus", which removes useless tokens from the "raw corpus" 

    [corpus]: List<Tuple(page_num, list of tokens)>
    output: List<Tuple(page_num, list of tokens)>
    '''
    result = [(i, clean_tokens(arr)) for (i, arr) in corpus if arr]
    result = [(i, arr) for (i, arr) in result if arr] # remove empty pages
    return result


def get_display_text(corpus, write_to_local = False):
    lines = []
    for _,line in corpus:
        if line:
            lines.append(" ".join(line)+ "\n")
    if write_to_local:
        with open("display_text.txt", "w", encoding = 'utf8') as txt_file:
            for line in lines:
                txt_file.write(line)
    long_line = ""
    for line in lines:
        long_line += line
    return long_line


def make_wordcount_hist(corpus, top = 20, write_to_local = False):
    '''
    Generate a histogram of word counts from given text, open a new window with the histogram
    input: cleaned corpus that has been tokenized
    output: histogram: the number of counts for top frequent words
    '''
    tokens = []
    for _ , arr in corpus:
        tokens += arr
    uniques, counts = np.unique(tokens, return_counts = True)
    sorted_inds = np.argsort(counts)
    uniques_sorted = np.flip(uniques[sorted_inds[-top:]])
    counts_sorted = np.flip(counts[sorted_inds[-top:]])

    fig, ax = plt.subplots()
    ax.bar(uniques_sorted, counts_sorted)
    plt.setp(ax.get_xticklabels(), rotation='vertical')
    if write_to_local:
        fig.savefig('hist.png', dpi=600, bbox_inches = 'tight')
        plt.show()
    img = BytesIO()
    fig.savefig(img, format='png')
    plt.close(fig)
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    return plot_url


# if __name__ == "__main__":
#     pdf_file = '../pdfs/Curato.pdf'
#     pages = get_pages(pdf_file)
#     raw_corpus = get_raw_corpus(pages)
#     clean_corpus = get_clean_corpus(raw_corpus)
#     lines_text = get_display_text(clean_corpus, True)
#     print(lines_text[:100])
#     url = make_wordcount_hist(clean_corpus, 20, True)
#     print(url[:100])