# Changelog

All notable changes to this project will be documented in this file.

## Release 0.0.4 - Unreleased

## Release 0.0.3 - Unreleased

**Features**

- The privilege escalation helper can now run proactively in some situations. While it could only be enabled or disabled (`use_pe_helper = True/False`), it can now also run proactively in some situations. To accomodate this, a new enum `PEHelperMode` was added. Instead of simply enabling or disabling it, a `PEHelperMode` enum has been introduced. The old `False` for disabling is now `PEHelperMode.DO_NOT_USE`, both `PEHelperMode.USE_IF_REQUIRED` and `PEHelperMode.USE_PROACTIVE` replace the old `True`, with the latter performing the action or parts of it (like umounting before destroying) before the actual action occurs. The old parameters and properties are slated for removal in the next release.

**Deprecated features**

- `use_pe_helper` was deprecated in favor of `pe_helper_mode`. Usage of the old parameters or properties will generate a `DeprecationWarning`. When used, they will set `pe_helper_mode` if appropriate, by either setting it to `PEHelperMode.DO_NOT_USE` (if `False`) or `PEHelperMode.USE_IF_REQUIRED` (when set `True`). The parameters and properties will be removed in the next version (`0.0.4`).

**Features**

- Support privilege escalation when removing a fileset in OpenZFS 2.0+, where the error message does no longer indicate that it is a permission problem.
- In some situations, privilege escalation can be performed proactively, i.e. if selected it calls the pe_helper right away instead of failing, analyzing the error message and then calling it.

**Tooling**

- Fix pytest deprecation warning


## Release 0.0.2

It spawned like this out of thin air.
