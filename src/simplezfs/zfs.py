
'''
ZFS frontend API
'''

import logging
from typing import Dict, List, Optional, Union

from .exceptions import (
    DatasetNotFound,
    PermissionError,
    PoolNotFound,
    PropertyNotFound,
    ValidationError,
)
from .pe_helper import PEHelperBase
from .types import Dataset, DatasetType, Property
from .validation import (
    validate_dataset_path,
    validate_metadata_property_name,
    validate_native_property_name,
    validate_pool_name,
    validate_property_value,
)

log = logging.getLogger('simplezfs.zfs')


class ZFS:
    '''
    ZFS interface class. This API generally covers only the zfs(8) tool, for zpool(8) please see
    :class:`~simplezfs.zpool.ZPool`.

    **ZFS implementation**

    There are two ways how the API actually communicates with the ZFS filesystem:

    * Using the CLI tools (:class:`~simplezfs.zfs_cli.ZFSCli`)
    * Using the native API (:class:`~simplezfs.zfs_native.ZFSNative`)

    You can select the API by either creating an instance of one of them or using :func:`~simplezfs.zfs.get_zfs`.


    **Properties and Metadata**

    The functions :func:`~simplezfs.zfs.ZFS.set_property`, :func:`~simplezfs.zfs.ZFS.get_property` and
    :func:`~simplezfs.zfs.ZFS.get_properties` wrap the ZFS get/set functionality. To support so-called
    `user properties`, which are called `metadata` in this API, a default namespace can be stored using
    `metadata_namespace` when instantiating the interface or by calling
    :func:`~simplezfs.zfs.ZFS.set_metadata_namespace` at any time.

    :note: Not setting a metadata namespace means that one can't set or get metadata properties, unless the overwrite
        parameter for the get/set functions is used.

    The parameter ``use_pe_helper`` is used to control whether the ``pe_helper`` will be used when performing actions
    that require elevated permissions. It can be changed at anytime using the ``use_pe_helper`` property.

    :param metadata_namespace: Default namespace
    :param pe_helper: Privilege escalation (PE) helper to use for actions that require elevated privileges (root).
    :param use_pe_helper: Whether to use the PE helper for creating and (u)mounting.
    :param kwargs: Extra arguments, ignored
    '''
    def __init__(self, *, metadata_namespace: Optional[str] = None, pe_helper: Optional[PEHelperBase] = None,
                 use_pe_helper: bool = False, **kwargs) -> None:
        self.metadata_namespace = metadata_namespace
        self.pe_helper = pe_helper
        self.use_pe_helper = use_pe_helper

    def __repr__(self) -> str:
        return f'<ZFS(pe_helper="{self._pe_helper}", use_pe_helper="{self._use_pe_helper}")>'

    @property
    def metadata_namespace(self) -> Optional[str]:
        '''
        Returns the metadata namespace, which may be None if not set.
        '''
        return self._metadata_namespace

    @metadata_namespace.setter
    def metadata_namespace(self, namespace: str) -> None:
        '''
        Sets a new metadata namespace

        :todo: validate!
        '''
        self._metadata_namespace = namespace

    @property
    def pe_helper(self) -> Optional[PEHelperBase]:
        '''
        Returns the pe_helper, which may be None if not set.
        '''
        return self._pe_helper

    @pe_helper.setter
    def pe_helper(self, helper: Optional[PEHelperBase]) -> None:
        '''
        Sets the privilege escalation (PE) helper. Supply ``None`` to unset it.

        :raises FileNotFoundError: if the script can't be found or is not executable.
        '''
        if helper is None:
            log.debug('PE helper is None')
        self._pe_helper = helper

    @property
    def use_pe_helper(self) -> bool:
        '''
        Returns whether the privilege escalation (PE) helper should be used. If the helper has not been set, this
        property evaluates to ``False``.
        '''
        return self._pe_helper is not None and self._use_pe_helper

    @use_pe_helper.setter
    def use_pe_helper(self, use: bool) -> None:
        '''
        Enable or disable using the privilege escalation (PE) helper.
        '''
        self._use_pe_helper = use

    def dataset_exists(self, name: str) -> bool:
        '''
        Checks is a dataset exists. This is done by querying for its `type` property.

        :param name: Name of the dataset to check for.
        :return: Whether the dataset exists.
        '''
        try:
            return self.get_property(name, 'type') is not None
        except (DatasetNotFound, PermissionError, PoolNotFound):
            return False
        except PropertyNotFound:
            return True
        return False

    def get_dataset_info(self, name: str) -> Dataset:
        '''
        Returns basic information about a dataset. To retrieve its properties, see :func:`~ZFS.get_property` and
        :func:`~ZFS.get_properties`.

        :param name: The name of the dataset in question.
        :returns: The dataset info.
        :raises DatasetNotFound: If the dataset does not exist.
        :raises ValidationError: If the name was invalid.
        '''
        raise NotImplementedError(f'{self} has not implemented this function')

    def list_datasets(self, *, parent: Union[str, Dataset] = None) -> List[Dataset]:
        '''
        Lists all datasets known to the system. If ``parent`` is set to a pool or dataset name (or a
        :class:`~zfs.types.Dataset`), lists all the children of that dataset.

        :param parent: If set, list all child datasets.
        :return: The list of datasets.
        '''
        raise NotImplementedError(f'{self} has not implemented this function')

    def set_mountpoint(self, fileset: str, mountpoint: str, *, use_pe_helper: Optional[bool] = None) -> None:
        '''
        Sets or changes the mountpoint property of a fileset. While this can be achieved using the generic function
        :func:`~ZFS.set_property`, it allows for using the privilege escalation (PE) helper if so desired.

        The argument ``use_pe_helper`` can overwrite the property of the same name. If the argument is None, the
        properties value will be assumed. In any case, the function attempts to set the property on its own first. If
        that fails, it evaluates if the PE helper should be used, and will error out if it should be used but has not
        been set. If the helper fails, a :class:`~simplezfs.exceptions.PEHelperException` is raised.

        :param fileset: The fileset to modify.
        :param mountpoint: The new value for the ``mountpoint`` property.
        :param use_pe_helper: Overwrite the default for using the privilege escalation (PE) helper for this task.
            ``None`` (default) uses the default setting. If the helper is not set, it is not used.
        :raises DatasetNotFound: if the fileset could not be found.
        :raises ValidationError: if validating the parameters failed.
        '''
        ds_type = self.get_property(fileset, 'type')
        if ds_type != 'filesystem':
            raise ValidationError(f'Dataset is not a filesystem and can\'t have its mountpoint set')

        try:
            self.set_property(fileset, 'mountpoint', mountpoint)
        except PermissionError as exc:
            if self.pe_helper is not None:
                real_use_pe_helper = use_pe_helper if use_pe_helper is not None else self.use_pe_helper

                if real_use_pe_helper:
                    log.info(f'Permission error when setting mountpoint for "{fileset}", retrying using PE helper')
                    self.pe_helper.zfs_set_mountpoint(fileset, mountpoint)
                else:
                    log.error(f'Permission error when setting mountpoint for "{fileset}" and not using PE helper')
                    raise exc
            else:
                log.error(f'Permission error when setting mountpoint for "{fileset}" and PE helper is not set')

    def set_property(self, dataset: str, key: str, value: str, *, metadata: bool = False,
                     overwrite_metadata_namespace: Optional[str] = None) -> None:
        '''
        Sets the ``value`` of the native property ``key``. By default, only native properties can be set. If
        ``metadata`` is set to **True**, the default metadata namespace is prepended or the one in
        ``overwrite_metadata_namespace`` is used if set to a valid string.

        .. note::

           Use :func:`set_mountpoint` to change the ``mountpoint`` property if your setup requires the use of elevated
           permissions (such as Linux).

        Example:

        >>> z = ZFSCli(namespace='foo')
        >>> z.set_property('tank/test', 'testprop', 'testval', metadata=True, overwrite_metadata_namespace='bar')
        >>> z.get_property('tank/test', 'testprop')
        Exception
        >>> z.get_property('tank/test', 'testprop', metadata=True)
        Exception
        >>> z.get_property('tank/test', 'testprop', metadata=True, overwrite_metadata_namespace='bar')
        Property(key='testprop', val='testval', source='local', namespace='bar')

        :param dataset: Name of the dataset to set the property. Expects the full path beginning with the pool name.
        :param key: Name of the property to set. For non-native properties, set ``metadata`` to **True** and overwrite
            the default namespace using ``overwrite_metadata_namespace`` if required.
        :param value: The new value to set.
        :param metadata: If **True**, prepend the namespace to set a user (non-native) property.
        :param overwrite_metadata_namespace: Overwrite the default metadata namespace for user (non-native) properties
        :raises DatasetNotFound: If the dataset could not be found.
        :raises ValidationError: If validating the parameters failed.
        '''
        if key.strip() == 'all' and not metadata:
            raise ValidationError('"all" is not a valid property name')
        if '/' not in dataset:
            validate_pool_name(dataset)
        else:
            validate_dataset_path(dataset)
        if metadata:
            if overwrite_metadata_namespace:
                prop_name = f'{overwrite_metadata_namespace}:{key}'
            elif self.metadata_namespace:
                prop_name = f'{self.metadata_namespace}:{key}'
            else:
                raise ValidationError('no metadata namespace set')
            validate_metadata_property_name(prop_name)
        else:
            validate_native_property_name(key)
            prop_name = key
        validate_property_value(value)
        self._set_property(dataset, prop_name, value, metadata)

    def _set_property(self, dataset: str, key: str, value: str, is_metadata: bool) -> None:
        '''
        Actual implementation of the set_property function. This is to be implemented by the specific APIs. It is
        called by set_property, which has done all the validation and thus the parameters can be trusted to be valid.

        :param dataset: Name of the dataset to set the property. Expects the full path beginning with the pool name.
        :param key: Name of the property to set. For non-native properties, set ``metadata`` to **True** and overwrite
            the default namespace using ``overwrite_metadata_namespace`` if required.
        :param value: The new value to set.
        :param is_metadata: Indicates we're dealing with a metadata property.
        :raises DatasetNotFound: If the dataset could not be found.
        '''
        raise NotImplementedError(f'{self} has not implemented this function')

    def get_property(self, dataset: str, key: str, *, metadata: bool = False,
                     overwrite_metadata_namespace: Optional[str] = None) -> Property:
        '''
        Gets a specific property named ``key`` from the ``dataset``. By default, only native properties are returned.
        This behaviour can be changed by setting ``metadata`` to **True**, which uses the default `metadata_namespace`
        to select the namespace. The namespace can be overwritten using ``overwrite_metadata_namespace`` for the
        duration of the method invocaton.

        :param dataset: Name of the dataset to get the property. Expects the full path beginning with the pool name.
        :param key: Name of the property to set. For non-native properties, set ``metadata`` to **True** and overwrite
            the default namespace using ``overwrite_metadata_namespace`` if required.
        :param metadata: If **True**, prepend the namespace to set a user (non-native) property.
        :param overwrite_metadata_namespace: Overwrite the default namespace for user (non-native) properties.
        :raises DatasetNotFound: If the dataset does not exist.
        :raises ValidationError: If validating the parameters failed.
        '''
        if key.strip() == 'all' and not metadata:
            raise ValidationError('"all" is not a valid property, use get_properties instead')
        if '/' not in dataset:
            # got a pool here
            validate_pool_name(dataset)
        else:
            validate_dataset_path(dataset)
        if metadata:
            if overwrite_metadata_namespace:
                prop_name = f'{overwrite_metadata_namespace}:{key}'
            elif self.metadata_namespace:
                prop_name = f'{self.metadata_namespace}:{key}'
            else:
                raise ValidationError('no metadata namespace set')
            validate_metadata_property_name(prop_name)
        else:
            validate_native_property_name(key)
            prop_name = key
        return self._get_property(dataset, prop_name, metadata)

    def _get_property(self, dataset: str, key: str, is_metadata: bool) -> Property:
        '''
        Actual implementation of the get_property function. This is to be implemented by the specific APIs. It is
        called by get_property, which has done all the validation and thus the parameters can be trusted to be valid.

        :param dataset: Name of the dataset to get the property. Expects the full path beginning with the pool name.
        :param key: Name of the property to set. For non-native properties, set ``metadata`` to **True** and overwrite
            the default namespace using ``overwrite_metadata_namespace`` if required.
        :param is_metadata: Indicates we're dealing with a metadata property.
        :raises DatasetNotFound: If the dataset does not exist.
        '''
        raise NotImplementedError(f'{self} has not implemented this function')

    def get_properties(self, dataset: str, *, include_metadata: bool = False) -> List[Property]:
        '''
        Gets all properties from the ``dataset``. By default, only native properties are returned. To include metadata
        properties, set ``include_metadata`` to **True**. In this mode, all properties are included, regardless of
        ``metadata_namespace``, it is up to the user to filter the metadata.

        :param dataset: Name of the dataset to get properties from. Expects the full path beginning with the pool name.
        :param include_metadata: If **True**, returns metadata (user) properties in addition to native properties.
        :raises DatasetNotFound: If the dataset does not exist.
        :raises ValidationError: If validating the parameters failed.
        '''
        if '/' not in dataset:
            validate_pool_name(dataset)
        else:
            validate_dataset_path(dataset)
        return self._get_properties(dataset, include_metadata)

    def _get_properties(self, dataset: str, include_metadata: bool):
        '''
        Actual implementation of the get_properties function. This is to be implemented by the specific APIs. It is
        called by get_properties, which has done all the validation and thus the parameters can be trusted to be valid.

        :param dataset: Name of the dataset to get properties from. Expects the full path beginning with the pool name.
        :param include_metadata: If **True**, returns metadata (user) properties in addition to native properties.
        :raises DatasetNotFound: If the dataset does not exist.
        :return: A list of properties.
        '''
        raise NotImplementedError(f'{self} has not implemented this function')

    def create_snapshot(
        self,
        dataset: str,
        name: str,
        *,
        properties: Dict[str, str] = None,
        metadata_properties: Dict[str, str] = None
    ) -> Dataset:
        '''
        Create a new snapshot from an existing dataset.

        .. warning::

           This action requires the ``pe_helper`` on Linux when not running as `root`.

        :param dataset: The dataset to snapshot.
        :param name: Name of the snapshot (the part after the ``@``)
        :param properties: Dict of native properties to set.
        :param metadata_properties: Dict of native properties to set. For namespaces other than the default (or when
            no default has been set, format the key using ``namespace:key``.
        :return: Info about the newly created dataset.
        :raises ValidationError: If validating the parameters failed.
        :raises DatasetNotFOund: If the dataset can't be found.
        '''
        return self.create_dataset(
            f'{dataset}@{name}',
            dataset_type=DatasetType.SNAPSHOT,
            properties=properties,
            metadata_properties=metadata_properties
        )

    def create_bookmark(self, snapshot: str, name: str) -> Dataset:
        '''
        Create a new bookmark from an existing snapshot.

        :param snapshot: The snapshot to attach a bookmark to.
        :param name: Name of the bookmark (the part after the ``#``)
        :return: Info about the newly created dataset.
        :raises ValidationError: If validating the parameters failed.
        :raises DatasetNotFound: If the snapshot can't be found.
        '''
        raise NotImplementedError(f'{self} has not implemented this function')

    def create_fileset(
        self,
        name: str,
        *,
        mountpoint: str = None,
        properties: Dict[str, str] = None,
        metadata_properties: Dict[str, str] = None,
        recursive: bool = True
    ) -> Dataset:
        '''
        Create a new fileset. For convenience, a ``mountpoint`` parameter can be given. If not **None**, it will
        overwrite any `mountpoint` value in the ``properties`` dict.

        .. warning::

           This action requires the ``pe_helper`` on Linux when not running as `root`.

        .. note::

           If the function raises a ``PermissionError`` or ``PEHelperException``, the fileset may have been created,
           but is missing its mountpoint property (along with it not being mounted) or other properties to which the
           user has no permission to change (not in ``zfs allow``).

        :param name: Name of the new fileset (complete path in the ZFS hierarchy).
        :ppram mountpoint: Convenience parameter for setting/overwriting the moutpoint property
        :param properties: Dict of native properties to set.
        :param metadata_properties: Dict of native properties to set. For namespaces other than the default (or when
            no default has been set, format the key using ``namespace:key``.
        :param recursive: Recursively create the parent fileset. Refer to the ZFS documentation about the `-p`
            parameter for ``zfs create``.
        :return: Info about the newly created dataset.
        :raises ValidationError: If validating the parameters failed.
        :raises DatasetNotFOund: If the parent dataset can't be found and ``recursive`` is `False`.
        '''
        if mountpoint is not None:
            if properties is None:
                properties = dict()
            # TODO validate path
            properties['mountpoint'] = mountpoint

        return self.create_dataset(
            name,
            dataset_type=DatasetType.FILESET,
            properties=properties,
            metadata_properties=metadata_properties,
            recursive=recursive,
        )

    def create_volume(
        self,
        name: str,
        *,
        size: int,
        sparse: bool = False,
        blocksize: Optional[int] = None,
        properties: Dict[str, str] = None,
        metadata_properties: Dict[str, str] = None,
        recursive: bool = False
    ) -> Dataset:
        '''
        Create a new volume of the given ``size`` (in bytes). If ``sparse`` is **True**, a sparse volume (also known
        as thin provisioned) will be created. If ``blocksize`` is given, it overwrites the ``blocksize`` property.

        .. note::

           Please read the note in :func:`~simplezfs.ZFS.create_filesystem` for permission handling for filesystems.
           Generally, if the user does not have permission to set certain properties, the dataset may or may not have
           been created but is missing the properties. It is up to the user of the library to clean up after
           catching a :class:`+simplezfs.exceptions.PermissionError`.

        :param name: Name of the new volume (complete path in the ZFS hierarchy).
        :param size: The size (in `bytes`) for the new volume.
        :param sparse: Whether to create a sparse volume. Requires ``size`` to be set.
        :param blocksize: If set, overwrites the `blocksize` property. Provided for convenience.
        :param properties: Dict of native properties to set.
        :param metadata_properties: Dict of native properties to set. For namespaces other than the default (or when
            no default has been set, format the key using ``namespace:key``.
        :param recursive: Recursively create the parent fileset. Refer to the ZFS documentation about the `-p`
            parameter for ``zfs create``.
        :return: Info about the newly created dataset.
        :raises ValidationError: If validating the parameters failed.
        :raises DatasetNotFound: If the parent dataset can't be found and ``recursive`` is `False`.
        '''
        if blocksize is not None:
            if properties is None:
                properties = dict()
            properties['blocksize'] = f'{blocksize}'
        return self.create_dataset(
            name,
            dataset_type=DatasetType.VOLUME,
            properties=properties,
            metadata_properties=metadata_properties,
            sparse=sparse,
            size=size,
            recursive=recursive
        )

    def create_dataset(
        self,
        name: str,
        *,
        dataset_type: DatasetType = DatasetType.FILESET,
        properties: Dict[str, str] = None,
        metadata_properties: Dict[str, str] = None,
        sparse: bool = False,
        size: Optional[int] = None,
        recursive: bool = False
    ) -> Dataset:
        '''
        Create a new dataset. The ``dataset_type`` parameter contains the type of dataset to create. This is a generic
        function to create datasets, you may want to take a look at the more specific functions (that essentially call
        this one) for convenience:

        * :func:`~ZFS.create_fileset`
        * :func:`~ZFS.create_snapshot`
        * :func:`~ZFS.create_volume`

        Properties specified with this call will be included in the create operation and are thus atomic. An exception
        applies for `filesets` with mountpoints that are neither ``none`` nor ``legacy`` on `Linux`.

        .. note::

            Bookmarks can't be created this way, use :func:`~ZFS.create_bookmark` for that.

        .. warning::

            On Linux, only root is allowed to manipulate the namespace (aka `mount`). Refer to :ref:`the_mount_problem`
            in the documentation.

        :param name: The name of the new dataset. This includes the full path, e.g. ``tank/data/newdataset``.
        :param dataset_type: Indicates the type of the dataset to be created.
        :param properties: A dict containing the properties for this new dataset. These are the native properties.
        :param metadata_properties: The metadata properties to set. To use a different namespace than the default (or
            when no default is set), use the ``namespace:key`` format for the dict keys.
        :param sparse: For volumes, specifies whether a sparse (thin provisioned) or normal (thick provisioned) volume
            should be created.
        :param size: For volumes, specifies the size in bytes.
        :param recursive: Recursively create the parent fileset. Refer to the ZFS documentation about the `-p`
            parameter for ``zfs create``. This does not apply to types other than volumes or filesets.
        :raises ValidationError: If validating the parameters failed.
        :raises DatasetNotFound: If the dataset (snapshot) or parent dataset (filesets and volumes with `recursive`
            set to `False`) can't be found.
        '''
        if dataset_type == DatasetType.BOOKMARK:
            raise ValidationError('Bookmarks can\'t be created using this function.')

        if '/' in name:
            validate_dataset_path(name)
        else:
            validate_pool_name(name)

        if self.dataset_exists(name):
            msg = 'Dataset already exists'
            log.error(msg)
            raise Exception(msg)

        # we can't create a toplevel element
        if '/' not in name and type in (DatasetType.FILESET, DatasetType.VOLUME):
            raise ValidationError('Can\'t create a toplevel fileset or volume, use ZPool instead.')

        # check the syntax of the properties
        if properties is not None:
            for k, val in properties.items():
                validate_native_property_name(k)
                validate_property_value(val)

        _metadata_properties = dict()  # type: Dict[str, str]
        if metadata_properties is not None:
            for k, val in metadata_properties.items():
                # if the name has no namespace, add the default one if set
                if ':' not in k:
                    if not self._metadata_namespace:
                        raise ValidationError(f'Metadata property {k} has no namespace and none is set globally')
                    meta_name = f'{self._metadata_namespace}:{k}'
                else:
                    meta_name = k
                _metadata_properties[meta_name] = metadata_properties[k]
                validate_metadata_property_name(meta_name)

                if type(val) != str:
                    _metadata_properties[meta_name] = f'{val}'
                validate_property_value(_metadata_properties[meta_name])

        # sparse and size are reset for all but the VOLUME type
        if dataset_type != DatasetType.VOLUME:
            if sparse:
                log.warning('Ignoring "sparse" it is only valid for volumes')
                sparse = False
            if size:
                log.warning('Ignoring "size", it is only valid for volumes')
                size = None

        # validate type specifics
        if dataset_type in (DatasetType.FILESET, DatasetType.VOLUME):
            if '@' in name or '#' in name:
                raise ValidationError('Volumes/Filesets can\'t contain @ (snapshot) or # (bookmark)')

            # NOTE this assumes that we're not being called on the root dataset itself!
            # check if the parent exists
            parent_ds = '/'.join(name.split('/')[:-1])
            if not self.dataset_exists(parent_ds) and not recursive:
                raise DatasetNotFound(f'Parent dataset "{parent_ds}" does not exist and "recursive" is not set')

            if dataset_type == DatasetType.VOLUME:
                if not size:
                    raise ValidationError('Size must be specified for volumes')
                try:
                    size = int(size)
                except ValueError as exc:
                    raise ValidationError('Size is not an integer') from exc

                if size < 1:
                    raise ValidationError('Size is too low')

                if properties and 'blocksize' in properties:
                    try:
                        blocksize = int(properties['blocksize'])
                    except ValueError as exc:
                        raise ValidationError('blocksize must be an integer') from exc
                    if blocksize < 2 or blocksize > 128 * 1024:  # zfs(8) version 0.8.1 lists 128KB as maximum
                        raise ValidationError('blocksize must be between 2 and 128kb (inclusive)')
                    if not ((blocksize & (blocksize - 1) == 0) and blocksize != 0):
                        raise ValidationError('blocksize must be a power of two')

        elif dataset_type == DatasetType.SNAPSHOT:
            if recursive:
                log.warning('"recursive" set for snapshot or bookmark, ignored')
                recursive = False

            symbol = '@' if dataset_type == DatasetType.SNAPSHOT else '#'

            if symbol not in name:
                raise ValidationError(f'Name must include {symbol}name')

            # check if parent exits
            ds_name, ss_name = name.split(symbol)
            if not self.dataset_exists(ds_name):
                raise DatasetNotFound(f'The parent dataset "{ds_name}" could not be found')

            # TODO

        return self._create_dataset(name, dataset_type=dataset_type, properties=properties,
                                    metadata_properties=_metadata_properties, sparse=sparse, size=size,
                                    recursive=recursive)

    def _create_dataset(
        self,
        name: str,
        *,
        dataset_type: DatasetType,
        properties: Dict[str, str] = None,
        metadata_properties: Dict[str, str] = None,
        sparse: bool = False,
        size: Optional[int] = None,
        recursive: bool = False,
    ) -> Dataset:
        '''
        Actual implementation of :func:`create_dataset`.

        :param name: The name of the new dataset. This includes the full path, e.g. ``tank/data/newdataset``.
        :param dataset_type: Indicates the type of the dataset to be created.
        :param properties: A dict containing the properties for this new dataset. These are the native properties.
        :param metadata_properties: The metadata properties to set. To use a different namespace than the default (or
            when no default is set), use the ``namespace:key`` format for the dict keys.
        :param sparse: For volumes, specifies whether a sparse (thin provisioned) or normal (thick provisioned) volume
            should be created.
        :param size: For volumes, specifies the size in bytes.
        t:param recursive: Recursively create the parent fileset. Refer to the ZFS documentation about the `-p`
            parameter for ``zfs create``. This does not apply to types other than volumes or filesets.
        :raises ValidationError: If validating the parameters failed.
        :raises DatasetNotFound: If the dataset can't be found (snapshot, bookmark) or the parent dataset can't be
            found (fileset, volume with ``recursive = False``).
        '''
        raise NotImplementedError(f'{self} has not implemented this function')

    def destroy_dataset(self, dataset: str, *, recursive: bool = False, force_umount: bool = False) -> None:
        '''
        Destroy a dataset. This function tries to remove a dataset, optionally removing all children recursively if
        ``recursive`` is **True**. This function works on all types of datasets, ``fileset``, ``volume``, ``snapshot``
        and ``bookmark``.

        This function can't be used to destroy pools, please use :class:`~zfs.ZPool` instead.

        Example:

        >>> zfs = ZFSCli()
        >>> zfs.destroy_dataset('pool/system/root@pre-distupgrade')

        :note: This is a destructive process that can't be undone.

        :param dataset: Name of the dataset to remove.
        :param recursive: Whether to recursively delete child datasets such as snapshots.
        :param force_umount: Forces umounting before destroying. Refer to ``ZFS(8)`` `zfs destroy` parameter ``-f``.
        :raises ValidationError: If validating the parameters failed.
        :raises DatasetNotFound: If the dataset can't be found.
        '''
        if '/' not in dataset:
            raise ValidationError('Cannot destroy the pool using this function')
        validate_dataset_path(dataset)

        if not self.dataset_exists(dataset):
            raise DatasetNotFound('The dataset could not be found')

        self._destroy_dataset(dataset, recursive=recursive, force_umount=force_umount)

    def _destroy_dataset(self, dataset: str, *, recursive: bool = False, force_umount: bool = False) -> None:
        '''
        Internal implementation of :func:`destroy_dataset`.

        :param dataset: The name of the dataset to remove.
        :param recursive: Whether to recursively delete child datasets such as snapshots.
        :param force_umount: Forces umounting before destroying.
        :raises ValidationError: If validating the parameters failed.
        :raises DatasetNotFound: If the dataset can't be found.
        '''
        raise NotImplementedError(f'{self} has not implemented this function')

    def _execute_pe_helper(self, action: str, name: str, mountpoint: Optional[str] = None):
        '''
        Runs the specified action through the PE helper.

        :param action: The action to perform. Valid are: "create", "destroy", "set_mountpoint".
        :param name: The name of the dataset to operate on.
        :param mountpoint: The mountpoint for create/set_mountpoint actions.
        :raises ValidationError: If the parameters are invalid.
        :raises PEHelperException: If the PE helper reported an error.
        '''
        if not self._pe_helper:
            raise ValidationError('PE Helper is not set')
        if action not in ('create', 'destroy', 'set_mountpoint'):
            raise ValidationError('Invalid action')
        validate_dataset_path(name)

        if action == 'create':
            if mountpoint is None:
                raise ValidationError(f'Mountpoint has to be set for action "{action}"')
            # TODO validate filesystem path
            cmd = [self._pe_helper, 'create', name, mountpoint]
        elif action == 'destroy':
            cmd = [self._pe_helper, 'destroy', name]
        elif action == 'set_mountpoint':
            if mountpoint is None:
                raise ValidationError(f'Mountpoint has to be set for action "{action}"')
            # TODO validate filesystem path
            cmd = [self._pe_helper, 'set_mountpoint', name, mountpoint]
        else:
            raise ValidationError('Invalid action')

        print(f'PE Helper: {cmd}')

        log = logging.getLogger('simplezfs.zfs.pe_helper')
        log.debug(f'About to run the following command: {cmd}')

        pass


def get_zfs(api: str = 'cli', metadata_namespace: Optional[str] = None, **kwargs) -> ZFS:
    '''
    Returns an instance of the desired ZFS API. Default is ``cli``.

    Using this function is an alternative to instantiating one of the implementations yourself.

    The parameters ``metadata_namespace`` and all of the ``kwargs`` are passed to the implementations constructor.

    Example:

    >>> from zfs import get_zfs, ZFS
    >>> type(get_zfs('cli'))
    <class 'zfs.zfs_cli.ZFSCli'>
    >>> type(get_zfs('native'))
    <class 'zfs.zfs_native.ZFSNative'>
    >>> isinstance(get_zfs(), ZFS)
    True

    :param api: API to use, either ``cli`` for zfs(8) or ``native`` for the `libzfs_core` api.
    :param metadata_namespace: Default namespace.
    :param kwargs: Extra parameters to pass to the implementations constructor.
    :return: An API instance.
    :raises NotImplementedError: If an unknown API was requested.
    '''
    if api == 'cli':
        from .zfs_cli import ZFSCli
        return ZFSCli(metadata_namespace=metadata_namespace, **kwargs)
    if api == 'native':
        from .zfs_native import ZFSNative
        return ZFSNative(metadata_namespace=metadata_namespace, **kwargs)
    raise NotImplementedError(f'The api "{api}" has not been implemented.')
