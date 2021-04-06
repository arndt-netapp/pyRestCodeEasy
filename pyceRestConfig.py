# Variables that define how we connect to the storage cluster or vserver
ce_cluster              = "vs1"
ce_user                 = "vsadmin"
ce_passwd               = "netapp123"
ce_vserver              = "vs1"

# Variables related to volume creation
ce_volume_create_options = {}
ce_volume_create_options['aggregates'] = []
ce_volume_create_options['aggregates'].append({})
ce_volume_create_options['aggregates'][0]['name']                = 'aggr1'
ce_volume_create_options['size']                                 = '10240g'
ce_volume_create_options['nas'] = {}
ce_volume_create_options['nas']['uid']                           = '0'
ce_volume_create_options['nas']['gid']                           = '25'
ce_volume_create_options['nas']['unix_permissions']              = '777'
ce_volume_create_options['nas']['export_policy'] = {}
ce_volume_create_options['nas']['export_policy']['name']         = 'default'
ce_volume_create_options['snapshot_policy'] = {}
ce_volume_create_options['snapshot_policy']['name']              = 'none'
ce_volume_create_options['space'] = {}
ce_volume_create_options['space']['snapshot'] = {}
ce_volume_create_options['space']['snapshot']['reserve_percent'] = '0'
ce_volume_create_options['guarantee'] = {}
ce_volume_create_options['guarantee']['type']                    = 'none'
ce_volume_create_options['nas']['security_style']                = 'unix'

# Options maxfiles setting
ce_vol_maxfiles         = "75000000"

#ce_volume_create_options['efficiency-policy']                    = 'auto'
