Python REST CodeEasy (pyce_rest)

This sample code implements a number of storage operations around volume,
snapshot, and flexclone management.  This is based off the Perl implementation
of the NetApp CodeEasy framework of scripts, and has been updated to use the
ONTAP REST API.

```
Requirements:
  1. Configure pyceRestConfig.py with your storage system related details.
  2. Python 3.5 or higher.
  3. The netapp-ontap Python package as described at:
     https://pypi.org/project/netapp-ontap/
     Note: Use module version 9.8.0 or higher, even with ONTAP 9.7!
  4. ONTAP 9.6 or higher.

Run "./pyce_rest.py -h" to see usage and examples.
```

Using pyce_rest.py

```
Usage: pyce_rest.py [options]

Options:
  --version     show program's version number and exit
  -h, --help    show this help message and exit
  -o OPERATION  operation type (see below)
  -v VOLUME     volume name
  -j JUNCTION   junction path
  -s SNAPSHOT   snapshot name
  -c CLONE      clone name
  -m MIRROR     snapmirror destination volume name
  -d            debug mode

  The following operation types are supported:
    list_volumes
    create_volume
    delete_volume
    remount_volume
    list_snapshots
    create_snapshot
    delete_snapshot
    list_clones
    create_clone
    list_mirrors
    create_mirror
    update_mirror
    delete_mirror

  Examples
    List all volumes with the string "build" in them:
    %> pyce_rest.py -o list_volumes -v build

    Create a new volume named "build123" with a junction-path of "/builds/build123":
    %> pyce_rest.py -o create_volume -v build123 -j /builds/build123

    Delete a volume or a clone named "build123":
    %> pyce_rest.py -o delete_volume -v build123 

    Remount a volume named "build123" with a junction-path of "/builds/build_current"
    %> pyce_rest.py -o remount_volume -v build123 -j /builds/build_current

    List all snapshots for volume "build123":
    %> pyce_rest.py -o list_snapshots -v build123 
  
    Create a snapshot named "snap1" on volume "build123":
    %> pyce_rest.py -o create_snapshot -v build123 -s snap1

    Delete a snapshot named "snap1" on volume "build123":
    %> pyce_rest.py -o delete_snapshot -v build123 -s snap1

    List all clones with the string "clone" in them:
    %> pyce_rest.py -o list_clones -c clone

    Create a new clone named "build123_clone" from volume "build", using
    snapshot "snap1", and use a junction-path of "/builds/build123_clone":
    %> pyce_rest.py -o create_clone -c build123_clone -v build123 -s snap1 -j /builds/build123_clone

    List snapmirror relationships:
    %> pyce_rest.py -o list_mirrors

    Create snapmirror relationship:
    %> pyce_rest.py -o create_mirror -v build123 volume -m build123_mirror

    Update snapmirror relationship:
    %> pyce_rest.py -o update_mirror -m build123_mirror

    Delete snapmirror relationship:
    %> pyce_rest.py -o delete_mirror -m build123_mirror
```

When using a custom vserver scoped login and role, other than admin or vsadmin,
note the following requirements.

1. The custom login must use "http" as the application:
```
security login create -user-or-group-name {user} -application http -authentication-method {method} -role {role} -vserver {svm}
```

2. The custom role must be given access to the SVM rest web service:
```
vserver services web access create -vserver {svm} -name rest -role {role}
```

3. The role must have access to the "job" command directory, since the
netapp-ontap Python module with make REST calls to poll for job completion.
```
security login role create -vserver {svm} -role {role} -cmddirname job -access readonly
```
