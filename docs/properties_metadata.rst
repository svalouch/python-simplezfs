#######################
Properties and Metadata
#######################

ZFS features a property system using ``zfs(8) get/set``, which is used to read information about datasets and change their behaviour. Additionally, it allows users to attach arbitrary properties on their own to datasets. ZFS calls these "`user properties`", distinguishing them from its own "`native properties`" by requirim a ``:`` character. This library calls the user properties **metadata** properties.


