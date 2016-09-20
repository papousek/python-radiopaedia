from unifr.crawler import load_translation
import os.path
from spiderpig.msg import info


def execute(output_dir='output'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    load_translation(latin=True).to_csv('{}/terminologia_anatomica.csv'.format(output_dir), index=False)
    info('{}/terminologia_anatomica.csv'.format(output_dir))
