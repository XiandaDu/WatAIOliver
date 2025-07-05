from setuptools import setup, find_packages

setup(
    name='extractapi',
    version='0.1',
    packages=find_packages(include=['extractapi', 'extractapi.*']),
    install_requires=[
        'PyMuPDF',        # fitz is part of PyMuPDF
        'PyPDF2',
        'pdf2image',
        'Pillow',         # PIL is now maintained as Pillow
        'python-docx'
    ],
    py_modules=["extract_api"],
    description='Extract API library',
    author='Mike Cooper-Stachowsky',
    author_email='mstachowsky@gmail.com',
    url='http://example.com',
)
