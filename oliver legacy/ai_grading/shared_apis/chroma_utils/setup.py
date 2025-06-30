from setuptools import setup, find_packages

setup(
    name="chromautils",
    version="0.1",
    packages=find_packages(include=['chroma_utils', 'chroma_utils.*']),
    py_modules=["chroma_utils"],
    install_requires=[
        "chromadb",  
    ],
    author="Haoran Zhu",
    author_email="h287zhu@uwaterloo.ca",
    description="A package for working with ChromaDB utilities."
)
