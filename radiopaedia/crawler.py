from urllib.request import urlopen
from bs4 import BeautifulSoup
from clint.textui import progress
from spiderpig import spiderpig


@spiderpig()
def load_all_articles(category='all'):
    return _load_all_articles('http://radiopaedia.org/encyclopaedia/{}/all'.format(category))


def _load_all_articles(start_url):
    homepage = _load_soup(start_url)
    last_page_number = int(homepage.find('div', {'id': 'pager'}).find_all('a')[-2].text)
    result = {}
    print('Loading articles from radiopaedia ({}):'.format(start_url))
    for page_number in progress.bar(range(last_page_number)):
        url = start_url + '?page={}'.format(page_number + 1)
        search_page = _load_soup(url)
        for link in search_page.find_all('a', {'class': 'search-result-article'}):
            article_url = 'http://radiopaedia.org' + link.get('href')
            article_name = link.find('h4', {'class': 'search-result-title-text'}).text
            article_description = link.find('div', {'class': 'search-result-body'}).text
            article_body = _load_article_body(article_url)
            article_id = article_url.split('/')[-1]
            result[article_id] = {
                'url': article_url,
                'name': article_name,
                'description': article_description,
                'body': str(article_body),
                'id': article_id,
            }
    return result


@spiderpig()
def _load_article_body(url):
    return _load_soup(url).find('div', {'id': 'content'}).prettify()


@spiderpig()
def _load_page_content(url):
    return urlopen(url).read()


def _load_soup(url):
    return BeautifulSoup(_load_page_content(url), 'html.parser')
