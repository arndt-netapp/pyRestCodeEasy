```
Python REST CodeEasy (pyce_rest)

This sample code implements a number of storage operations around volume,
snapshot, and flexclone management.  This is based off the Perl implementation
of the NetApp CodeEasy framework of scripts, and has been updated to use the
ONTAP REST API.

Requirements:
  1. Configure pyceRestConfig.py with your storage system related details.
  2. Python 3.5 or higher.
  3. The netapp-ontap Python package as described at:
     https://pypi.org/project/netapp-ontap/
  4. ONTAP 9.6 or higher.

Run "./pyce_rest.py -h" to see usage and examples.

Usage: pyce_rest.py [options]

Options:
  --version     show program's version number and exit
  -h, --help    show this help message and exit
  -o OPERATION  operation type (see below)
  -v VOLUME     volume name
  -j JUNCTION   junction path
  -s SNAPSHOT   snapshot name
  -c CLONE      clone name
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
```
