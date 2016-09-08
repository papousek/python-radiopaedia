from clint.textui import progress
import matplotlib.pyplot as plt
import pandas
import seaborn as sns


def compute_percentage_of_symmetric_links(graph):
    symmetric_links = 0
    all_links = 0
    for node, data in graph.items():
        for node_to in data.get('link-to', []):
            all_links += 1
            if node in graph[node_to].get('link-to', []):
                symmetric_links += 1
    return symmetric_links / all_links


def compute_degrees(graph):
    return pandas.DataFrame([{
        'id': a['id'],
        'degree_in': len(a.get('linked-by', [])),
        'degree_out': len(a.get('link-to', [])),
    } for a in graph.values()])


def compute_stats(graph):
    degrees = compute_degrees(graph)
    pagerank = compute_pagerank(graph)
    result = pandas.merge(degrees, pagerank, how='inner', on='id')
    result['name'] = result['id'].apply(lambda i: graph[i]['name'])
    return result


def compute_pagerank(graph, iterations=100, debug=False, output_dir='output'):
    pagerank = {}
    print('Computing page rank:')
    for i in progress.bar(range(iterations)):
        if debug:
            to_plot = pandas.DataFrame([{'pagerank': pagerank.get(node, 0)} for node in graph.keys()])
            sns.distplot(to_plot['pagerank'], bins=20, kde=False)
            plt.savefig('{}/debug_pagerank_{}_hist.svg'.format(output_dir, i))
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
