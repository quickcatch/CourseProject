import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import time
from sklearn.cluster import KMeans
from joblib import dump
import pandas as pd
from sys import argv, exit
from crawler import text_from_html, get_html

def get_lines(file_name):
    with open(file_name, "r", encoding="utf8") as f:
        lines = "".join(f.readlines()[1:])
        if len(lines) > 0:
            return lines
        else: 
            return None


#provide the directory, the destination directory, number of kmeans clusters, and how many iterations for kmeans to go through
def clustering(directory, dest_dir, num_clusters=5, max_iterations=200):
    #for debugging purposes only
    #initial_time = time.time()
    filenames = []
    print(directory)
    for foldername in os.listdir(directory):
        # access directory of certain day
        daydir = os.path.join(directory, foldername)
        if os.path.isdir(daydir):
            max_count = 50
            for i, filename in enumerate(os.listdir(daydir)):
                if i >= max_count:
                    break
                f = os.path.join(daydir, filename)
                if os.path.isfile(f):
                    filenames.append(f)
    file_contents_fit = ("".join(open(f,"r",encoding="utf8").readlines()[1:]) for f in filenames)
    file_contents_transform = ("".join(open(f,"r",encoding="utf8").readlines()[1:]) for f in filenames)
    urls = (open(f,"r",encoding="utf8").readline() for f in filenames)
    #first_time = time.time()
    #print('time to access files: %s seconds' % (time.time() - initial_time))
    tfidf_vectorizer = TfidfVectorizer(use_idf=True, stop_words={'english'}, max_df=.7)
    vec = tfidf_vectorizer.fit(file_contents_fit)
    tfidf_matrix = vec.transform(file_contents_transform)
    print("Done transforming")
    #for debugging purposes only
    #second_time = time.time()
    #print('time to vectorize: %s seconds' % (time.time() - first_time))
    km = KMeans(n_clusters= num_clusters, max_iter=max_iterations, n_init=10)
    km = km.fit(tfidf_matrix)
    labels = km.labels_
    #for debugging purposes only
    #print('time for kmeans: %s seconds' % (time.time() - second_time))
    
    #to re-access the file, call load(filename)
    #can compress this kmeans file with arg compress=, will put both files in directory with specific names
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)
    dump(km, os.path.join(dest_dir,'model.pkl'))
    URL_cl = pd.DataFrame(list(zip(urls, labels)), columns= ['URL', 'cluster'])
    dump(URL_cl, os.path.join(dest_dir, 'dataframe.pkl'))
    dump(vec,os.path.join(dest_dir,'vectorizer.pkl'))

def classify(url, model, vectorizer):
    html = get_html(url)
    text = text_from_html(html)
    tfdif_matrix = vectorizer.transform([text])
    return model.predict(tfdif_matrix)
if __name__ == "__main__":
    print(argv)
    if len(argv) < 3:
        print("bad args")
        exit(1)
    if argv[3]:
        clustering(argv[1],argv[2],num_clusters=int(argv[3]))
    else:
        clustering(argv[1],argv[2])
