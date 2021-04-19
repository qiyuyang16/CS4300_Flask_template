import io
import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
stopwords_set = set(stopwords.words('english'))
porter = PorterStemmer()


def get_pages(txt_file):
    """
    [txt_file]: path to txt file
    return:
        Dict{page_num: page_text_string}
    """
    with io.open(txt_file, encoding = 'utf8') as f:
        txt_string = f.read()
    f.close()
    pages = dict(enumerate(txt_string.split('\n\n'), start = 1))
    return pages


def get_formatted_docs(pages, paragraph_size = 0.33):
    """
    Format the pages extracted from pdf, by removing excessive whitespaces 
    but preserving punctuations, capital cases, etc.

    [pages]: Dict{page_num: page_text_string}
    [paragragh_size]: portion of page to be considered a "paragraph"
    return:
        [formatted_docs]: Dict{parapgrah_idx: paragraph_text_string}
        [paragraph_page_idxs]: Dict{paragraph_idx: page_num}
    """
    formatted_docs = {}
    paragraph_page_idxs = {}
    paragraphs = []
    for page_num in pages.keys():
        page = pages[page_num]
        page = re.sub('-[\n\r\t\s]+', '', page) # words broken by line break
        page = re.sub('[\n\r\t\s]+', ' ', page) # remove line break, tabs, whitespaces
        # build paragraphs
        page = page.split()
        k = int(len(page)*paragraph_size)
        if k < 1:
            paragraphs += [(page_num, ' '.join(page))]
        else:
            paragraphs += [(page_num,' '.join(page[i:i+k])) for i in range(0, len(page), k)]
    for i in range(len(paragraphs)):
        formatted_docs[i] = paragraphs[i][1]
        paragraph_page_idxs[i] = paragraphs[i][0]
    return (formatted_docs, paragraph_page_idxs)


def preprocess(s, min_length = 2):
    """
    [s]: a string
    [min_length]: minimum length of tokens considered useful
    return:
        preprocessed string
    """
    # TODO more preprocessing steps
    result = s
    result = re.sub('[^a-zA-Z]+', ' ', result) # remove non-letter chars
    result = result.lower()
    result = result.split()
    result = [w for w in result if len(w) >= min_length] # remove tokens below a certain length
    result = [w for w in result if w not in stopwords_set] # remove stopwords
    result = [porter.stem(w) for w in result] # stemming
    result = [w for w in result if len(w) >= min_length] # remove tokens below a certain length again after stemming
    result = ' '.join(result)
    return result


def get_preprocessed_docs(formatted_docs):
    """
    Preprocess the formatted text, by removing useless tokens, etc.

    [formatted_docs]: Dict{parapgrah_idx: paragraph_text_string}
    return:
        [preprocessed_docs]: same structure, same length as [formatted_docs]
    """
    preprocessed_docs = {}
    for idx in formatted_docs.keys():
        preprocessed_docs[idx] = preprocess(formatted_docs[idx])
    return preprocessed_docs