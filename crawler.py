from ast import literal_eval
from bs4 import BeautifulSoup as bs
from bs4.element import Comment
import calendar
import datetime
import numpy as np
import time
from os import path,mkdir, getcwd
import requests
import tldextract
import validators

from multiprocessing import Process


def get_html(url,number_of_retries_remaining=3):
    try:
        r = requests.get(url, timeout=5)
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

def get_toplevel_domain(url):
    parsed = tldextract.extract(url)
    return parsed.domain + '.' + parsed.suffix

def get_blacklisted_sites(file_name):
    with open(file_name, 'r') as f:
        return set([get_toplevel_domain(x) for x in f.readlines()])

def url_to_filename(url):
    return url.replace("/", "{").replace(":","}")[:254]

def text_from_html(body):
    soup = bs(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def get_stories(limit, end_stamp, start_stamp=None):
    if start_stamp == None:
        url = f"http://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage={limit}&numericFilters=created_at_i<{end_stamp}"
    else:
        url = f"http://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage={limit}&numericFilters=created_at_i<{end_stamp},created_at_i>{start_stamp}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"Failed to get stories for {url} with status code {r.status_code}")
        return None

def all_timestamps(year, month, date, number_of_days=365):
    """
    Gets all the time stamps for the specified interval, where each index in the list represents the timestamp of a new day
    """
    start_date = datetime.date(year, month, date)
    end_date = start_date + datetime.timedelta(days=number_of_days)
    if (end_date > datetime.date.today()): 
        end_date = datetime.date.today()
    delta = datetime.timedelta(days=1)
    all_stamps = list()

    while start_date <= end_date:
        timestamp = calendar.timegm(start_date.timetuple())
        all_stamps.append(timestamp)
        start_date += delta
    return all_stamps

def parse_json(json, blacklisted):
    result = []
    if len(json.keys()) == 0:
        return None
    if json.get('nbHits',0) <= 0:
        return []
    for hit in json.get('hits'):
        if hit['url'] == None or get_toplevel_domain(hit['url']) in blacklisted:
            continue
        result.append((hit['url'],hit['created_at_i']))
    return result

def write_articles(folder, urls):
    for url,_ in urls:
        body = get_html(url)
        if body == None:
            continue
        text = text_from_html(body)
        path_name = path.join(folder,url_to_filename(url))
        print(path_name)
        with open(path_name,'w+') as f:
            f.write(text) 
def write_stories_for_time_interval(start_year,start_month,start_day,num_days=365, blacklist_file='blacklist_sites.txt', limit=250, num_threads = 1):
    blacklisted = get_blacklisted_sites(blacklist_file)
    stamps = all_timestamps(start_year,start_month,start_day,num_days)
    cur_start = stamps[0]
    cur_end = stamps[1]
    if not path.isdir('data'):
        mkdir('data')
    cur_dir = path.join('data',str(cur_start) + "_" + str(cur_end))
    i = 0
    while i < len(stamps) - 1:
        print(i,cur_start, cur_end)
        if not path.isdir(cur_dir):
            mkdir(cur_dir)
        parsed = parse_json(get_stories(limit,cur_end,cur_start),blacklisted)
        if len(parsed) == 0:
            i += 1
            if i < len(stamps) - 1:
                cur_start = stamps[i]
                cur_end = stamps[i+1]
            continue
        min_time = min([p[1] for p in parsed])
        split_articles = np.array_split(parsed,num_threads)
        processes = []
        for i in range(num_threads):
            processes.append(Process(target=write_articles, args=(cur_dir,split_articles[i])))
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        if min_time < 9999999999999999 and min_time > dates[i]:
            cur_end = min_time
            cur_dir = path.join('data',str(cur_start) + "_" + str(cur_end))
        else:
            i += 1
            if i < len(stamps) - 1:
                cur_start = stamps[i]
                cur_end = stamps[i+1]
                cur_dir = path.join('data',str(cur_start) + "_" + str(cur_end))
                min_time = 9999999999999999

if __name__ == "__main__":
    dates = all_timestamps(2021,11,1,13)
    #crawl(dates)
    #multiprocess_crawl(2021,11,12,1,1)
    #print(get_toplevel_domain("https://github.com/rabbibotton/clog"))
    #blacklisted = get_blacklisted_sites('blacklist_sites.txt')
    #timestamp = int(1636929155)
    #json = get_stories(50,timestamp)
    #print(parse_json(json,blacklisted))
    print(write_stories_for_time_interval(2021,11,1,13,limit=500,num_threads=8))
