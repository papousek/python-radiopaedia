from fma.ontology import load_ontology
import pandas


def names_list(val):
    if val is None:
        return None
    return '|'.join(val)


def execute(output_dir='output'):
    result = []
    for term, term_data in load_ontology()['terms'].items():
        info_data = term_data['info']
        result.append({
            'FMA': term.replace('http://purl.org/sig/ont/fma/', '').upper(),
            'TA': info_data.get('http://purl.org/sig/ont/fma/TA_ID', [None])[0],
            'RADLEX': info_data.get('http://purl.org/sig/ont/fma/RadLex_ID', [None])[0],
            'english_name': info_data.get('http://purl.org/sig/ont/fma/preferred_name', [None])[0],
            'latin_name': names_list(info_data.get('http://purl.org/sig/ont/fma/non-English_equivalent_Latin', None))
        })
    pandas.DataFrame(result).to_csv('{}/fma_terminology.csv'.format(output_dir), index=False)
