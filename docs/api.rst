###
API
###

Enumerations
************

.. autoclass:: simplezfs.types.DatasetType
   :members:

.. autoclass:: simplezfs.types.PropertySource
   :members:

.. autoclass:: simplezfs.types.ZPoolHealth
   :members:

Types
*****

.. autoclass:: simplezfs.types.Dataset
   :members:

.. autoclass:: simplezfs.types.Property
   :members:

Interfaces
**********

ZFS
===

.. autofunction:: simplezfs.zfs.get_zfs

.. autoclass:: simplezfs.ZFS
   :members:

ZPool
=====

.. autofunction:: simplezfs.zpool.get_zpool

.. autoclass:: simplezfs.ZPool
   :members:

Implementations
***************

.. autoclass:: simplezfs.zfs_cli.ZFSCli
   :members:

.. autoclass:: simplezfs.zfs_native.ZFSNative
   :members:

.. autoclass:: simplezfs.zpool_cli.ZPoolCli
   :members:

.. autoclass:: simplezfs.zpool_native.ZPoolNative
   :members:

Validation functions
********************
A set of validation functions exist to validate names and other data. All of them raise a
:class:`simplezfs.exceptions.ValidationError` as a result of a failed validation and return nothing if everything is okay.

.. autofunction:: simplezfs.validation.validate_dataset_name

.. autofunction:: simplezfs.validation.validate_dataset_path

.. autofunction:: simplezfs.validation.validate_native_property_name

.. autofunction:: simplezfs.validation.validate_metadata_property_name

.. autofunction:: simplezfs.validation.validate_pool_name

.. autofunction:: simplezfs.validation.validate_property_value

Exceptions
**********

.. autoexception:: simplezfs.exceptions.ZFSException

.. autoexception:: simplezfs.exceptions.DatasetNotFound

.. autoexception:: simplezfs.exceptions.PermissionError

.. autoexception:: simplezfs.exceptions.PoolNotFound

.. autoexception:: simplezfs.exceptions.PropertyNotFound

.. autoexception:: simplezfs.exceptions.ValidationError
