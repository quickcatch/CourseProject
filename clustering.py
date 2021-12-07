import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import time
from sklearn.cluster import KMeans
from joblib import dump, load
import pandas as pd



#provide the directory, the destination directory, number of kmeans clusters, and how many iterations for kmeans to go through
def clustering(directory, dest_dir, num_clusters=5, max_iterations=200):
    file_URLS = list()
    fie_contents = list()
    #for debugging purposes only
    #initial_time = time.time()
    for foldername in os.listdir(directory):
        # access directory of certain day
        daydir = os.path.join(directory, foldername)
        for filename in os.listdir(daydir):
            f = os.path.join(daydir, filename)
            if os.path.isfile(f):
                file = open(f, "r", encoding="utf8")
                file_URLS.append(file.readline())
                fie_contents.append(file.readline())
    #first_time = time.time()
    #print('time to access files: %s seconds' % (time.time() - initial_time))
    tfidf_vectorizer = TfidfVectorizer(use_idf=True, stop_words={'english'})
    tfdif_matrix = tfidf_vectorizer.fit_transform(fie_contents)
    #for debugging purposes only
    #second_time = time.time()
    #print('time to vectorize: %s seconds' % (time.time() - first_time))
    km = KMeans(n_clusters= num_clusters, max_iter=max_iterations, n_init=10)
    km = km.fit(tfdif_matrix)
    labels = km.labels_
    #for debugging purposes only
    #print('time for kmeans: %s seconds' % (time.time() - second_time))
    
    #to re-access the file, call load(filename)
    #can compress this kmeans file with arg compress=, will put both files in directory with specific names
    dump(km, dest_dir + '\\kmeans.pkl')
    URL_cl = pd.DataFrame(list(zip(file_URLS, labels)), columns= ['URL', 'cluster'])
    dump(URL_cl, dest_dir + '\\URL-cluster.pkl')


