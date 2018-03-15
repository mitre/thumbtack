import os

from invoke import task

PROJ_ROOT = os.path.abspath(os.path.dirname(__file__))


@task
def clean(c):
    """Clean the local project documentation"""

    with c.cd(os.path.join(PROJ_ROOT, 'docs')):
        c.run('make clean')


@task(clean)
def docs(c):
    """Build the project documentation using Sphinx."""

    with c.cd(os.path.join(PROJ_ROOT, 'docs')):
        c.run('make html')
