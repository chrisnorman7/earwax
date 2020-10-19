Installation
============

Installing Using pip
====================

It is recommended that you install Earwax using pip::

    pip install Earwax

Install Using Git
=================

Alternatively, you could install using git::

    git clone https://github.com/chrisnorman7/earwax.git
    cd earwax
    python setup.py

Running Test
============

To run the tests, you will need to install `pytest <https://pytest.org/>`_::

    pip install pytest

Then to run the tests::

    py.test

While the tests run, many windows will appear and disappear. That is completely normal, I just use lots of Pyglet for testing.

Building Documentation
======================

You can always find the most up to date version of the docs on `Read the Docs <https://earwax.readthedocs.io/en/latest/>`_, but you can also build them yourself::

    pip install -Ur docs/requirements.txt
    python setup.py build_sphinx
