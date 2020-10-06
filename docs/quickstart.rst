##########
Quickstart
##########

Installation
************

From the repo
=============

You can pull the code from the repository at URL using pip:

::

    pip install git+https://github.com/svalouch/python-simplezfs#egg=simplezfs


Interfaces
**********
For both ``zfs(8)`` and ``zpool(8)`` there exist two interfaces:

* **cli** calls the ``zfs`` and ``zpool`` binaries in subprocesses
* **native** uses ``libzfs_core`` to achieve the same goals

There exist two functions :func:`~simplezfs.zfs.get_zfs` and :func:`~simplezfs.zpool.get_zpool` that take the
implementation as first argument and return the appropriate implementation. The main documentation about how it works
are in the api documentation for the interface classes :class:`~simplezfs.zfs.ZFS` and :class:`~simplezfs.zpool.ZPool`.

This guide focuses on the ``cli`` variants.

It is not strictly neccessary to get and pass around an instance every time, as the classes hold very little state.
They need to do some initialization however, such as finding the binaries (and thus hitting the local filesystem).

For the rest of the guide, we'll assume that the following has been run and we have a :class:`~simplezfs.zfs.ZFS`
instance in ``zfs``:

.. code-block:: pycon

   >>> from simplezfs import get_zfs
   >>> zfs = get_zfs('cli')
   >>> zfs
   <zfs.zfs_cli.ZFSCli object at 0x7f9f00faa9b0>

As well as a :class:`~simplezfs.zpool.ZPool` instance in ``zpool`` after running the following:

.. code-block:: pycon

   >>> from simplezfs import get_zpool
   >>> zpool = get_zpool('cli')
   >>> zpool
   <zfs.zpool_cli.ZPoolCli object at 0x7f67d5254940>

To be continued

