# 📖 microGoogle

### The Team
Vince Bartle (vb344), Qiyu Yang (qy35), Youhan Yu (yy435), Dubem Ogwulumba (dao52), Erik Ossner (eco9)

Applies information retrieval and unsupervised NLP methods at a pdf document scale. 


### How to use
Visit https://microgoogle.herokuapp.com

------
Demo day notes:

1. http://www.passuneb.com/elibrary/ebooks/Harry%20Potter%20and%20The%20Sorcerer%E2%80%99s%20Stone.pdf 
1. 1-word dispersion: Dursley Petunia Harry
1. cosine-SVD: harry potters family 
1. Verbatim: Family
1. Paragraph comparison: 309 and 316
1. Try submitting results and rating results throughout the app.

The main challenge to our project was in the fact that the database is being provided by the user, so we spent a lot of time thinking about compute at query time and controlling input PDF sizes. There was a lot of trial and error around getting a pdf parser that was really useful but also decently fast. There was one that didn’t extract enough information and one that extracted too much information mostly about images. We then found an obscure structure parsing library and played around at length with how to get paragraphs out of it efficiently which involves conversion to JSON and tree parsing. Using each of these variants essentially meant rebuilding the backend to accommodate the different upload type.

On information retrieval, the essence of this is building and exploring a TF-IDF. For large pdfs, the tf-idf matrix has an increasingly large number of terms, so cosine similarity scores get increasingly computationally expensive. We first used preprocessing to remove useless tokens in order to reduce corpus size, then we added singular value decomposition to reduce the dimensionality of the problem, which gave a much smaller document matrix. Which was great because we got improved confidence and speed for large pdf’s by removing noise. BUT we found that for small pdfs SVD would reduce the dimensionality too much such that cosine wasn’t able to meaningfully distinguish between documents. So we added a hyperparameter so SVD only runs if the vocabulary size exceeds 1000.
We also wanted to incorporate verbatim search into cosine similarity but couldn’t get around recomputing TF-IDF at query time and how much slower the overall app would be, we considered a linear combination but ran out of time. As they are, they’re just left as separate search bars to let a user see the differences. 

For future work, in increasing difficulty cost of implementation: 1. Some default pdf’s so a user doesn’t necessarily need to upload, 2. Pdf re-rendering so a user can see the actual results in the pdf, possibly being highlighted, 3. Automatic question suggestion based on the pdf analysis by finding key topics and injecting ‘what is [blank]’ as a suggestion 4. Neural nets for a question answering system 5. Rochio update based on the social voting scheme to enable finding specific items like lists and tables and having users inform a model that identifies lists or tables. This would enable for example: “Find all lists in this pdf” Which could then lead into “Find the lists that are instructions” then “Find instructions for blood pressure” And then ask the user if this format matches their expectation. We also don’t have a way of identifying and removing sections of a pdf that might not be relevant, like the page of contents or appendix. Allowing a user to remove these would likely clean up results significantly. 
