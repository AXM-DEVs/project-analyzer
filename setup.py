# setup.py
from setuptools import setup, find_packages

setup(
    name="project-analyzer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "requests>=2.31.0",
        "tree-sitter>=0.20.4",
        "gitpython>=3.1.40",
        "jinja2>=3.1.2",
        "rich>=13.7.0",
        "networkx>=3.2.1",
    ],
    entry_points={
        "console_scripts": [
            "project-analyzer=main:cli",
        ],
    },
    python_requires=">=3.11",
)