var backendUrl = "gjfdklsgjlfdkg";

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

function createGetUrl(baseUrl, values) {
    var url = baseUrl;
    var numParams = 0;
    for (const [key, value] of Object.entries(values)) {
        if(numParams > 0) {
            url += "&" + key + "=" + value;
        }
        else {
            url  += "?" + key + "=" + value;
        }
        numParams += 1;
      }
    return url;
}

function sendGet(url) {
    //values is a dict
    var req = new XMLHttpRequest();
    req.open("GET", url, true);
    req.setRequestHeader('Content-Type', 'application/json');
    req.onreadystatechange = function()
    {
        if(req.readyState == 4 && req.status == 200) {
            return req.responseText
        }
    }
    req.send(null);
    return null;
}

function updateTable(results) {
    //results is an array of arrays where each element is of the form [post title, url]
    for(var i = 1; i <= 5; i++) {
        setValue('result${i}-url', results[i][0]);
        setValue('result${i}-title', results[i][1]);
    }
}

function getRelatedArticles(url) {
    var getUrl = createGetUrl(backendUrl,{"articleUrl":url});
    var results = sendGet(getUrl);
    updateTable(results)
    toggleElement('results');
}

function setValue(id,value) {
    var e = document.getElementById(id);
    e.innerHTML = value;
    e.value = value;
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
        alert(url);
        setValue('result1-title',"fart");
        getRelatedArticles(url);
    }
    else {
        alert("not an article lol");
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
