Requirements
============

This document describes the requirements of HasDocs.

Documentation Generation
------------------------
Users should be able to build the documentation for a repository simply by
importing the repository from GItHub. It needs to be rebuilt whenever a change
is code has occured.

Documentation Hosting
---------------------
Documentation should be hosted in reliable storage. It needs to provide
reasonable latency of under 500ms.

Access Control
--------------

Access control to the private GitHub projects must be provided. The
organizations and the teams at GitHub must be honored.

Documentation Generator Support
-------------------------------

The following documentation generators need to be supported:

* Sphinx
* Jekyll

Custom domain names
-------------------

Linking from custom domain names should be supported.
