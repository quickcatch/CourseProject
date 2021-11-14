from bs4 import BeautifulSoup as bs
import requests
from bs4.element import Comment
import datetime
from os import path,mkdir
import time
import validators
import numpy as np
from multiprocessing import Process

def should_check_url(url : str, blacklisted_sites : dict):
    split = url.split(".")
    if ("www" in split[0] and blacklisted_sites.get(split[1]) != None):
        return False
    elif(blacklisted_sites.get(split[0]) != None):
        return False
    return True

def get_blacklisted_sites(file_name):
    with open(file_name, 'r') as f:
        return f.readlines()

def get_html(url,number_of_retries_remaining=5):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code < 200 or r.status_code > 299: # error ocurred
            if r.status_code == 503:
                if number_of_retries_remaining > 0:
                    time.sleep(3)
                    return get_html(url,number_of_retries_remaining - 1)
            print(f"Error getting html for {url} with status code {r.status_code}")
            return None 
        return r.text
    except Exception as e:
        print(f"Error getting html for {url} due to timeout")


def tag_visible(element):
    if element.parent.name in ['a','style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def is_valid_url(url):
    return validators.url(url)

def get_all_articles(hn_url):
    soup = bs(get_html(hn_url),'html.parser')
    return [a['href'] for a in soup.find_all('a',{'class':'titlelink'}) if "ycombinator" not in a['href'] and is_valid_url(a["href"])]


def text_from_html(body):
    soup = bs(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def all_dates(year, month, date, number_of_days=365):
    start_date = datetime.date(year, month, date)
    end_date = start_date + datetime.timedelta(days=number_of_days)
    if (end_date > datetime.date.today()): 
        end_date = datetime.date.today()
    print(end_date)
    delta = datetime.timedelta(days=1)
 
    all_days = list()

    while start_date <= end_date:
        date = start_date.strftime("%Y-%m-%d")
        all_days.append(date)
        start_date += delta
    return all_days

def get_articles_for_date(date):
    page_num = 1
    current_url = f"https://news.ycombinator.com/front?day={date}&p={page_num}"
    current_articles = get_all_articles(current_url)
    articles = []
    while len(current_articles) > 0:
        for a in current_articles:
            articles.append(a)
        page_num += 1
        current_url = f"https://news.ycombinator.com/front?day={date}&p={page_num}"
        print(f"getting articles for {current_url}")
        current_articles = get_all_articles(current_url)
    return articles

def url_to_filename(url):
    return url.replace("/", "{").replace(":","}")

def get_subranges(start_year, start_month, start_day, number_of_days, num_threads=1):
    dates = all_dates(start_year, start_month, start_day, number_of_days=number_of_days)
    return [list(x) for x in np.array_split(dates,num_threads)]

def crawl(dates):
    if not path.isdir('data'):
        mkdir('data')
    for d in dates:
        print(d)
        articles = get_articles_for_date(d)
        dir_name = path.join('data',d)
        print(dir_name)
        if not path.isdir(dir_name):
            print(f"creating {dir_name}")
            mkdir(dir_name)
        for a in articles:
            print(a)
            body = get_html(a)
            if body == None:
                continue
            text = text_from_html(body)
            file_name = path.join(dir_name,url_to_filename(a))
            with open(file_name,'w+') as f:
                f.write(text)

def multiprocess_crawl(start_year, start_month, start_day, number_of_days, num_threads):
    ranges = get_subranges(start_year, start_month, start_day, number_of_days, num_threads)
    processes = []

    for subrange in ranges:
        processes.append(Process(target=crawl, args=(subrange,)))

    for p in processes:
        p.start()

    for p in processes:
        p.join()

if __name__ == "__main__":
    #dates = all_dates(2021,11,1,13)
    #crawl(dates)
    multiprocess_crawl(2021,11,1,13,2)