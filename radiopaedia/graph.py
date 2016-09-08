from bs4 import BeautifulSoup
from clint.textui import progress
from collections import defaultdict
from radiopaedia.crawler import load_all_articles
from spiderpig import spiderpig
import pandas
import matplotlib.pyplot as plt
import seaborn as sns


@spiderpig()
def load_stats(category):
    graph = load_graph(category)
    degrees = load_degrees(category)
    pagerank = load_pagerank(category)
    result = pandas.merge(degrees, pagerank, how='inner', on='id')
    result['name'] = result['id'].apply(lambda i: graph[i]['name'])
    return result


def load_percentage_of_symmetric_links(category):
    graph = load_graph(category)
    symmetric_links = 0
    all_links = 0
    for node, data in graph.items():
        for node_to in data.get('link-to', []):
            all_links += 1
            if node in graph[node_to].get('link-to', []):
                symmetric_links += 1
    return symmetric_links / all_links


@spiderpig()
def load_degrees(category):
    graph = load_graph()
    return pandas.DataFrame([{
        'id': a['id'],
        'degree_in': len(a.get('linked-by', [])),
        'degree_out': len(a.get('link-to', [])),
    } for a in graph.values()])


@spiderpig()
def load_pagerank(category, iterations=100, debug=False, output='output'):
    graph = load_graph(category)
    pagerank = {}
    print('Computing page rank:')
    for i in progress.bar(range(iterations)):
        if debug:
            to_plot = pandas.DataFrame([{'pagerank': pagerank.get(node, 0)} for node in graph.keys()])
            sns.distplot(to_plot['pagerank'], bins=20, kde=False)
            plt.savefig('{}/debug_pagerank_{}_hist.svg'.format(output, i))
            plt.close()
        new_pagerank = {}
        for node, data in graph.items():
            if 'link-to' not in data:
                continue
            to_propagate = pagerank.get(node, 1) / len(data['link-to'])
            for node_to in data['link-to']:
                old_pagerank = new_pagerank.get(node_to, 0)
                new_pagerank[node_to] = old_pagerank + to_propagate
        pagerank.update(new_pagerank)
    max_pagerank = max(pagerank.values())
    result = []
    for node, data in graph.items():
        result.append({
            'id': node,
            'pagerank': pagerank.get(node, 0) / max(max_pagerank, 0.00001),
        })
    return pandas.DataFrame(result)


@spiderpig()
def load_graph(category):
    graph = defaultdict(lambda: defaultdict(list))
    articles = load_all_articles(category=category)
    print('Transforming radiopaedia articles to link graph:')
    for article_id, article in progress.bar(articles.items()):
        soup = BeautifulSoup(article['body'], 'html.parser')
        for a in soup.find_all('a'):
            if a.get('href') is None:
                continue
            if a.get('href').startswith('/articles'):
                found = articles.get(a.get('href').split('/')[-1])
                if found is not None:
                    graph[article_id]['link-to'].append(found['id'])
                    graph[found['id']]['linked-by'].append(article_id)
        graph[article_id]['name'] = article['name']
        graph[article_id]['id'] = article['id']
        graph[article_id]['description'] = article['description'].strip('\n')
        graph[article_id]['html'] = article['body']
    return {key: {key_inner: value_inner for key_inner, value_inner in value.items()} for key, value in graph.items()}
