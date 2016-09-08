from .ontology import load_ontology
from clint.textui import progress
from collections import defaultdict
from common.graph import compute_pagerank, compute_degrees, compute_stats, compute_percentage_of_symmetric_links
from spiderpig import spiderpig


@spiderpig()
def load_stats():
    return compute_stats(load_graph())


@spiderpig()
def load_percentage_of_symmetric_links():
    return compute_percentage_of_symmetric_links(load_graph())


@spiderpig()
def load_degrees():
    return compute_degrees(load_graph())


@spiderpig()
def load_pagerank(iterations=100, debug=False, output_dir='output'):
    graph = load_graph()
    return compute_pagerank(graph, iterations=iterations, debug=debug, output_dir=output_dir)


@spiderpig()
def load_graph():
    graph = defaultdict(lambda: defaultdict(list))
    print('Transforming FMA ontology to link graph:')
    for t_id, t_data in progress.bar(load_ontology()['terms'].items()):
        graph[t_id]['id'] = t_id
        graph[t_id]['ta_ids'] = t_data['info']['http://purl.org/sig/ont/fma/TA_ID']
        graph[t_id]['name'] = t_data['info']['http://purl.org/sig/ont/fma/preferred_name']
        for relations in t_data.get('relations', {}).values():
            for relation in relations:
                if not relation.startswith('http://purl.org/sig/ont/fma/'):
                    continue
                graph[t_id]['link-to'].append(relation)
                graph[relation]['linked-by'].append(t_id)
    return {key: {key_inner: value_inner for key_inner, value_inner in value.items()} for key, value in graph.items()}
