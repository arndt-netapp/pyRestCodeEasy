#!/usr/bin/env python3

################################################################################
#
# Python CodeEasy with ONTAP REST API (pyce_rest)
#
# This sample code implements a number of storage operations around volume,
# snapshot, and flexclone management.  This is based off the Perl implementation
# of the NetApp CodeEasy framework of scripts.
#
# Requirements:
#   1. Configure pyceRestConfig.py with your storage system related details.
#   2. Python 3.5 or higher.
#   3. The netapp-ontap Python package as described at:
#      https://pypi.org/project/netapp-ontap/
#   3. ONTAP 9.6 or higher.
#
# Run "./pyce_rest.py -h" to see usage and examples.
#
################################################################################

version="1.0"

import sys
import logging
from optparse import OptionParser
import pyceRestConfig

# Import the required netap_ontap modules.
from netapp_ontap import HostConnection, NetAppRestError, config, utils
from netapp_ontap.resources import Volume, Snapshot

# Uncomment these for additional ONTAP REST API debugging.
#logging.basicConfig(level=logging.DEBUG)
#utils.DEBUG = 1
#utils.LOG_ALL_API_CALLS = 1


def list_volumes(volume_string):
    print("Getting list of volumes that match: " + volume_string)

    # Print header
    print("")
    print("%-24s %-40s %10s %10s" % ("Volume Name", "Junction Path", "Size (GB)", "Used (GB)"))
    print("---------------------------------------------------------------------------------------")

    # Get list of volumes and print matches as we go.    
    kwargs = {
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        for volume in Volume.get_collection(**kwargs): 
            name = volume.to_dict()['name']
            if volume_string in name:
                try:
                    volume.get(fields="name,space.used,space.size,nas.path")
                except NetAppRestError:
                    print("Error retrieving volume details for volume: " + name)
                    raise
                volume_dict = volume.to_dict()
                used = size = junc_path = ""
                if "space" in volume_dict:
                    if "used" in volume_dict["space"]:
                        used = volume_dict['space']['used']
                        size = volume_dict['space']['size']
                        size  = int(size / (1024*1024*1024))
                        used  = int(used / (1024*1024*1024))
                if "nas" in volume_dict:
                    if "path" in volume_dict['nas']:
                        junc_path = volume_dict['nas']['path']
                print("%-24s %-40s %10s %10s" % (name, junc_path, size, used))
    except NetAppRestError:
        print("Error retrieving volume list.")
        raise


def create_volume(name, junction_path):
    print("Creating volume: " + name + " with junction-path " + junction_path)

    # Build arguments for volume creation.
    kwargs = {}
    kwargs.update(pyceRestConfig.ce_volume_create_options)
    kwargs["name"] = name
    kwargs["svm"] = {}
    kwargs["svm"]["name"] = pyceRestConfig.ce_vserver
    kwargs["nas"]["path"] = junction_path

    # Create the volume.
    volume = Volume(**kwargs)
    try:
        volume.post()
    except NetAppRestError:
        print("Error creating volume!")
        raise
    print("Volume created succesfully.")

    # Set maxfiles if required.
    try:
        pyceRestConfig.ce_vol_maxfiles
    except NameError:
      pyceRestConfig.ce_vol_maxfiles = "0"
    if int(pyceRestConfig.ce_vol_maxfiles) > 0:
        # First find the volume that we just created.
        kwargs = {
            "name": name,
            "svm": {"name": pyceRestConfig.ce_vserver},
        }
        try:
            volume = Volume.find(fields="files.maximum", **kwargs)
        except NetAppRestError:
            print("Error finding new volume to set maxfiles!")
            raise
        # Now set the files.maximum field and patch the volume.
        volume.files.maximum = pyceRestConfig.ce_vol_maxfiles
        try:
            volume.patch()
        except NetAppRestError:
            print("Error setting maxfiles on volume!")
            raise
        print("Volume maxfiles updated successfully.")


def delete_volume(name):
    print("Deleting volume: " + name)

    # First find the volume to be deleted.
    kwargs = {
        "name": name,
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        volume = Volume.find(**kwargs)
    except NetAppRestError:
        print("Error finding volume to be deleted!")
        raise

    # If we have found the volume, delete it.
    if volume:
        try:
            volume.delete()
        except NetAppRestError:
            print("Error deleting volume!")
            raise
        print("Volume deleted.")
    else:
        print("Error: Volume not found!")


def remount_volume(name, junction_path):
    print("Re-mounting volume: " + name + " with junction of " + junction_path)

    # First find the volume to be remounted.
    kwargs = {
        "name": name,
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        volume = Volume.find(fields="nas.path", **kwargs)
    except NetAppRestError:
        print("Error finding volume to be remounted!")
        raise

    # Now set the new nas.path for the volume and update it.
    volume.nas.path = junction_path
    try:
        volume.patch()
    except NetAppRestError:
        print("Error remounting volume!")
        raise

    print("Volume remounted successfully.")

def list_snapshots(volume_name):
    print("Getting list of snapshots on volume: " + volume_name)

    # First find the volume uuid.
    kwargs = {
        "name": volume_name,
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        volume = Volume.find(fields="uuid", **kwargs)
    except NetAppRestError:
        print("Error finding volume for snapshot listing!")
        raise
    if volume is None:
       print("Volume not found!")
       return

    # Print header.
    print("")
    print("%-32s %-32s %-28s" % ("Volume Name", "Snapshot Name", "Snapshot Date"))
    print("----------------------------------------------------------------------------------------------")

    # Now get the collection of snapshots for the volume and print details.
    try:
        for snapshot in Snapshot.get_collection(volume.uuid):
            try:
                snapshot.get(fields="name,create_time")
            except NetAppRestError:
                print("Error retrieving snapshot details for volume!")
                raise
            snapshot_dict = snapshot.to_dict()
            snapname = create_time = ""
            if "name" in snapshot_dict:
                snapname = snapshot_dict["name"]
            if "create_time" in snapshot_dict:
                snaptime = snapshot_dict["create_time"]
            print("%-32s %-32s %-28s" % (volume_name, snapname, snaptime))
    except NetAppRestError:
        print("Error retrieving snapshot list.")
        raise


def create_snapshot(volume_name, snapshot_name):
    # First find the volume uuid.
    kwargs = {
        "name": volume_name,
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        volume = Volume.find(fields="uuid", **kwargs)
    except NetAppRestError:
        print("Error finding volume for snapshot listing!")
        raise
    if volume is None:
       print("Volume not found!")
       return
    
    # Create the snapshot.
    print("Creating snapshot " + snapshot_name + " in volume " + volume_name)
    snapshot = Snapshot(volume.uuid)
    snapshot.name = snapshot_name
    try:
        snapshot.post()
    except NetAppRestError:
        print("Error creating snapshot!")
        raise
    print("Created snapshot.")


def delete_snapshot(volume_name, snapshot_name):
    # First find the volume uuid.
    kwargs = {
        "name": volume_name,
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        volume = Volume.find(fields="uuid", **kwargs)
    except NetAppRestError:
        print("Error finding volume for snapshot listing!")
        raise
    if volume is None:
       print("Volume not found!")
       return

    # Now find the snapshot and delete it.
    kwargs = {
        "name": snapshot_name,
    }
    snapshot = Snapshot.find(volume.uuid, **kwargs)
    if snapshot:
        print("Deleting snapshot " + snapshot_name + " in volume " + volume_name)
        try:
            snapshot.delete()
        except NetAppRestError:
            print("Error deleting snapshot!")
            raise
        print("Deleted snapshot.")
    else:
        print("Snapshot not found!")


def list_clones(volume_string):
    print("Getting list of clones that match: " + volume_string)

    # Print header
    print("")
    print("%-24s %-24s %-24s %-24s" % ("Parent Volume", "Parent Snapshot", "FlexClone Volume", "FlexClone Junction"))
    print("----------------------------------------------------------------------------------------------------")

    # Get list of volume clones and print matches as we go.    
    kwargs = {
        "svm.name": pyceRestConfig.ce_vserver,
        "clone.is_flexclone": True
    }
    try:
        for volume in Volume.get_collection(**kwargs): 
            name = volume.to_dict()['name']
            if volume_string in name:
                try:
                    volume.get(fields="name,clone,nas.path")
                except NetAppRestError:
                    print("Error retrieving volume details for volume: " + name)
                    raise
                volume_dict = volume.to_dict()
                volume_name = snapshot = clone_name = junction_path = ""
                if "name" in volume_dict:
                    clone_name = volume_dict["name"]
                if "clone" in volume_dict:
                    if "parent_volume" in volume_dict["clone"]:
                        volume_name = volume_dict["clone"]["parent_volume"]["name"]
                    if "parent_snapshot" in volume_dict["clone"]:
                        snapshot = volume_dict["clone"]["parent_snapshot"]["name"]
                if "nas" in volume_dict:
                    if "path" in volume_dict["nas"]:
                        junction_path = volume_dict["nas"]["path"]
                print("%-24s %-24s %-24s %-24s" % \
                (volume_name, snapshot, clone_name, junction_path))
    except NetAppRestError:
        print("Error retrieving volume list.")
        raise

  
def create_clone(volume, clone, snapshot, junction_path):
    print("Creating clone volume " + clone + " of parent volume " + volume + \
          " with snapshot " + snapshot + " and junction-path " + junction_path)

    # Build arguments for volume clone creation.
    kwargs = {
        "svm": {"name": pyceRestConfig.ce_vserver},
        "name": clone,
        "nas": {"path": junction_path}, 
        "clone": {
            "is_flexclone": "true",
            "parent_snapshot": {"name": snapshot},
            "parent_volume": {"name": volume},
        }
    }

    # Create the clone.
    volume = Volume(**kwargs)
    try:
        volume.post()
    except NetAppRestError:
        print("Error creating clone!")
        raise

    print("Volume clone created succesfully.")


def help_text():
    help_text = """
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
    %> pyce.py -o list_volumes -v build

    Create a new volume named "build123" with a junction-path of "/builds/build123":
    %> pyce.py -o create_volume -v build123 -j /builds/build123

    Delete a volume or a clone named "build123":
    %> pyce.py -o delete_volume -v build123 

    Remount a volume named "build123" with a junction-path of "/builds/build_current"
    %> pyce.py -o remount_volume -v build123 -j /builds/build_current

    List all snapshots for volume "build123":
    %> pyce.py -o list_snapshots -v build123 
  
    Create a snapshot named "snap1" on volume "build123":
    %> pyce.py -o create_snapshot -v build123 -s snap1

    Delete a snapshot named "snap1" on volume "build123":
    %> pyce.py -o delete_snapshot -v build123 -s snap1

    List all clones with the string "clone" in them:
    %> pyce.py -o list_clones -c clone

    Create a new clone named "build123_clone" from volume "build", using
    snapshot "snap1", and use a junction-path of "/builds/build123_clone":
    %> pyce.py -o create_clone -c build123_clone -v build123 -s snap1 -j /builds/build123_clone
"""

    return help_text

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

# Parse CLI options
help_text = help_text()
OptionParser.format_epilog = lambda self, formatter: self.epilog
parser = OptionParser(epilog=help_text, version=version)
parser.add_option("-o", dest="operation", help="operation type (see below)")
parser.add_option("-v", dest="volume", help="volume name")
parser.add_option("-j", dest="junction", help="junction path")
parser.add_option("-s", dest="snapshot", help="snapshot name")
parser.add_option("-c", dest="clone", help="clone name")
parser.add_option("-d", dest="debug", action="store_true", help="debug mode")
(options, args) = parser.parse_args()

# Check for a valid operation type.
op = options.operation
operations = ["list_volumes","create_volume","delete_volume","remount_volume",\
              "list_snapshots","create_snapshot","delete_snapshot",\
              "list_clones","create_clone"\
             ]
if not op:
    print("No operation type given.")
    print("Use -h to see usage and examples.")
    sys.exit(2)
if op not in operations:
    print("Invalid operation type: " + op)
    print("Use -h to see usage and examples.")
    sys.exit(2)

# Make sure we have the required arguments for each operation
if op == "list_volumes" or op == "delete_volume" or op == "list_snapshots":
    if not options.volume:
        print("Missing volume name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
if op == "create_volume" or op == "remount_volume":
    if not options.volume:
        print("Missing volume name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.junction:
        print("Missing junction path for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
if op == "create_snapshot" or op == "delete_snapshot":
    if not options.volume:
        print("Missing volume name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.snapshot:
        print("Missing snapshot name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
if op == "list_clones":
    if not options.clone:
        print("Missing clone name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
if op == "create_clone":
    if not options.volume:
        print("Missing volume name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.snapshot:
        print("Missing snapshot name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.clone:
        print("Missing clone name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.junction:
        print("Missing junction path for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)

# If we get here, everything should be OK

# Setup the REST API connection to ONTAP.
# Using verify=False to ignore that we may see self-signed SSL certificates.
config.CONNECTION = HostConnection(
    pyceRestConfig.ce_cluster, username=pyceRestConfig.ce_user,
    password=pyceRestConfig.ce_passwd, verify=False,
)

# Call the requested operation
if op == "list_volumes":
    list_volumes(options.volume)

if op == "create_volume":
    create_volume(options.volume, options.junction)

if op == "delete_volume":
    delete_volume(options.volume)

if op == "remount_volume":
    remount_volume(options.volume, options.junction)

if op == "list_snapshots":
    list_snapshots(options.volume)
   
if op == "create_snapshot":
    create_snapshot(options.volume, options.snapshot)

if op == "delete_snapshot":
    delete_snapshot(options.volume, options.snapshot)

if op == "list_clones":
    list_clones(options.clone)

if op == "create_clone":
    create_clone(options.volume, options.clone, options.snapshot, options.junction)
