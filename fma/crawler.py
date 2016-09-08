from collections import defaultdict
from spiderpig import spiderpig
import os
import os.path
import rdflib
import urllib.request


def load_fma_file(output_dir='output'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filename = '{}/fma.owl'.format(output_dir)
    if not os.path.exists(filename):
        print('Downloading FMA OWL file ...')
        urllib.request.urlretrieve('http://data.bioontology.org/ontologies/FMA/submissions/16/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb', filename)
        print('    DONE')
    return filename


@spiderpig()
def load_raw_rdf():
    print('Loading raw RDF graph ...')
    graph = rdflib.Graph()
    graph.parse(load_fma_file())
    print('    DONE')
    return graph


@spiderpig()
def load_transformed_triples():
    triples = load_raw_triples()
    # drop anonymous inheritance
    an_inh = [t for t in triples if t[1] == 'http://www.w3.org/2000/01/rdf-schema#subClassOf' and t[2].startswith('N')]
    an_class_names = {t[2] for t in an_inh}
    an_class_triples = [t for t in triples if t[0] in an_class_names]
    an_classes = defaultdict(list)
    for t in an_class_triples:
        an_classes[t[0]].append(t)
    properties = defaultdict(list)
    for an_class in an_classes.values():
        if len([t for t in an_class if t[2] == 'http://www.w3.org/2002/07/owl#Restriction']) == 0:
            continue
        property_name = [t[2] for t in an_class if t[1] == 'http://www.w3.org/2002/07/owl#onProperty'][0]
        end_name = [t[2] for t in an_class if t[1] in {'http://www.w3.org/2002/07/owl#someValuesFrom', 'http://www.w3.org/2002/07/owl#hasValue'}][0]
        properties[an_class[0][0]].append(('transformed/{}'.format(property_name), end_name))
    to_remove = set(properties.keys())
    triples = list(set(triples) - {t for t in triples if t[1] == 'http://www.w3.org/2000/01/rdf-schema#subClassOf' and t[2] in to_remove} - {t for t in triples if t[0] in to_remove})
    for start, _, end in an_inh:
        if end in to_remove:
            for property_name, property_value in properties[end]:
                triples.append((start, property_name, property_value))

    # drop axioms
    ax_names = {t[0] for t in triples if t[1] == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' and t[2] == 'http://www.w3.org/2002/07/owl#Axiom'}
    ax_triples = [t for t in triples if t[0] in ax_names]
    axs = defaultdict(list)
    for t in ax_triples:
        axs[t[0]].append(t)
    properties = defaultdict(list)
    for ax in axs.values():
        ta_ids = [t[2] for t in ax if t[1] == 'http://purl.org/sig/ont/fma/TA_ID']
        term = [t[2] for t in ax if t[1] == 'http://www.w3.org/2002/07/owl#annotatedSource'][0]
        property_name = [t[2] for t in ax if t[1] == 'http://www.w3.org/2002/07/owl#annotatedProperty'][0]
        property_value = [t[2] for t in ax if t[1] == 'http://www.w3.org/2002/07/owl#annotatedTarget'][0]
        if len(ta_ids) > 0:
            properties[ax[0][0]].append((term, 'http://purl.org/sig/ont/fma/TA_ID', ta_ids[0]))
        properties[ax[0][0]].append((term, property_name, property_value))
    to_remove = set(properties)
    triples = list(set(triples) - {t for t in triples if t[0] in to_remove})
    for ax_properties in properties.values():
        for start, property_name, property_value in ax_properties:
            triples.append((start, property_name, property_value))

    # drop equivalent classes (useless)
    triples = [t for t in triples if t[1] != 'http://www.w3.org/2002/07/owl#equivalentClass']
    return triples


@spiderpig()
def load_raw_triples():
    return [(str(a), str(b), str(c)) for a, b, c in load_raw_rdf()]
