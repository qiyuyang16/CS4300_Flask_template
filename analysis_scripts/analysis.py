import pdfplumber
import re
import string
import numpy as np
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
#from flask import app
import os

"""
def clean_string(s):
    '''
    Pre-process text
    input: string
    output: string
    '''
    # TODO better cleaning/pre-processing
    text = s.lower()
    text = re.sub('\[.*?\]', ' ', text) #brackets
    text = re.sub('[%s]' % re.escape(string.punctuation), ' ', text) #punctions
    text = re.sub('\w*\d\w*', ' ', text) #digits
    text = re.sub('[’’“”…]', ' ', text) #quotes
    text = re.sub('\n', ' ', text) #newlines
    text = re.sub('♪', ' ', text) #symbols
    text = re.sub('–', ' ', text) #dashes
    return text

def clean_corpus(corpus):
    '''
    [corpus]: List<Tuple(page_num, text_string)>
    output: pre-processed corpus
    '''
    # TODO save as txt / hook up with backend
    result = [(i, clean_string(s)) for (i, s) in corpus]
    return result

def tokenize(corpus):
    '''
    [corpus]: Pre-processed corpus, List<Tuple(page_num, text_string)>
    output: list of tokens for entire corpus
    '''
    # TODO better tokenization
    tokens = []
    for _,s in corpus:
        tokens += s.split(' ')
    return tokens

def get_display_text(cleaned_corpus):
    tokens = tokenize(cleaned_corpus)
    lines = ""
    with open("output.txt", "w", encoding = 'utf8') as txt_file:
        for line in tokens:
            txt_file.write(" ".join(line) + "\n") 
            lines += " ".join(line)+ "\n"
    return lines
    

def get_pages(file):
    '''
    Gets list of page text.
    input: path to the pdf file
    output: list of tuples (page #, page text string)
    '''
    corpus = []
    with pdfplumber.open(file) as pdf:
        for i, page in enumerate(pdf.pages):
            corpus.append((i, page.extract_text()))
    pdf.close()
    return corpus

def make_wordcount_hist(corpus):
    '''
    Generate a histogram of word counts from given text, open a new window with the histogram
    input: cleaned corpus that has been tokenized
    output: histogram: the number of counts for top frequent words
    '''
    tokens = tokenize(corpus)
    uniques, counts = np.unique(tokens, return_counts = True)
    plt.bar(uniques[:20], counts[:20], align='center')
    #plt.savefig(os.path.join(app.root_path, 'static', 'hist.png'), dpi=600)
    plt.savefig('hist.png', dpi=600)
    plt.show()

#if __name__ == "__main__":
 #   # TODO take in command line argument / find a way to hook up this to backend
  #  corpus = clean_corpus(get_pages(file))
   # get_display_text(corpus)
    #make_wordcount_hist(corpus)
    
"""

def get_pages(file):
    '''
    Gets list of page text.
    input: path to the pdf file
    output: list of tuples (page #, page text string)
    '''
    corpus = []
    with pdfplumber.open(file) as pdf:
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
    text = re.sub('[^0-9a-z]+', ' ', s) # replace non-alphanumeric chars with space
    return text


def tokenize(s):
    '''
    Second stage of pre-processing: tokenize the text
    [s]: string
    output: list of tokens
    '''
    # TODO better tokenization
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


def clean_corpus(corpus):
    '''
    [corpus]: List<Tuple(page_num, text_string)>
    output: pre-processed corpus
    '''
    # TODO save as txt / hook up with backend
    result = [(i, clean_tokens(tokenize(clean_string(s))) ) for (i, s) in corpus if s]
    result = [(i, arr) for (i, arr) in result if arr] # remove empty pages
    return result


def get_display_text(cleaned_corpus):
    lines = ""
    with open("output.txt", "w", encoding = 'utf8') as txt_file:
        for _,line in cleaned_corpus:
            if line:
                txt_file.write(" ".join(line) + "\n") 
                lines += " ".join(line)+ "\n"
    return lines


def make_wordcount_hist(corpus, top = 5):
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
    ax.bar(uniques_sorted, counts_sorted, align = 'center')
    plt.setp(ax.get_xticklabels(), rotation='vertical')
    #plt.savefig(os.path.join(app.root_path, 'static', 'hist.png'), dpi=600)
    fig.savefig('hist.png', dpi=600)
    plt.show()

"""
if __name__ == "__main__": 
    corpus = clean_corpus(get_pages(file))
    get_display_text(corpus)
    make_wordcount_hist(corpus, 20)
"""