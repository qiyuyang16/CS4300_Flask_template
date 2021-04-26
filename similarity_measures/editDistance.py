import numpy as np
import preprocessing
import nltk
nltk.download('stopwords')

"""
Code is edited based on Assignment3 from CS4300 Spring 2021
"""
#Define cost for each operations (insertion, deletion, substitution)
def insertion_cost(message, j):
    return 1

def deletion_cost(query, i):
    return 1

def substitution_cost(query, message, i, j):
    if query[i-1] == message[j-1]:
        return 0
    else:
        return 2

def edit_matrix(query, message):
    """ calculates the edit matrix
    
    Arguments
    =========
    query: query string,
    message: message string,
    
    Returns:
        edit matrix {(i,j): int}
    """
    
    m = len(query) + 1
    n = len(message) + 1
    
    matrix = np.zeros((m, n))
    for i in range(1, m):
        matrix[i, 0] = matrix[i-1, 0] + insertion_cost(query, i)
    
    for j in range(1, n):
        matrix[0, j] = matrix[0, j-1] + insertion_cost(message, j)
    
    for i in range(1, m):
        for j in range(1, n):
            matrix[i, j] = min(
                matrix[i-1, j] + deletion_cost(query, i), # "down" or delete op
                matrix[i, j-1] + insertion_cost(message, j), # "right" or insert op
                matrix[i-1, j-1] + substitution_cost(query, message, i, j) # "diagnol" or sub op
            )
    
    return matrix

def edit_distance(query, message):
    """ Edit distance calculator
    
    Arguments
    =========
    query: query string,
    message: message string,
    
    Returns:
        edit cost (int)
    """
        
    query = query.lower()
    message = message.lower()
    
    m = edit_matrix(query, message)
    return m[-1][-1]

def edit_distance_search(query, msgs):
    """ Edit distance search
    
    Arguments
    =========
    query: string,
        The query we are looking for.
        
    msgs: list of messages
    
    Returns
    =======
    
    result: list of similarity scores.
    """
    res = []
    for m in msgs:
        res.append(edit_distance(query,m))
    return res

def display_rankings(scores, formatted_docs, paragraph_page_idx, top=10):
    """
    Arguments
    =========
    score: list of float,
        A unsorted list of similarity scores
    
    formatted_docs: dict,
        key = index of paragraph, value = paragraph string
    
    paragraph_page_index: dict,
        key = index of paragraph, value = page number 
        
    msgs: list of messages

    top: int
        num of top results to display
    
    Returns
    =======
    
    result: list of similarity scores.
    """
    rankings = np.argsort(scores)[-top:]
    rankingScores = np.array(scores)[rankings]
    for i in range(len(rankings)):
        idx = rankings[i]
        score = rankingScores[i]
        print(str(i+1) + ',   editDistance score: ' + str(score) + ',   page: ' + str(paragraph_page_idx[idx]))
        print(formatted_docs[idx])
        print('\n')

if __name__ == "__main__":
    pages = preprocessing.get_pages('../notebooks/pdftotext_result.txt')
    formatted_docs, paragraph_page_idx = preprocessing.get_formatted_docs(pages, 0.33)
    preprocessed_docs = preprocessing.get_preprocessed_docs(formatted_docs)

    test_query = "display protective behavior disproportionate (too little/too much) to client’s abilities or need for autonomy. Diabetic ketoacidosis CH/MS deficient Fluid Volume [specify] may be related to hyperosmolar urinary losses, gastric losses and inadequate intake, possibly evidenced by increased urinary output/dilute urine; reports of weakness, thirst; sudden weight loss, hypotension, tachycardia, delayed capillary refill, dry mucous membranes, poor skin turgor. imbalanced Nutrition: less than body requirements that may be related to inadequate utilization of nutrients (insulin deficiency), decreased oral intake, hypermetabolic state, possibly evidenced by recent weight loss, reports of weakness, lack of interest in food, gastric fullness/ abdominal pain, and increased ketones, imbalance between glucose/ insulin levels. Fatigue may be related to decreased metabolic energy production, altered body chemistry (insufficient insulin), increased energy demands (hypermetabolic state/infection), possibly evidenced by overwhelming lack of energy,"
    scores = edit_distance_search(test_query,preprocessed_docs.values())
    display_rankings(scores, formatted_docs, paragraph_page_idx, top=10)


