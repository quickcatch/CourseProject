import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from joblib import dump, load
import pandas as pd
from sys import argv, exit
from crawler import text_from_html, get_html
import nltk, string
from tqdm import tqdm
from itertools import chain

remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)


def get_lines(file_name):
    """Gets lines from file

    Args:
        file_name (str): file name

    Returns:
        str: concatenated lines
    """
    with open(file_name, "r", encoding="utf8") as f:
        lines = "".join(f.readlines()[1:])
        if len(lines) > 0:
            return lines
        else:
            return None


def get_file_names(directory, filter=set()):
    """Gets filenames from root data directory

    Args:
        directory (str): root data directory
        filter (set, optional): set of urls to include. Defaults to set().

    Returns:
        list: list of filenames
    """
    filenames = []
    for foldername in tqdm(os.listdir(directory), desc="Getting files"):
        # access directory of certain day
        daydir = os.path.join(directory, foldername)
        if os.path.isdir(daydir):
            max_count = 2
            for i, filename in enumerate(os.listdir(daydir)):
                if i >= max_count:
                    break
                f = os.path.join(daydir, filename)
                if len(filter) > 0:
                    with open(f, "r", encoding="utf8") as filtered_f:
                        url = parse_metadata(filtered_f.readline())["url"]
                        if url in filter:
                            filenames.append(f)
                else:
                    if os.path.isfile(f):
                        filenames.append(f)
    return filenames


def stem_tokens(tokens):
    """Stems tokens

    Args:
        tokens (seq): sequence of tokens

    Returns:
        Generator: generator of stemmed items
    """
    stemmer = nltk.stem.porter.PorterStemmer()
    return (stemmer.stem(item) for item in tokens)


def normalize(text):
    """Converts words to lowercase, removes punctuation, and stems

    Args:
        text (str): text to normalize

    Returns:
        str: normalized text
    """
    return stem_tokens(
        nltk.word_tokenize(text.lower().translate(remove_punctuation_map))
    )


def parse_metadata(metadata):
    """Parses metadata line from file

    Args:
        metadata (str): metadata line

    Returns:
        dict: dict containing title and url
    """
    split_triple = metadata.split("---")
    url = split_triple[1].split("/------------------------------")[0]
    return {"title": split_triple[0], "url": url}


def clustering(
    directory, dest_dir, num_clusters=5, max_iterations=200, vectorizer_path=None
):
    """Clusters text documents using KMeans

    Args:
        directory (str): root directory containing text documents
        dest_dir (str): Folder to save model to
        num_clusters (int, optional): Number of clusters. Defaults to 5.
        max_iterations (int, optional): Max number of K-Means iterations. Defaults to 200.
        vectorizer_path ([type], optional): Filename of saved vectorizer object. Defaults to None.
    """
    filenames = get_file_names(directory)
    print(f"{len(filenames)} total files")
    file_contents_fit = (
        "".join(open(f, "r", encoding="utf8").readlines()[1:]) for f in filenames
    )
    file_contents_transform = (
        "".join(open(f, "r", encoding="utf8").readlines()[1:]) for f in filenames
    )
    urls = (
        parse_metadata(open(f, "r", encoding="utf8").readline())["url"]
        for f in filenames
    )
    titles = (
        parse_metadata(open(f, "r", encoding="utf8").readline())["title"]
        for f in filenames
    )
    if vectorizer_path == None or not os.path.exists(vectorizer_path):
        tfidf_vectorizer = TfidfVectorizer(
            use_idf=True, stop_words={"english"}, max_df=0.7, tokenizer=normalize
        )
        vectorizer = tfidf_vectorizer.fit(file_contents_fit)
    else:
        vectorizer = load(vectorizer_path)
    tfidf_matrix = vectorizer.transform(file_contents_transform)
    print("Done transforming")
    km = KMeans(n_clusters=num_clusters, max_iter=max_iterations, n_init=10)
    km = km.fit(tfidf_matrix)
    labels = km.labels_

    # to re-access the file, call load(filename)
    # can compress this kmeans file with arg compress=, will put both files in directory with specific names
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)
    dump(km, os.path.join(dest_dir, "model.pkl"))
    URL_cl = pd.DataFrame(
        list(
            zip(
                urls,
                titles,
                labels,
            )
        ),
        columns=["URL", "Title", "cluster"],
    )
    dump(URL_cl, os.path.join(dest_dir, "dataframe.pkl"))
    dump(vectorizer, os.path.join(dest_dir, "vectorizer.pkl"))


class CosSimilarity:
    def __init__(self, directory, model, df, vect):
        """Initializes CosSimilarity object

        Args:
            directory (str): data directory
            model (sklearn.cluster.KMeans): trained cluster model
            df (pd.DataFrame): dataframe storing URL's, Titles, and cluster label
            vect (TfidfVectorizer): Trained TfidfVectorizer
        """
        self.vectorizer = TfidfVectorizer(
            use_idf=True, stop_words={"english"}, tokenizer=normalize, dtype=np.float32
        )
        self.directory = directory
        self.model = model
        self.df = df
        self.existing_vect = vect

    def cos_similarity(self, texts):
        """Calculates cos similarity matrix between list of text documents

        Args:
            texts (list): list of text documents, 1st element must be the document we want to find similar documents for

        Returns:
            np.ndarray: 1st column of similarity matrix representing similarities with other documents
        """
        tfidf = self.vectorizer.fit_transform(texts)
        result = ((tfidf * tfidf.T).A)[1:, 0]
        return result

    def get_similarity(self, url):
        """Gets similarity matrix and urls/titles for given url

        Args:
            url (str): url to get similarity matrix for

        Returns:
            tuple: tuple containing similarity vector, urls, and titles
        """
        cluster = classify(url, self.model, self.existing_vect)
        urls = set(self.df[self.df["cluster"] == cluster]["URL"])
        titles = set(self.df[self.df["cluster"] == cluster]["Title"])
        html = get_html(url)
        html_text = text_from_html(html)
        filenames = get_file_names(self.directory, filter=urls)
        texts = chain(
            [html_text],
            ("".join(open(f, "r", encoding="utf8").readlines()[1:]) for f in filenames),
        )
        sim = self.cos_similarity(texts)
        return (sim, list(urls), list(titles))

    def get_most_similar(self, matrix, urls, titles, num_docs=1):
        """Gets most similar documents according to similarity vector

        Args:
            matrix (np.ndarray): similarity vector
            urls (list): list of urls
            titles (list): list of titles
            num_docs (int, optional): Number of similar documents to find. Defaults to 1.

        Returns:
            tuple: tuple containing list of urls and list of titles of similar documents
        """
        assert type(urls) == list
        ind = np.argpartition(matrix, -num_docs)[-num_docs:]
        return ([urls[i] for i in ind], [titles[i] for i in ind])


def classify(url, model, vectorizer):
    """Predicts cluster of url

    Args:
        url (str): url of article
        model (sklearn.cluster.KMeans): trained model
        vectorizer (TfIdfVectorizer): Trained vectorizer

    Returns:
        [type]: [description]
    """
    html = get_html(url)
    text = text_from_html(html)
    tfdif_matrix = vectorizer.transform([text])
    result = model.predict(tfdif_matrix)
    if type(result) == list or type(result) == np.ndarray:
        return result[0]
    return result


def get_similar_docs(url, cos, num_similar=5):
    """Gets similar docs for given url

    Args:
        url (str): url of article
        cos (CosSimilarity): CosSimilarity object
        num_similar (int, optional): number of similar docs to retrieve. Defaults to 5.

    Returns:
         tuple: tuple containing list of urls and list of titles of similar documents
    """
    matrix, urls, titles = cos.get_similarity(url)
    return cos.get_most_similar(matrix, urls, titles, num_similar)


if __name__ == "__main__":

    print(argv)
    if len(argv) < 3:
        print("bad args")
        exit(1)
    if argv[3]:
        clustering(
            argv[1],
            argv[2],
            num_clusters=int(argv[3]),
            vectorizer_path="clusters/vectorizer.pkl",
        )
    else:
        clustering(argv[1], argv[2], vectorizer_path="clusters/vectorizer.pkl")
    # print(get_similar_docs("https://www.detroitnews.com/story/business/2021/12/07/amazon-aws-cloud-users-report-issues-accessing-websites/6419088001/"))
