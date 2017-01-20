from fma.ontology import load_terminology


def execute(output_dir='output'):
    load_terminology().to_csv('{}/fma_terminology.csv'.format(output_dir), index=False)
