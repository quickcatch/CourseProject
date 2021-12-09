# HackerNews Chrome Extension

This is an extension built to work with HackerNews.com. When the extension is used, 
it takes the article from the current page you are look at and uses advanced search techniques 
to find 5 articles that of similar interest that you can choose to look at. 

## Library Requirements

In order to run this github, you will need the following libraries installed:
Os, numpy, time, sklearn, joblib, pandas, sys, crawler, nltk, string, tqdm, itertools, 
ast, bs4, calendar, datetime, requests, tldextract, validators, fastAPI.

## Setting up the Extension

### Step 1: Crawler.py

To get the data necessary for the extension to work, we first need to crawl Hackernews.com for data. To do so, you need to run the main function in crawler.py. There is a pre-set in the function, but that can be changed to the date range you desire. It will crawl up to 365 days ahead of the initial date entered. This is the longest step of the whole process, and it will take time to crawl the data.

### Step 2: Clustering.py

After you have crawled the data, the next step is to run the main function in clustering.py. This function takes in three inputs: the folder containing all the data, the word cluster, and the amount of clusters you would like the data to be divided into. An example would be: py clustering.py <directory_holding_files> cluster <#>. This can vary based on user performance needs. After this is done, it will create and store pickle files that will hold all the info necessary for the chrome extension to work.

### Step 3: Setting up the API

From here, we need to set up the FastAPI, which is simple. One needs to go to the terminal they are using and type ``` 
uvicorn api:app --reload  ```
This will begin the process of loading all the data acquired from clustering.py into the file so that the API will work. Eventually a message in the terminal will pop saying that the API is all set, and ready to begin.

### Step 4: Adding the Chrome Extension
Now all we do is add the extension to Chrome. Go to the settings for chrome extensions and enable developer tools. From there, press the button load unpacked. The folder ro unpack is the folder extensions in the github code. Once this is loaded, you are all set and ready to use the extension!

## Using the extension

To use the Extension itself, you just need to click on the extension, and press the button get similar articles. This will take about 30 seconds to work, but when its done a table of 5 article titles and URLS will pop up that you can feel free to look at. From there, you can repeat as many times as you want on any page. Happy Usage!
