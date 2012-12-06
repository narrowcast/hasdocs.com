Architecture
============

This document describes the architecture and design of HasDocs.


Hosting
-------

Static files are stored in Amazon S3 for relatively reliable and cheap storage.
They are served through a WSGI server such as gunicorn. This is inefficient,
but is done to provide access control to the files. One way to improve the
efficiency would be to use a reverse proxy like nginx.
