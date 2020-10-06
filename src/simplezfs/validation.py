
'''
Functions for validating data.
'''

import re

from .exceptions import ValidationError


#: Maximum length of a dataset (from zfs(8)) in bytes
MAXNAMELEN: int = 256
#: Maximum length of a native property name (assumed, TODO check in source)
NATIVE_PROPERTY_NAME_LEN_MAX: int = MAXNAMELEN
#: Maximum length of a metadata property name (assumed, TODO check in source)
METADATA_PROPERTY_NAME_LEN_MAX: int = MAXNAMELEN
#: Maximum length of a metadata property value in bytes
METADATA_PROPERTY_VALUE_LEN_MAX: int = 8192

#: Regular expression for validating dataset names, handling both the name itself as well as snapshot or bookmark names
DATASET_NAME_RE = re.compile(r'^(?P<dataset>[a-zA-Z0-9_\-.:]+)(?P<detail>(@|#)[a-zA-Z0-9_\-.:]+)?$')
#: Regular expression for validating a native property name
NATIVE_PROPERTY_NAME_RE = re.compile(r'^[a-z]([a-z0-9]+)?$')
#: Regular expression for validating the syntax of a user property (metadata property in python-zfs)
METADATA_PROPERTY_NAME_RE = re.compile(r'^([a-z0-9_.]([a-z0-9_.\-]+)?)?:([a-z0-9:_.\-]+)$')


def validate_pool_name(name: str) -> None:
    '''
    Validates a pool name.

    :raises ValidationError: Indicates validation failed
    '''
    try:
        b_name = name.encode('utf-8')
    except UnicodeEncodeError as err:
        raise ValidationError(f'unicode encoding error: {err}') from err
    if len(b_name) < 1:
        raise ValidationError('too short')
    # TODO find maximum pool name length

    # The pool name must begin with a letter, and can only contain alphanumeric characters as well as underscore
    # ("_"), dash ("-"), colon (":"), space (" "), and period (".").
    if not re.match(r'^[a-z]([a-z0-9\-_: .]+)?$', name):
        raise ValidationError('malformed name')
    # The pool names mirror, raidz, spare and log are reserved,
    if name in ['mirror', 'raidz', 'spare', 'log']:
        raise ValidationError('reserved name')
    # as are names beginning with mirror, raidz, spare,
    for word in ['mirror', 'raidz', 'spare']:
        if name.startswith(word):
            raise ValidationError(f'starts with invalid token {word}')
    # and the pattern c[0-9].
    if re.match(r'^c[0-9]', name):
        raise ValidationError('begins with reserved sequence c[0-9]')


def validate_dataset_name(name: str, *, strict: bool = False) -> None:
    '''
    Validates a dataset name. By default (``strict`` set to **False**) a snapshot (``name@snapshotname``) or bookmark
    (``name#bookmarkname``) postfix are allowed. Otherwise, these names are rejected. To validate a complete path, see
    :func:`validate_dataset_path`.

    Example:

    >>> from zfs.validation import validate_dataset_name
    >>> validate_dataset_name('swap')
    >>> validate_dataset_name('backup', strict=True)
    >>> validate_dataset_name('backup@20190525', strict=True)
    zfs.validation.ValidationError: snapshot or bookmark identifier are not allowed in strict mode
    >>> validate_dataset_name('')
    zfs.validation.ValidationError: name is too short
    >>> validate_dataset_name('pool/system')
    zfs.validation.ValidationError: name contains disallowed characters
    >>> validate_dataset_name('a' * 1024)  # really long name
    zfs.validation.ValidationError: length > 255

    :param name: The name to validate
    :param strict: Whether to allow (``False``) or disallow (``True``) snapshot and bookmark names.
    :raises ValidationError: Indicates validation failed
    '''
    try:
        b_name = name.encode('utf-8')
    except UnicodeEncodeError as err:
        raise ValidationError(f'unicode encoding error: {err}') from err
    if len(b_name) < 1:
        raise ValidationError('name is too short')
    if len(b_name) > MAXNAMELEN - 1:
        raise ValidationError(f'length > {MAXNAMELEN - 1}')
    match = DATASET_NAME_RE.match(name)
    if not match:
        raise ValidationError('name contains disallowed characters')
    if strict and match.group('detail') is not None:
        raise ValidationError('snapshot or bookmark identifier are not allowed in strict mode')


def validate_dataset_path(path: str) -> None:
    '''
    Validates a path of datasets. While :func:`validate_dataset_name` validates only a single entry in a path to a
    dataset, this function validates the whole path beginning with the pool.

    :raises ValidationError: Indicates validation failed
    '''
    try:
        b_name = path.encode('utf-8')
    except UnicodeEncodeError as err:
        raise ValidationError(f'unicode encoding error: {err}') from err
    if len(b_name) < 3:  # a/a is the smallest path
        raise ValidationError('path is too short')
    if '/' not in path:
        raise ValidationError('Not a path')
    if path.startswith('/'):
        raise ValidationError('zfs dataset paths are never absolute')

    tokens = path.split('/')
    # the first token is the pool name
    validate_pool_name(tokens[0])
    # second token to second-to-last token are normal datasets that must not be snapshots or bookmarks
    for dataset in tokens[1:-1]:
        validate_dataset_name(dataset, strict=True)
    # last token is the actual dataset, this may be a snapshot or bookmark
    validate_dataset_name(tokens[-1])


def validate_native_property_name(name: str) -> None:
    '''
    Validates the name of a native property. Length and syntax is checked.

    :note: No check is performed to match the name against the actual names the target ZFS version supports.
    :raises ValidationError: Indicates that the validation failed.
    '''
    try:
        b_name = name.encode('utf-8')
    except UnicodeEncodeError as err:
        raise ValidationError(f'unicode encoding error: {err}') from err
    if len(b_name) < 1:
        raise ValidationError('name is too short')
    if len(b_name) > NATIVE_PROPERTY_NAME_LEN_MAX - 1:
        raise ValidationError(f'length > {NATIVE_PROPERTY_NAME_LEN_MAX - 1}')
    if not NATIVE_PROPERTY_NAME_RE.match(name):
        raise ValidationError('property name does not match')


def validate_metadata_property_name(name: str) -> None:
    '''
    Validate the name of a metadata property (user property in ZFS manual).

    :raises ValidationError: Indicates that the validation failed.
    '''
    try:
        b_name = name.encode('utf-8')
    except UnicodeEncodeError as err:
        raise ValidationError(f'unicode encoding error: {err}') from err
    if len(b_name) < 1:
        raise ValidationError('name is too short')
    if len(b_name) > METADATA_PROPERTY_NAME_LEN_MAX - 1:
        raise ValidationError(f'length > {METADATA_PROPERTY_NAME_LEN_MAX - 1}')
    if not METADATA_PROPERTY_NAME_RE.match(name):
        raise ValidationError('property name does not match')


def validate_property_value(value: str) -> None:
    '''
    Validates the value of a property. This works for both native properties, where the driver will tell us if the
    value was good or not, as well metadata (or user) properties where the only limit is its length.

    :param value: The value to validate.
    :raises ValidationError: Indicates that the validation failed.
    '''
    try:
        b_value = value.encode('utf-8')
    except UnicodeEncodeError as err:
        raise ValidationError(f'unicode encoding error: {err}') from err
    if len(b_value) > METADATA_PROPERTY_VALUE_LEN_MAX - 1:
        raise ValidationError(f'length > {METADATA_PROPERTY_VALUE_LEN_MAX - 1}')
