Munin plugins that monitor FreeNAS.

Where possible we monitor via SNMP, however some stats are not accessible via SNMP.  The current script runs a python script via SSH,
this dumps data to a text file, then we scp it back.
