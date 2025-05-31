from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Leggi requirements.txt
with open(here / 'requirements.txt', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='gestione-finanziaria',
    version='0.1.0',
    description='Sistema CLI per gestione finanziaria e immobiliare personale',
    long_description=(here / 'docs/README.md').read_text(encoding='utf-8') if (here / 'docs/README.md').exists() else '',
    long_description_content_type='text/markdown',
    author='Tuo Nome',
    author_email='tuo@email.com',
    url='https://github.com/tuo-utente/gestione-finanziaria',
    package_dir={'': 'src'},
    packages=find_packages(where="src"),
    python_requires='>=3.8',
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'gestfin=src.cli.main:menu_principale',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console',
        'Topic :: Office/Business :: Financial',
    ],
    keywords='finanza immobiliare cli gestione personale',
)
