import pdfplumber
import re
import string
import numpy as np
import matplotlib.pyplot as plt
file = '../pdfs/regularization.pdf'


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
    plt.savefig('hist.png', dpi=600)
    plt.show()

#if __name__ == "__main__":
 #   # TODO take in command line argument / find a way to hook up this to backend
  #  corpus = clean_corpus(get_pages(file))
   # get_display_text(corpus)
    #make_wordcount_hist(corpus)
    
    
    