import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import time
from sklearn.cluster import KMeans
from joblib import dump,load
import pandas as pd
from sys import argv, exit
from crawler import text_from_html, get_html
import nltk, string
from tqdm import tqdm
from itertools import chain
remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
def get_lines(file_name):
    with open(file_name, "r", encoding="utf8") as f:
        lines = "".join(f.readlines()[1:])
        if len(lines) > 0:
            return lines
        else: 
            return None


def get_file_names(directory,filter=set()):
    filenames = []
    for foldername in tqdm(os.listdir(directory),desc="Getting files"):
        # access directory of certain day
        daydir = os.path.join(directory, foldername)
        if os.path.isdir(daydir):
            max_count = 2
            for i, filename in enumerate(os.listdir(daydir)):
                if i >= max_count:
                    break
                f = os.path.join(daydir, filename)
                if len(filter) > 0:
                    with open(f,'r',encoding='utf8') as filtered_f:
                        url = parse_metadata(filtered_f.readline())['url']
                        if url in filter:
                            filenames.append(f)
                else:
                    if os.path.isfile(f):
                        filenames.append(f)
    return filenames
#provide the directory, the destination directory, number of kmeans clusters, and how many iterations for kmeans to go through

def stem_tokens(tokens):
    stemmer = nltk.stem.porter.PorterStemmer()
    return (stemmer.stem(item) for item in tokens)

'''remove punctuation, lowercase, stem'''
def normalize(text):
    return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))    

def parse_metadata(metadata):
    split_triple = metadata.split("---")
    url = split_triple[1].split("/------------------------------")[0]
    return {"title" : split_triple[0], "url" : url}

def clustering(directory, dest_dir, num_clusters=5, max_iterations=200, vectorizer_path=None):
    #for debugging purposes only
    #initial_time = time.time()
    stemmer = nltk.stem.porter.PorterStemmer()
    filenames =  get_file_names(directory)
    print(f"{len(filenames)} total files")
    file_contents_fit = ("".join(open(f,"r",encoding="utf8").readlines()[1:]) for f in filenames)
    file_contents_transform = ("".join(open(f,"r",encoding="utf8").readlines()[1:]) for f in filenames)
    urls = (parse_metadata(open(f,"r",encoding="utf8").readline())['url'] for f in filenames)
    titles = (parse_metadata(open(f,"r",encoding="utf8").readline())['title'] for f in filenames)
    if vectorizer_path == None or not os.path.exists(vectorizer_path):
        tfidf_vectorizer = TfidfVectorizer(use_idf=True, stop_words={'english'}, max_df=.7, tokenizer=normalize)
        vectorizer = tfidf_vectorizer.fit(file_contents_fit)
    else:
        vectorizer = load(vectorizer_path)
    tfidf_matrix = vectorizer.transform(file_contents_transform)
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
    URL_cl = pd.DataFrame(list(zip(urls, titles, labels, )), columns= ['URL', 'Title', 'cluster'])
    dump(URL_cl, os.path.join(dest_dir, 'dataframe.pkl'))
    dump(vectorizer,os.path.join(dest_dir,'vectorizer.pkl'))

class CosSimilarity:
    def __init__(self, directory,model,df,vect):
        self.vectorizer = TfidfVectorizer(use_idf=True, stop_words={'english'}, tokenizer=normalize, dtype=np.float32)
        self.directory = directory
        self.model = model
        self.df = df
        self.existing_vect = vect
    def cos_similarity(self,texts):
        tfidf = self.vectorizer.fit_transform(texts)
        result = ((tfidf * tfidf.T).A)[1:,0]
        return result
    def parse_metadata(metadata):
        split_triple = metadata.split("---")
        url = split_triple[1].split("/------------------------------")[0]
        return {"title" : split_triple[0], "url" : url}
    def get_similarity(self,url):
        cluster = classify(url,self.model, self.existing_vect)
        urls = set(self.df[self.df["cluster"] == cluster]['URL'])
        titles = set(self.df[self.df["cluster"] == cluster]['Title'])
        html = get_html(url)
        html_text = text_from_html(html)
        filenames = get_file_names(self.directory,filter=urls)        
        texts = chain([html_text],("".join(open(f,"r",encoding="utf8").readlines()[1:]) for f in filenames))
        sim = self.cos_similarity(texts)
        return (sim, list(urls), list(titles))
    def get_most_similar(self,matrix,urls, titles, num_docs=1):
        assert type(urls) == list
        ind = np.argpartition(matrix,-num_docs)[-num_docs:]
        return ([urls[i] for i in ind],[titles[i] for i in ind])

                
def classify(url, model, vectorizer):
    html = get_html(url)
    text = text_from_html(html)
    tfdif_matrix = vectorizer.transform([text])
    result = model.predict(tfdif_matrix)
    if type(result) == list or type(result) == np.ndarray:
        return result[0]
    return result
def get_similar_docs(url,cos,num_similar=5):
    matrix,urls, titles = cos.get_similarity(url)
    return cos.get_most_similar(matrix,urls, titles, num_similar)
if __name__ == "__main__":
    
    print(argv)
    if len(argv) < 3:
        print("bad args")
        exit(1)
    if argv[3]:
        clustering(argv[1],argv[2],num_clusters=int(argv[3]),vectorizer_path="clusters/vectorizer.pkl")
    else:
        clustering(argv[1],argv[2],vectorizer_path="clusters/vectorizer.pkl")
    #print(get_similar_docs("https://www.detroitnews.com/story/business/2021/12/07/amazon-aws-cloud-users-report-issues-accessing-websites/6419088001/"))
