var backendUrl = "http://127.0.0.1:8000/classify/";

function getCurUrl(tabs) {
    return tabs[0].url;
}

function isArticle(url) {
    return /^.*https:\/\/news\.ycombinator\.com\/item\?id=[0-9]+.*$/.test(url);
}

function toggleElement(id) {
    var e = document.getElementById(id);
    if(e.style.display == 'none')
       e.style.display = 'block';
    else
       e.style.display = 'none';
}


function sendGet(url) {
    //values is a dict
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", url, false ); // false for synchronous request
    xmlHttp.send( null );
    return xmlHttp.responseText;
}

function updateTable(results) {
    //results is an array of arrays where each element is of the form [post title, url]
    alert(JSON.stringify(results));
    for(var i = 0; i < 5; i++) {
        setValue('result' + (i+1) + '-url', results['docs'][i],results['docs'][i]);
        setValue('result' + (i+1) + '-title', results['titles'][i]);
    }
}

function getRelatedArticles(url) {
    var getUrl = backendUrl + encodeURIComponent(url);
    var results = JSON.parse(sendGet(getUrl));
    updateTable(results)
    toggleElement('results');
}

function setValue(id,value,href=null) {
    var e = document.getElementById(id);
    if(href != null)
        e.href = href;
    e.innerHTML = value;
}

function handleClick() {
    let currentUrl = window.location.toString();
    var randomColor = Math.floor(Math.random()*16777215).toString(16);
    document.body.style.backgroundColor = '#' + randomColor;
    var query = { active: true, lastFocusedWindow : true};
    var curUrl = chrome.tabs.query(query, function(tabs){
      var url = getCurUrl(tabs);
      getRelated(url);
    });
}


function getRelated(url){
    if (isArticle(url)) {
        getRelatedArticles(url);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    var button = document.getElementById('getRelated');
    // onClick's logic below:
    button.addEventListener('click', function() {
        handleClick();
    });
    toggleElement('results');
});
