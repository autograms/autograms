from setuptools import setup, find_packages

setup(
    name='autograms',
    version='0.5.0',
    description='A framework for programming stateful LLM based chatbots.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    package_data={'autograms': ['graph_utils/template.html']},
    packages=find_packages(exclude=['examples', 'examples.*']),
    install_requires=[
        "openai",
        "tiktoken",
        "pandas",
        "numpy",
        "graphviz",
        "setuptools",
        "dill",
    ],
    url='https://github.com/autograms/autograms',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
    ],
    python_requires='>=3.9',
)