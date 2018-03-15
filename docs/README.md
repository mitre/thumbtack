# Thumbtack Docs Instructions

In order to build the documentation you have a pre-requisite and two options.

Once you have the pre-reqs installed, you can build the docs in one of two ways.

## Pre-requisite
The pre-requisite is you need to install `invoke`, `sphinx`, and `sphinx_rtd_theme`.
(included in the `requirements.txt`).

```bash
pip install -r requirements.txt
```

## Build docs

```bash
# option #1 - uses invoke library (http://www.pyinvoke.org)
invoke docs

# option #2
cd docs
make html
```

## Read the Built Docs
Take a look at `docs/_build/html/index.html`. Voilà!
