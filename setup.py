from setuptools import setup, find_packages

setup(
    name='autograms',
    version='0.1.0',
    package_data={'autograms': ['graph_utils/template.html']},
    packages=find_packages(),
    install_requires=[
        "transformers",
        "openai==0.27.3",
        "tiktoken",
        "pandas",
        "numpy",
        "graphviz"
    ],
)