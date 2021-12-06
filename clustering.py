import os
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import time
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from joblib import dump, load



#provide the directory, the destination, number of kmeans clusters, and how many iterations for kmeans to go through
def clustering(directory, dest_file, num_clusters=5, max_iterations=200):
    myList = list()
    for foldername in os.listdir(directory):
        # access directory of certain day
        daydir = os.path.join(directory, foldername)
        for filename in os.listdir(daydir):
            f = os.path.join(daydir, filename)
            if os.path.isfile(f):
                file = open(f, "r", encoding="utf8")
                myList.append(file.read())
    first_time = time.time()
    #print('time to access files: %s seconds' % (time.time() - initial_time))
    tfidf_vectorizer = TfidfVectorizer(use_idf=True, stop_words={'english'})
    tfdif_matrix = tfidf_vectorizer.fit_transform(myList)
    second_time = time.time()
    #print('time to vectorize: %s seconds' % (time.time() - first_time))
    km = KMeans(n_clusters= num_clusters, max_iter=max_iterations, n_init=10)
    km = km.fit(tfdif_matrix)
    #to re-access the file, call load(filename)
    #can compress this kmeans file with arg compress=, putting specific ending like .z will automatically compress to that file type
    dump(km, dest_file)


