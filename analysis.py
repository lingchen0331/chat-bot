import sqlite3
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import Pipeline
from sklearn import metrics
import numpy as np

punctuation = set([',','.','?','!', ':'])

try:
    conn = sqlite3.connect("jarvis.db")
    c = conn.cursor()
except:
    print("Can't connect to sqlite3 database...")
   
    
text_clf = Pipeline([('vect', CountVectorizer()),('tfidf', TfidfTransformer()),('clf', MultinomialNB()),])
text_clf = text_clf.fit(index_list, action_list)

test_txt = ['what time is it?', 'get me some pizza']
action = ['TIME']

pr = []

for i in range(len(test_txt)):
    pr.append(text_clf.predict([test_txt[i]])[0])
    
print(pr)
print(action)
print(np.mean(pr == action))