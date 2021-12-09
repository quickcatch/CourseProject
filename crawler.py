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


def get_html(url,number_of_retries_remaining=3,log=False):
    """Gets raw html of URL

    Args:
        url (str): url of webpage to get html for
        number_of_retries_remaining (int, optional): Number of times to retry get request. Defaults to 3.
        log (bool, optional): whether to log errors or not. Defaults to False.

    Returns:
        str: raw html
    """
    try:
        r = requests.get(url, timeout=5)
        if r.status_code < 200 or r.status_code > 299: # error ocurred
            if r.status_code == 503:
                if number_of_retries_remaining > 0:
                    time.sleep(3)
                    return get_html(url,number_of_retries_remaining - 1)
            if log:
                print(f"Error getting html for {url} with status code {r.status_code}")
            return None 
        return r.text
    except Exception as e:
        if log:
            print(f"Error getting html for {url} due to timeout")


def tag_visible(element):
    """Determines if this tag is a visible text element or not

    Args:
        element (bs4.Element): element to parse

    Returns:
        bool: whether the element is visible or not
    """
    if element.parent.name in ['a','style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def is_valid_url(url):
    """Validates url

    Args:
        url (str): url to validate

    Returns:
        bool: whether url is valid or not
    """    
    return validators.url(url)

def get_toplevel_domain(url):
    """Gets TLD of url

    Args:
        url (str): URL to validate

    Returns:
        bool: whether url is valid or not
    """
    parsed = tldextract.extract(url)
    return parsed.domain + '.' + parsed.suffix

def get_blacklisted_sites(file_name):
    """Gets TLD's of blacklisted site from blacklist file

    Args:
        file_name (str): blacklist file name

    Returns:
        set: set of blacklisted URLs
    """    
    with open(file_name, 'r') as f:
        return set([get_toplevel_domain(x) for x in f.readlines()])

def url_to_filename(url):
    """converts url to filename because files can't have slashes or colons

    Args:
        url (str): url to convert

    Returns:
        str: file name
    """
    return url.replace("/", "{").replace(":","}")[:254]

def text_from_html(body):
    """Gets text from html body

    Args:
        body (str): html

    Returns:
        str: raw text
    """
    soup = bs(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def get_stories(limit, end_stamp, start_stamp=None):
    """Gets story JSON from HackerNews api

    Args:
        limit (int): max number of posts to return
        end_stamp (numeric): timestamp to end at
        start_stamp (numeric, optional): timestamp to start at. Defaults to None.

    Returns:
        dict: story json response
    """
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

def all_timestamps(year, month, day, number_of_days=365):
    """Gets all the time stamps for the specified interval, where each index in the list represents the timestamp of a new day

    Args:
        year (int): start year
        month (int): start month
        day (int): start day
        number_of_days (int, optional): Number of days to get stories for. Defaults to 365.

    Returns:
        list: list of timestamps
    """
    start_date = datetime.date(year, month, day)
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
    """Parses json from HN api and retrieves urls & timestamps

    Args:
        json (dict): json from api
        blacklisted (set): blacklisted TLDs

    Returns:
        list: list of tuples each containing at url and creation timestamp
    """
    result = []
    if json == None or len(json.keys()) == 0:
        return None
    if json.get('nbHits',0) <= 0:
        return []
    for hit in json.get('hits'):
        if hit['url'] == None or get_toplevel_domain(hit['url']) in blacklisted:
            continue
        result.append((hit['url'],hit['created_at_i']))
    return result

def write_articles(folder, urls):
    """Takes list of URLs and writes their text contents to files

    Args:
        folder (str): folder to write files to
        urls (list): list of url's
    """
    for url,_ in urls:
        body = get_html(url)
        if body == None:
            continue
        text = text_from_html(body)
        path_name = path.join(folder,url_to_filename(url))
        with open(path_name,'w+') as f:
            f.write(text) 
    
def write_stories_for_time_interval(start_year,start_month,start_day,num_days=365, blacklist_file='blacklist_sites.txt', limit=250, num_threads = 1):
    """Writes all stories for a specified time interval

    Args:
        start_year (int): start year of time interval
        start_month (int): start month of time interval
        start_day (int): start day of time interval
        num_days (int, optional): Length of time interval. Defaults to 365.
        blacklist_file (str, optional): TLDs to exclude. Defaults to 'blacklist_sites.txt'.
        limit (int, optional): Max number of documents for each day. Defaults to 250.
        num_threads (int, optional): Number of threads to use when fetching URLs. Defaults to 1.
    """
    blacklisted = get_blacklisted_sites(blacklist_file)
    stamps = all_timestamps(start_year,start_month,start_day,num_days)
    cur_start = stamps[0]
    cur_end = stamps[1]
    if not path.isdir('data'):
        mkdir('data')
    cur_dir = path.join('data',str(cur_start) + "_" + str(cur_end))
    i = 0
    while i < len(stamps) - 1:
        if not path.isdir(cur_dir):
            mkdir(cur_dir)
        parsed = parse_json(get_stories(limit,cur_end,cur_start),blacklisted)
        if parsed == None or len(parsed) == 0:
            i += 1
            if i < len(stamps) - 1:
                cur_start = stamps[i]
                cur_end = stamps[i+1]
                cur_dir = path.join('data',str(cur_start) + "_" + str(cur_end))
                min_time = 9999999999999999
            continue
        min_time = min([p[1] for p in parsed])
        split_articles = np.array_split(parsed,num_threads)
        processes = []
        for j in range(num_threads):
            processes.append(Process(target=write_articles, args=(cur_dir,split_articles[j])))
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        if min_time < 9999999999999999 and min_time > cur_start:
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
    print(write_stories_for_time_interval(2021,11,1,13,limit=500,num_threads=16))
