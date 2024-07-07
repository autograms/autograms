from setuptools import setup, find_packages

setup(
    name='autograms',
    version='0.1.1',
    package_data={'autograms': ['graph_utils/template.html']},
    packages=find_packages(),
    install_requires=[
        "transformers",
        "openai",
        "tiktoken",
        "pandas",
        "numpy",
        "graphviz",
        "setuptools"
    ],
    url='https://github.com/autograms/autograms',
    classifiers=['Programming Language :: Python :: 3'],
    python_requires='>=3.9',

)