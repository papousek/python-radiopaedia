from fma.graph import load_stats, load_graph, load_percentage_of_symmetric_links
import json
import matplotlib.pyplot as plt
import seaborn as sns


def execute(output_dir='output'):
    graph = load_graph()
    stats = load_stats()
    print('There are {} % of symmetric links.'.format(int(round(100 * load_percentage_of_symmetric_links()))))
    for stat in ['degree_in', 'degree_out', 'pagerank']:
        sns.distplot(stats[stat], bins=20, kde=False)
        plt.savefig('{}/{}_hist.svg'.format(output_dir, stat))
        plt.close()
    print(stats.head())
    print(len(graph))
    with open('{}/fma_graph.json'.format(output_dir), 'w') as f:
        json.dump(graph, f, sort_keys=True)
