from collections import defaultdict
from spiderpig import spiderpig
import os
import os.path
import rdflib
import urllib.request
from clint.textui import progress


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
    an_inh_triples = get_triples(
        triples,
        relation='http://www.w3.org/2000/01/rdf-schema#subClassOf',
        predicate=lambda t: is_id_anonymous(t[2])
    )
    an_inh_classes = group_triples_by_start(
        get_triples(triples, start=set(get_ends(an_inh_triples)))
    )
    an_all_classes = group_triples_by_start(
        get_triples(
            triples,
            predicate=lambda t: is_id_anonymous(t[0])
        )
    )
    inh_properties = defaultdict(list)
    to_remove = set()

    def _find_nested_properties(an_class):
        class_name = [t[2] for t in an_class if t[1] in {'http://www.w3.org/2002/07/owl#someValuesFrom', 'http://www.w3.org/2002/07/owl#hasValue'}][0]
        nested_class_name = [t for t in an_all_classes[class_name] if t[1] != 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'][0][2]
        nested_class = an_all_classes[nested_class_name]
        result = []
        related = None
        while len(nested_class) > 0:
            to_remove.add(nested_class[0][0])
            current = get_triples(triples, start=get_triples(nested_class, relation='http://www.w3.org/1999/02/22-rdf-syntax-ns#first')[0][2])
            property_name = get_triples(current, relation='http://www.w3.org/2002/07/owl#onProperty')[0][2]
            property_value = get_triples(current, relation={'http://www.w3.org/2002/07/owl#someValuesFrom', 'http://www.w3.org/2002/07/owl#hasValue'})[0][2]
            if property_name == 'http://purl.org/sig/ont/fma/related_object':
                if related is not None:
                    raise Exception('Expected only one related object!')
                related = property_value
            else:
                result.append((property_name, property_value))
            nested_class = get_triples(triples, start=get_triples(nested_class, relation='http://www.w3.org/1999/02/22-rdf-syntax-ns#rest')[0][2])
        return result, related

    print('Removing anonymous classes:')
    for an_class in progress.bar(an_inh_classes.values()):
        if len(get_triples(an_class, end='http://www.w3.org/2002/07/owl#Restriction')) == 0:
            continue
        property_name = get_triples(an_class, relation='http://www.w3.org/2002/07/owl#onProperty')[0][2]
        if property_name == 'http://purl.org/sig/ont/fma/muscle_attachment':
            nested_properties, related_object = _find_nested_properties(an_class)
            for p_name, p_value in nested_properties:
                if p_name not in ['http://purl.org/sig/ont/fma/has_insertion', 'http://purl.org/sig/ont/fma/has_origin']:
                    continue
                inh_properties[an_class[0][0]].append(('transformed/{}'.format(p_name), p_value))
            continue
        if property_name == 'http://purl.org/sig/ont/fma/attributed_part':
            continue
        end_name = get_triples(an_class, relation={'http://www.w3.org/2002/07/owl#someValuesFrom', 'http://www.w3.org/2002/07/owl#hasValue'})[0][2]
        inh_properties[an_class[0][0]].append(('transformed/{}'.format(property_name), end_name))
    to_remove |= set(inh_properties.keys())
    triples = list(
        set(triples)
        -
        set(get_triples(triples, relation='http://www.w3.org/2000/01/rdf-schema#subClassOf', predicate=lambda t: t[2] in to_remove))
        -
        set(get_triples(triples, predicate=lambda t: t[0] in to_remove))
    )
    for start, relation, end in an_inh_triples:
        if end in to_remove:
            for property_name, property_value in inh_properties[end]:
                triples.append((start, property_name, property_value))

    # removing some relation which are not handled
    NOT_HANDLED_RELATIONS = {
        'transformed/http://purl.org/sig/ont/fma/anatomical_coordinate',
        'transformed/http://purl.org/sig/ont/fma/attributed_constitutional_part',
        'transformed/http://purl.org/sig/ont/fma/attributed_development',
        'transformed/http://purl.org/sig/ont/fma/attributed_regional_part',
        'transformed/http://purl.org/sig/ont/fma/developmental_fusion',
        'transformed/http://purl.org/sig/ont/fma/orientation',
        'transformed/http://purl.org/sig/ont/fma/partition',
    }
    triples = get_triples(triples, predicate=lambda t: t[1] not in NOT_HANDLED_RELATIONS)

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


def is_id_anonymous(id):
    return len(id) == 33 and id.startswith('N')


def get_starts(triples):
    return _get_index(triples, 0)


def get_relations(triples):
    return _get_index(triples, 1)


def get_ends(triples):
    return _get_index(triples, 2)


def group_triples_by_start(triples):
    return _group_triples(triples, 0)


def group_triples_by_relation(triples):
    return _group_triples(triples, 1)


def group_triples_by_end(triples):
    return _group_triples(triples, 2)


def get_triples(triples, start=None, relation=None, end=None, predicate=None):
    if start is not None:
        if not isinstance(start, list) and not isinstance(start, set):
            triples = [t for t in triples if t[0] == start]
        else:
            triples = [t for t in triples if t[0] in start]
    if relation is not None:
        if not isinstance(relation, list) and not isinstance(relation, set):
            triples = [t for t in triples if t[1] == relation]
        else:
            triples = [t for t in triples if t[1] in relation]
    if end is not None:
        if not isinstance(end, list) and not isinstance(end, set):
            triples = [t for t in triples if t[2] == end]
        else:
            triples = [t for t in triples if t[2] in end]
    if predicate is not None:
        triples = [t for t in triples if predicate(t)]
    return triples


def _get_index(triples, index):
    return list({t[index] for t in triples})


def _group_triples(triples, index):
    result = defaultdict(list)
    for t in triples:
        result[t[index]].append(t)
    return {key: values for key, values in result.items()}
