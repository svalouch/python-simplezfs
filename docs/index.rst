##############################
Python-SimpleZFS documentation
##############################

The module implements a simple and straight-forward (hopefully) API for interacting with ZFS. It consists of two main
classes :class:`~simplezfs.zfs.ZFS` and :class:`~simplezfs.zpool.ZPool` that can be thought of as wrappers around the
ZFS command line utilities ``zfs(8)`` and ``zpool(8)``. This module provides two implementations:

* The ``cli``-API wrapps the command line utilities
* And the ``native``-API uses ``libzfs_core``.

At the time of writing, the ``native``-API has not been implemented.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   security
   pe_helper
   guide
   configuration
   properties_metadata
   testing
   api
   CHANGELOG

