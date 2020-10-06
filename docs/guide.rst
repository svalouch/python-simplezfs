#########################
Guide to python-simplezfs
#########################

Overview
********

The interfaces are similar to calling the zfs toolset on the command line. That is, there are not state holding classes
representing filesets or pools, each call must include the entire dataset path or pool name. There is also no way to
collect actions and run them at the end, each action is carried out immediately.

There are, however, two implementations of the functionality, using the ``cli`` tools and another one using the
`libzfs_core` ``native`` library. We'll focus on the ``cli`` version here.

Most of the functions raise a :class:`simplezfs.exceptions.ValidationError` with some helpful text if any of the data
turns out not to be valid. For example, including invalid or reserved strings in the dataset name raises this
exception.

Let's take a look at the two interfaces **ZFS** and **ZPool**...

.. warning:: All of the commands here attempt to modify something in the pool or dataset given as parameters. If run
             with high enough permission (usually ``root``, but there's ``zfs allow`` that can delegate to lower-
             privileged users, too) these commands can and will **delete** data! Always run these against pools, disks
             and datasets that bear no important data! You have been warned.

The ZFS interface
*****************

The :class:`simplezfs.zfs.ZFS` is the interface that corresponds to the ``zfs(8)`` program. It holds very little state,
and it is recommended to get an instance through the function :func:`~simplezfs.zfs.get_zfs`. It selects the desired
implementation and passes the required parameters. At the very least, it requires the ``api``-parameter, which is a
string that selects the actual implementation, either ``cli`` or ``native``.

All our examples use the ``cli`` implementation for simplicity.

.. code-block:: pycon

   >>> from zfs import get_zfs
   >>> zfs = get_zfs('cli')
   >>> zfs
   <zfs.zfs_cli.ZFSCli object at 0x7f9f00faa9b0>

For the remainder of this guide, we're going to assume that the variable ``zfs`` always holds a
:class:`simplezfs.zfs_cli.ZFSCli` object.

Viewing data
============
To get an overview over the interface, we'll dive in and inspect our running system. Information is returned in the
form if :class:`simplezfs.types.Dataset` instances, which is a named tuple containing a set of fields. For simplicity,
we'll output only a few of its fields to not clobber the screen, so don't be alarmed if there seems to be information
missing: we just omitted the boring parts.

Listing datasets
----------------
By default when listing datasets, all of them are returned regardless of their type. That means that it includes

* volumes
* filesets
* snapshots
* bookmars

.. code-block:: pycon

   >>> zfs.list_datasets()
   <Dataset pool/system/root>
   <Dataset pool/system/root@pre-distupgrade>
   <Dataset tank/vol>
   <Dataset tank/vol@test>

This is often unneccessary, and it allows to limit both by ``type`` and by including only datasets that are children
of another, and both at the same time:

.. code-block:: pycon

   >>> zfs.list_datasets(type=DatasetType.SNAPSHOT)
   <Dataset pool/root@pre-distupgrade>
   <Dataset tank/vol@test>
   >>> zfs.list_datasets(parent='pool/system')
   <Dataset pool/root>
   <Dataset pool/root@pre-distupgrade>
   >>> zfs.list_datasets(parent='pool/system', type=DatasetType.SNAPSHOT)
   <Dataset pool/root@pre-distupgrade>

Creating something new
======================

There are functions for creating the four different types of datasets with nice interfaces:

* :func:`~simplezfs.zfs.ZFS.create_fileset` for ordinary filesets, the most commonly used parameter is ``mountpoint``
  for telling it where it should be mounted.
* :func:`~simplezfs.zfs.ZFS.create_volume` creates volumes, or ZVols, this features a parameter ``thin`` for creating
  thin-provisioned or sparse volumes.
* :func:`~simplezfs.zfs.ZFS.create_snapshot` creates a snapshot on a volume or fileset.
* :func:`~simplezfs.zfs.ZFS.create_bookmark` creates a bookmark (on recent versions of ZFS).

These essentially call :func:`~simplezfs.zfs.ZFS.create_dataset`, which can be called directly, but its interface is
not as nice as the special purpose create functions.


Filesets
--------

Creating a fileset requires the dataset path, like this:

.. code-block:: pycon

   >>> zfs.create_fileset('pool/test', mountpoint='/tmp/test')
   <Dataset pool/test>

:todo: add create_dataset

Volumes
-------

Volumes are created similar to filesets, this example creates a thin-provisioned sparse volume:

.. code-block:: pycon

   >>> zfs.create_volume('pool/vol', thin=True)
   <Dataset pool/vol>

:todo: add create_dataset

Snapshots
---------

Snapshots are, like bookmarks, created on an existing fileset or volume, hence the first parameter to the function is
the dataset that is our base, and the second parameter is the name of the snapshot.

.. code-block:: pycon

   >>> zfs.create_snapshot('pool/test', 'pre-distupgrade')
   <Dataset pool/test@pre-distupgrade>

Bookmarks
---------

Like snapshots above, bookmarks are created on an existing fileset or volume.

.. code-block:: pycon

   >>> zfs.create_bookmark('pool/test', 'book-20190723')
   <Dataset pool/test#book-20190723>

Destroying things
=================

After creating some datasets of various kinds and playing around with some of their properties, it's time to clean up.
We'll use the ``destroy_*`` family of methods.

.. warning:: Bear in mind that things happening here are final and cannot be undone. When playing around, always make
             sure not to run this on pools containing important data!

Filesets
--------

Volumes
-------

Snapshots
---------

Bookmarks
---------

Properties
==========

Properties are one of the many cool and useful features of ZFS. They control its behaviour (like ``compression``) or
return information about the internal states (like ``creation`` time).

.. note:: The python library does not validate the names of native properties, as these are subject to change with the
          ZFS version and it would mean that the library needs an update every time a new ZFS version changes some of
          these. Thus, it relies on validating the input for syntax based on the ZFS documentation of the ZFS on Linux
          (ZoL) project and ZFS telling it that it did not like a name.

A word on metadata/user properties
----------------------------------

The API allows to get and set properties, for both ``native`` properties (the ones defined by ZFS, exposing information
or altering how it works) and ``user`` properties that we call **metadata properties** in the API.

When working with metadata properties, you need to supply a ``namespace`` to distinguish it from a native property.
This works by separating the namespace and the property name using a ``:`` character, so a property ``myprop``
in the namespace ``com.company.department`` becomes ``com.company.department:myprop`` in the ZFS property system. This
is done automatically for you if you supply a ``metadata_namespace`` when creating the ZFS instance and can be
overwritten when working with the get and set functions. It is also possible not to define the namespace and passing
it to the functions every time.

When you want to get or set a metadata property, set ``metadata`` to **True** when calling
:func:`~simplezfs.zfs.ZFS.get_property` or :func:`~simplezfs.zfs.ZFS.set_property`. This will cause it to automatically
prepend the namespace given on instantiation or to prepend the one given in the ``overwrite_metadata_namespace`` when
calling the functions. The name of the property **must not** include the namespace, though it may contain ``:``
characters on its own, properties of the form ``zfs:is:cool`` are valid afterall. ``:`` characters are never valid in
the context of native properties, and this is the reason why there is a separate switch to turn on metadata properties
when using these functions.

Error handling
--------------
If a property name is not valid or the value exceeds certain bounds, a :class:`simplezfs.exceptions.ValidationError` is
raised. This includes specifying a namespace in the property name if ``metadata`` is **False**, or exceeding the
length allowed for a metadata property (8192 - 1 bytes).

Though not an error for the ``zfs(8)`` utility, getting a non-existing metadata property also raises the above
exception to indicate that the property does not exist.

Getting a property
------------------

Getting properties is fairly straight-forward, especially for native properties:

.. code-block:: pycon

   >>> zfs.get_property('tank/system/root', 'mountpoint')
   Property(key='mountpoint', value='/', source='local', namespace=None)

For **metadata** properties, one needs to enable their usage by setting ``metadata`` to True. With a globally saved
namespace, it looks like this:

.. code-block:: pycon

   >>> zfs = get_zfs('cli', metadata_namespace='com.company')
   >>> zfs.get_property('tank/system/root', 'do_backup', metdata=True)
   Property(key='do_backup', value='true', source='local', namespace='com.company')

If you don't specify a namespace when calling :func:`~simplezfs.zfs.get_zfs` or if you want to use a different
namespace for one call, specify the desired namespace in ``overwrite_metadata_namespace`` like so:

.. code-block:: pycon

   >>> zfs.get_property('tank/system/root', 'requires', metadata=True, overwrite_metadata_namespace='user')
   Property(key='requires', value='coffee', source='local', namespace='user')

This is the equivalent of calling ``zfs get user:requires tank/system/root`` on the shell.

Asking it to get a native property that does not exist results in an error:

.. code-block:: pycon

   >>> zfs.get_property('tank/system/root', 'notexisting', metadata=False)
   zfs.exceptions.PropertyNotFound: invalid property on dataset tank/test

Setting a property
------------------

The interface for setting both native and metadata properties works exactly like the get interface shown earlier,
though it obviously needs a value to set. We won't go into ZFS delegation system (``zfs allow``) and assume the
following is run using **root** privileges.

.. code-block:: pycon

   >>> zfs.set_property('tank/service/backup', 'mountpoint', ''/backup')

Setting a metadata property works like this (again, like above):

.. code-block:: pycon

   >>> zfs.set_property('tank/system/root', 'requires', 'tea', metadata=True, overwrite_metadata_namespace='user')

Listing properties
------------------

:todo: ``zfs.get_properties``

The ZPool interface
*******************

The :class:`simplezfs.zfs.ZPool` is the interface that corresponds to the ``zpool(8)`` program. It holds very little
state, and it is recommended to get an instance through the function :func:`~simplezfs.zpool.get_zpool`. It selects the
desired implementation and passes the required parameters. At the very least, it requires the ``api``-parameter, which
is a string that selects the actual implementation, either ``cli`` or ``native``.

All our examples use the ``cli`` implementation for simplicity.

.. code-block:: pycon

   >>> from simplezfs import get_zpool
   >>> zpool = get_zpool('cli')
   >>> zpool
   <zfs.zpool_cli.ZPoolCli object at 0x7f67d5254940>

For the remainder of this guide, we're going to assume that the variable ``zpool`` always holds a
:class:`simplezfs.zpool_cli.ZPoolCli` object.

Error handling
**************
We kept the most important part for last: handling errors. The module defines its own hierarchy with
:class:`simplezfs.exceptions.ZFSException` as toplevel exception. Various specific exceptions are based on ot. When
working with :class:`simplezfs.zfs.ZFS`, the three most common ones are:

* :class:`simplezfs.exceptions.ValidationError` which indicates that a name (e.g. dataset name) was invalid.
* :class:`simplezfs.exceptions.DatasetNotFound` is, like FileNotFound in standard python, indicating that the dataset
  the module was instructed to work on (e.g. get/set properties, destroy) was not present.
* :class:`simplezfs.exceptions.PermissionError` is raised when the current users permissions are not sufficient to
  perform the requested operation. While some actions can be delegated using ``zfs allow``, linux, for example, doesn't
  allow non-root users to mount filesystems, which means that a non-root user may create filesets with a valid
  mountpoint property, but it won't be mounted.

Examples
========

.. code-block:: pycon

   >>> zfs.list_dataset(parent=':pool/name/invalid')
   zfs.exceptions.ValidationError: malformed name

.. code-block:: pycon

   >>> zfs.list_datasets(parent='pool/not/existing')
   zfs.exceptions.DatasetNotFound: Dataset "pool/not/existing" not found

