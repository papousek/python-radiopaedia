from bs4 import BeautifulSoup
from clint.textui import progress
from collections import defaultdict
from common.graph import compute_pagerank, compute_degrees, compute_stats, compute_percentage_of_symmetric_links
from radiopaedia.crawler import load_all_articles
from spiderpig import spiderpig


@spiderpig()
def load_stats(category):
    return compute_stats(load_graph(category))


@spiderpig()
def load_percentage_of_symmetric_links(category):
    return compute_percentage_of_symmetric_links(load_graph(category))


@spiderpig()
def load_degrees(category):
    return compute_degrees(load_graph(category))


@spiderpig()
def load_pagerank(category, iterations=100, debug=False, output_dir='output'):
    graph = load_graph(category)
    return compute_pagerank(graph, iterations=iterations, debug=debug, output_dir=output_dir)


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
