import pdfplumber
import re
import string
import numpy as np
import matplotlib.pyplot as plt
# from flask import app
import os


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


stopwords = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
     'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 
     'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 
     'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 
     'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 
     'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
      'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but',
       'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with',
        'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after',
         'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
          'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 
          'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 
          'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 
          'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should',
           "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren',
            "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 
            'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't",
             'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 
             'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren',
              "weren't", 'won', "won't", 'wouldn', "wouldn't"])

def clean_tokens(tokens):
    '''
    Third stage of pre-processing: remove useless tokens
    [tokens]: list of words
    output: list of words where useless tokens are removed
    '''
    # TODO more thorough
    result = [w for w in tokens if w.isalpha()] # remove non-letter tokens
    result = [w for w in result if len(w) >= 2] # remove tokens below a certain length
    result = [w for w in result if w not in stopwords] # remove stopwords
    return result


def clean_corpus(corpus):
    '''
    [corpus]: List<Tuple(page_num, text_string)>
    output: pre-processed corpus
    '''
    result = [(i, clean_tokens(tokenize(clean_string(s))) ) for (i, s) in corpus if s]
    result = [(i, arr) for (i, arr) in result if arr] # remove empty pages
    return result


def get_display_text(cleaned_corpus):
    lines = ""
    with open("output.txt", "w", encoding = 'utf8') as txt_file:
        for _,line in cleaned_corpus:
            if line:
                txt_file.write(" ".join(line) + "\n") # TODO is it really necessary to write to local txt
                lines += " ".join(line)+ "\n"
    return lines


def make_wordcount_hist(corpus, top = 10):
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

