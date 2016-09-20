from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import quote
from spiderpig import spiderpig
from collections import defaultdict
import pandas
from clint.textui import progress
from more_itertools import unique_everseen


@spiderpig()
def load_translation(latin=False):
    main_soup = _load_mainpage(latin=latin)
    result = []
    main_rows = main_soup.find_all('tr')
    print('Downloading TA data ...')
    for row_id, row in progress.bar(enumerate(main_rows), expected_size=len(main_rows)):
        if row_id == 0:
            continue
        cols = row.find_all('td')
        link_element = cols[2].find('a')
        if link_element is None:
            continue
        link = link_element.get('href')
        metadata = _load_term_metadata(link)
        result.append(metadata)
    return pandas.DataFrame(result)


@spiderpig()
def _load_term_metadata(path):
    term_soup = _load_termpage(path)
    sections_by_title = defaultdict(list)
    previous_title = None
    for table in term_soup.find_all('table'):
        if table.get('class') is None:
            continue
        if table.get('class')[0] == 'SectionTitle':
            previous_title = table.text.strip()
        elif table.get('class')[0] == 'SectionContent':
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue
                sections_by_title[previous_title].append((cols[0].text.strip(), cols[1].text.strip()))
    identification = dict(sections_by_title['Identification'])
    language = dict(sections_by_title['Language'])
    result = {
        'TA': identification['TA code'],
        'FMA': identification.get('FMA identifier'),
        'type': identification['Type of entity'],
        'ID': identification['Entity ID number'],
        'latin': language.get('TA98 Latin preferred term'),
        'english': language.get('TA98 English equivalent'),
    }
    ta_hiearchy = list(unique_everseen([ta for ta, _ in sections_by_title['TA98 Hierarchy'] if ta.startswith('A')]))
    if len(ta_hiearchy) > 1:
        result['TA_parent'] = ta_hiearchy[ta_hiearchy.index(result['TA']) - 1]
    if 'FMA Taxonomy' in sections_by_title:
        fma_hiearchy = [fma for fma, _ in sections_by_title['FMA Taxonomy'] if fma.startswith('FMA')]
        result['FMA_parent'] = fma_hiearchy[fma_hiearchy.index(result['FMA']) - 1]
    return result


def _load_termpage(path):
    URL_BASE = 'http://www.unifr.ch/ifaa/Public/EntryPage/TA98%20Tree/Alpha/'
    return BeautifulSoup(_load_page_content(URL_BASE + quote(path)), 'html.parser')


def _load_mainpage(latin=False):
    URL = 'http://www.unifr.ch/ifaa/Public/EntryPage/TA98%20Tree/Alpha/All%20KWIC%20{}.htm'
    return BeautifulSoup(_load_page_content(URL.format('G%20LA' if latin else 'EN')), 'html.parser')


@spiderpig()
def _load_page_content(url):
    return urlopen(url).read()
