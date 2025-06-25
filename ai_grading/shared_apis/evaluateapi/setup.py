from setuptools import setup, find_packages

setup(
    name='evaluateapi',
    version='0.1',
    packages=find_packages(include=['evaluateapi', 'evaluateapi.*']),
    install_requires=[
        'requests',
        'python-docx'
    ],
    py_modules=["evaluate_api"],
    description='Evaluate API library',
    author='Mike Cooper-Stachowsky',
    author_email='mstachowsky@gmail.com',
    url='http://example.com',
)
