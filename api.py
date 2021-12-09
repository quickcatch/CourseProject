from sklearn.cluster import KMeans
from fastapi import FastAPI
from clustering import classify, CosSimilarity, get_similar_docs
from joblib import load
from sklearn.feature_extraction.text import TfidfVectorizer
import os
app = FastAPI()
cluster_dir = "clusters"
data_dir = "data_entire"
url_df = None
model = None
vectorizer = None
cos = None

@app.on_event("startup")
async def startup():
    global model, url_df, cos, vectorizer
    model = load(os.path.join(cluster_dir,"model.pkl"))
    url_df = load(os.path.join(cluster_dir,"dataframe.pkl"))
    vectorizer = load(os.path.join(cluster_dir,"vectorizer.pkl"))
    cos = CosSimilarity(data_dir,model, url_df, vectorizer)

@app.get("/classify/{url:path}")
async def read_item(url):
    global cos
    #print(cos,vectorizer,url_df,model)
    docs, titles = get_similar_docs(url,cos)
    print(docs)
    print(titles)
    return {"docs": docs, "titles" : titles}