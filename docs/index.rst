Welcome to powermodes's documentation!
======================================

To help develop powermodes, we all make sure our code follows some standards. Before submitting
any pull request, make sure the following two static analyzers report no errors:

.. code:: bash

	$ pylint powermodes
	$ mypy --strict powermodes

To install these tools (if you haven't already), run:

.. code:: bash

	$ pip install pylint mypy

It's in the interest of every developer to learn how errors are dealt with in powermodes
(:mod:`powermodes.error`). Plugin developers should also read (:mod:`powermodes.plugin`).

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
