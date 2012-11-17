.. HasDocs documentation master file, created by
   sphinx-quickstart on Mon Nov 12 13:35:52 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

HasDocs documentation
===================

HasDocs is Heroku for documentation. This documentation is to share important
design decisions.

.. toctree::
   :maxdepth: 2

Overview
--------

1. User pushes to GitHub or Heroku triggering a post-commit hook.
2. HasDocs pulls the documentation sources from the repository and builds them.
3. HasDocs pushes the built documentation to Amazon S3.
4. Documentations are served from Amazon S3 with appropriate access control.

Connecting with other services
------------------------------

HasDocs can connect to GitHub or Heroku. A post-commit hook is created on GitHub
through its API.

Building the documentation
--------------------------

Builder pulls the documentation and builds them.

Pushing to Amazon S3
--------------------

After the documentation is built, it is uploaded to the Amazon S3.

Reasons for choosing Amazon S3 for hosting the documentation are following:

* It scales. (readthedocs.org is said to serve over 350GB/mongth in Sep 2012)
* It can serve the entire docs without Django.
  This means even if Heroku is down, docs will still be available.

Serving the built docs
----------------------

Documentations are served using `Amazon S3 <http://aws.amazon.com/s3/>`_ website
endpoint. `AWS Identity and Access Management (IAM)
<http://aws.amazon.com/iam/>`_ is used for limiting access to non-public docs.

Looks
-----

Looks do matter. There should be a neutral and simple basic theme as in
Wikipedia's mediawiki. Interested users should be able to implement their own
theme and apply it with ease.

Search
------

Full text search is provided using [blank]. We need to find the best options
for integrating search.

Analytics
---------

Information for measuring which docs are more important and useful should be
provided.

License
-------
Copyright 2012 Narrowcast, Inc.

Credits
-------
* `Read the Docs <http://readthedocs.org/>`_

TODO
----
* :doc:`TODO <todo>`

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`