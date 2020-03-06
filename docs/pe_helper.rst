###########################
Privilege Escalation Helper
###########################

The Privilege Escalation Helper (**PE Helper**) mechanism works around the problem that only `root` is allowed to
manipulate the global namespace on Linux hosts, which means that only `root` can mount and unmount filesystems /
filesets. In normal operation, users can be granted permission to do almost anything with a ZFS, except for mounting.

Thus, elevated privileges are required for these actions, which in particular revolves around:
* Creating a fileset with the ``mountpoint`` property set
* Mounting or unmounting a fileset
* Destroying a mounted fileset

While the PE Helper may be useful in other areas, such as acting as a ``sudo(8)`` wrapper, its use is limited to the
bare minimum. All other actions can be performed by using ``zfs allow`` to allow low-privilege-users to perform them.

There are two implementations of PE Helpers provided:

* :class:`~simplezfs.pe_helper.ExternalPEHelper` which runs a user-specified script or program to perform the actions,
  one is provided as an example in the `scripts` folder. This is the most flexible and possibly the most dangerous way
  to handle things.
* :class:`~simplezfs.pe_helper.SudoPEHelper` simply runs the commands through ``sudo(8)``, so the user needs to set up
  their ``/etc/sudoers`` accordingly.

Additonal implementations need only to inherit from :class:`~simplezfs.pe_helper.PEHelperBase`.
