from sklearn.cluster import KMeans
from fastapi import FastAPI
from clustering import classify
from joblib import load
from sklearn.feature_extraction.text import TfidfVectorizer
import os
app = FastAPI()
cluster_dir = "clusters"
url_df = None
model = None
vectorizer = None

@app.on_event("startup")
async def startup():
    model = load(os.path.join(cluster_dir,"kmeans.pkl"))
    url_df = load(os.path.join(cluster_dir,"URL-cluster.pkl"))
    vectorizer = load(os.path.join(cluster_dir,"vectorizer"))


@app.get("/classify/{url}")
async def read_item(url):
    results = classify(url,cluster_dir)
    return {"results": results}