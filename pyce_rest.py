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
#      Note: Use module version 9.8.0 or higher, even with ONTAP 9.7!
#   4. ONTAP 9.7 or higher.
#
# Run "./pyce_rest.py -h" to see usage and examples.
#
################################################################################

version="2020.04.08"

import sys
import logging
from optparse import OptionParser
import pyceRestConfig

# Import the required netap_ontap modules.
from netapp_ontap import config as NaConfig
from netapp_ontap.host_connection import HostConnection as NaHostConnection
from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Volume as NaVolume
from netapp_ontap.resources import Snapshot as NaSnapshot
from netapp_ontap.resources import SnapmirrorRelationship as NaSnapmirrorRelationship
from netapp_ontap.resources import SnapmirrorTransfer as NaSnapmirrorTransfer

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
    volume_args = {
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        for volume in NaVolume.get_collection(**volume_args):
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


def create_volume(name, junction_path, type):
    if type == "dp":
        print("Creating mirror volume: " + name)
    else: 
        print("Creating volume: " + name + " with junction-path " + junction_path)

    # Build arguments for volume creation.
    volume_dict = {}
    volume_dict.update(pyceRestConfig.ce_volume_create_options)
    volume_dict["name"] = name
    volume_dict["svm"] = {}
    volume_dict["svm"]["name"] = pyceRestConfig.ce_vserver
    volume_dict["nas"]["path"] = junction_path
    volume_dict["type"] = type
    if type == "dp":
        # Mirror destinations cannot have these attributes set.
        del volume_dict["nas"]

    # Create the volume.
    volume = NaVolume.from_dict(volume_dict)
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
    if int(pyceRestConfig.ce_vol_maxfiles) > 0 and type != "dp":
        # First find the volume that we just created.
        volume_args = {
            "name": name,
            "svm.name": pyceRestConfig.ce_vserver,
        }
        try:
            volume = NaVolume.find(fields="files.maximum", **volume_args)
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
    volume_args = {
        "name": name,
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        volume = NaVolume.find(**volume_args)
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
    volume_args = {
        "name": name,
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        volume = NaVolume.find(fields="nas.path", **volume_args)
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
    volume_args = {
        "name": volume_name,
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        volume = NaVolume.find(fields="uuid", **volume_args)
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
        for snapshot in NaSnapshot.get_collection(volume.uuid):
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
    volume_args = {
        "name": volume_name,
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        volume = NaVolume.find(fields="uuid", **volume_args)
    except NetAppRestError:
        print("Error finding volume for snapshot listing!")
        raise
    if volume is None:
       print("Volume not found!")
       return
    
    # Create the snapshot.
    print("Creating snapshot " + snapshot_name + " in volume " + volume_name)
    snapshot = NaSnapshot(volume.uuid)
    snapshot.name = snapshot_name
    try:
        snapshot.post()
    except NetAppRestError:
        print("Error creating snapshot!")
        raise
    print("Created snapshot.")


def delete_snapshot(volume_name, snapshot_name):
    # First find the volume uuid.
    volume_args = {
        "name": volume_name,
        "svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        volume = NaVolume.find(fields="uuid", **volume_args)
    except NetAppRestError:
        print("Error finding volume for snapshot listing!")
        raise
    if volume is None:
       print("Volume not found!")
       return

    # Now find the snapshot and delete it.
    snapshot_args = {
        "name": snapshot_name,
    }
    try:
        snapshot = NaSnapshot.find(volume.uuid, **snapshot_args)
    except NetAppRestError:
        print("Error finding snapshot!")
        raise
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
    volume_args = {
        "svm.name": pyceRestConfig.ce_vserver,
        "clone.is_flexclone": True
    }
    try:
        for volume in NaVolume.get_collection(**volume_args): 
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
    volume_dict = {
        "svm": {
            "name": pyceRestConfig.ce_vserver
        },
        "name": clone,
        "nas": {
            "path": junction_path
        }, 
        "clone": {
            "is_flexclone": "true",
            "parent_snapshot": {"name": snapshot},
            "parent_volume": {"name": volume},
        },
    }

    # Create the clone.
    volume = NaVolume.from_dict(volume_dict)
    try:
        volume.post()
    except NetAppRestError:
        print("Error creating clone!")
        raise

    print("Volume clone created succesfully.")


def list_mirrors():
    print("Getting list snapmirror relationships.")

    # Print header
    print("")
    print("%-32s %-32s %-16s %-16s" % ("Source", "Destination", "State", "Status"))
    print("------------------------------------------------------------------------------------------------")

    # Get list of volumes and print matches as we go.    
    sm_args = {
        "destination.svm.name": pyceRestConfig.ce_vserver
    }
    try:
        for mirror in NaSnapmirrorRelationship.get_collection(**sm_args):
            try:
                mirror.get(fields="state,transfer,source.path,destination.path")
            except NetAppRestError:
                print("Error retrieving mirror details.")
                raise
            src = dst = state = status = ""
            mirror_dict = mirror.to_dict()
            if "source" in mirror_dict:
                if "path" in mirror_dict["source"]:
                    src = mirror_dict["source"]["path"]
            if "destination" in mirror_dict:
                if "path" in mirror_dict["destination"]:
                    dst = mirror_dict["destination"]["path"]
            if "state" in mirror_dict:
                state = mirror_dict["state"]
            if "transfer" in mirror_dict:
                if "state" in mirror_dict["transfer"]:
                    status = mirror_dict["transfer"]["state"]
            # The transfer.status is only returned for active relationships.
            if status == "":
                status = "idle"
            print("%-32s %-32s %-16s %-16s" % (src, dst, state, status))
    except NetAppRestError:
        print("Error retrieving mirror relationship list.")
        raise


def create_mirror(src, dst):
    print("Creating mirror " + dst + " of source " + src)

    # Build arguments for volume creation.
    sm_dict = {
        "source": {
            "path": pyceRestConfig.ce_vserver + ":" + src
        },
        "destination": {
            "path": pyceRestConfig.ce_vserver + ":" + dst
        },
    }

    # Create the snapmirror.
    # This assumes we have already created a DP mirror destination.
    mirror = NaSnapmirrorRelationship.from_dict(sm_dict)
    try:
        mirror.post()
    except NetAppRestError:
        print("Error creating mirror!")
        raise
    print("Mirror created succesfully.")


def update_mirror(dst):
    # First find the snapmirror relationship uuid.
    sm_args = {
        "destination.path": pyceRestConfig.ce_vserver + ":" + dst,
        "destination.svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        mirror = NaSnapmirrorRelationship.find(fields="uuid", **sm_args)
    except NetAppRestError:
        print("Error finding mirror volume!")
        raise

    # If we found the relationshp, perform the update.
    if mirror:
        print("Updating mirror " + dst)
        mirror_transfer = NaSnapmirrorTransfer(mirror.uuid)
        try:
            mirror_transfer.post()
        except NetAppRestError:
            print("Error updating mirror!")
            raise
        print("Mirror updated.")
    else:
        print("Mirror not found.")


def delete_mirror(dst):
    # First find the snapmirror relationship uuid.
    sm_args = {
        "destination.path": pyceRestConfig.ce_vserver + ":" + dst,
        "destination.svm.name": pyceRestConfig.ce_vserver,
    }
    try:
        mirror = NaSnapmirrorRelationship.find(fields="uuid", **sm_args)
    except NetAppRestError:
        print("Error finding mirror volume!")
        raise

    # If we found the relationshp, delete it.
    if mirror:
        print("Deleting mirror " + dst)
        try:
            mirror.delete()
        except NetAppRestError:
            print("Error deleting mirror!")
            raise
        print("Mirror deleted.")
    else:
        print("Mirror not found.")


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
parser.add_option("-m", dest="mirror", help="snapmirror destination volume name")
parser.add_option("-d", dest="debug", action="store_true", help="debug mode")
(options, args) = parser.parse_args()

# Check for a valid operation type.
op = options.operation
operations = ["list_volumes","create_volume","delete_volume","remount_volume",
              "list_snapshots","create_snapshot","delete_snapshot",
              "list_clones","create_clone",
              "list_mirrors", "create_mirror","update_mirror","delete_mirror",
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
if op == "create_mirror":
    if not options.volume:
        print("Missing volume name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.mirror:
        print("Missing mirror volume for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
if op == "update_mirror" or op == "delete_mirror":
    if not options.mirror:
        print("Missing mirror volume for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)

# If we get here, everything should be OK

# Setup the REST API connection to ONTAP.
# Using verify=False to ignore that we may see self-signed SSL certificates.
NaConfig.CONNECTION = NaHostConnection(
    host = pyceRestConfig.ce_cluster,
    username = pyceRestConfig.ce_user,
    password = pyceRestConfig.ce_passwd,
    verify = False,
    poll_timeout = 120,
)

# Call the requested operation
if op == "list_volumes":
    list_volumes(options.volume)

if op == "create_volume":
    create_volume(options.volume, options.junction, "rw")

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

if op == "list_mirrors":
    list_mirrors()

if op == "create_mirror":
    create_volume(options.mirror, "", "dp")
    create_mirror(options.volume, options.mirror)
    update_mirror(options.mirror)

if op == "update_mirror":
    update_mirror(options.mirror)

if op == "delete_mirror":
    delete_mirror(options.mirror)
