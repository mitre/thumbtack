import io
import os

from setuptools import setup, find_packages

# Package meta-data.
NAME = 'thumbtack'
DESCRIPTION = 'Service to manage disk image mounts.'
URL = 'https://github.com/mitre/thumbtack'
EMAIL = 'thumbtack@mitre.org'
AUTHOR = 'The MITRE Corporation'
LICENSE = 'Apache 2.0'
REQUIRES_PYTHON = '>=2.7.0'
VERSION = '0.1.4'

REQUIRED = [
    'Flask',
    'Flask-RESTful',
    'gunicorn',
    'imagemounter',
    'requests',
    'pathlib2 ; python_version<"3.4"',
]

doc_requires = [
    'sphinx',
]

test_requires = [
    'coverage',
    'pytest',
    'pytest-cov',
]

dev_requires = doc_requires + test_requires + [
    'bumpversion',
    'python-magic',
    'pytsk3',
]

EXTRAS = {
    'dev': dev_requires,
    'docs': doc_requires,
    'test': test_requires,
}

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
try:
    with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    license=LICENSE,
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Security',
        'Topic :: System :: Filesystems',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    packages=find_packages(exclude=('tests',)),
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'thumbtack = thumbtack:start_app',
        ]
    }
)
