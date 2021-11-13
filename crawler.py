from bs4 import BeautifulSoup as bs
import requests
from bs4.element import Comment
import datetime

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

def get_html(url):
    r = requests.get(url)
    if r.status_code < 200 or r.status_code > 299: # error ocurred
        return None 
    return r.text

def tag_visible(element):
    if element.parent.name in ['a','style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def get_all_articles(hn_url):
    soup = bs(get_html(hn_url),'html.parser')
    return [a['href'] for a in soup.find_all('a',{'class':'titlelink'})]


def text_from_html(body):
    soup = bs(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def all_dates(year, month, date):
    start_date = datetime.date(year, month, date)
    end_date = datetime.date(year+1, month, date)
    if (end_date > datetime.date.today()): 
        end_date = datetime.date.today()
    print(end_date)
    delta = datetime.timedelta(days=1)

    all_days = list()

    while start_date <= end_date:
    	date = start_date.strftime("%m%d%Y")
    	all_days.append(date)
    	start_date += delta
    return all_days
