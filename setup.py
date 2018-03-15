from setuptools import setup, find_packages

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

setup(
    name='thumbtack',
    version='0.1.0',
    description="Service to manage disk image mounts",
    author='The MITRE Corporation',
    author_email='thumbtack@mitre.org',
    packages=find_packages(),
    install_requires=[
        'apistar',
        'Flask',
        'Flask-RESTful',
        'gunicorn',
        'imagemounter',
        'pathlib2 ; python_version<"3.4"',
    ],
    extras_require={
        'dev': dev_requires,
        'docs': doc_requires,
        'test': test_requires,
    },
)
