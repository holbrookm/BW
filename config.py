#!/usr/bin/python

""" This script will be the configuration file for the EMA APPlication.
    #Marc Holbrook
    # 0851742253
    # <mholbrook@eircom.ie>
"""


from mysockets import SET_LAB_FLAG

#_host = '10.147.21.198'  # Live Node
_host = '10.144.134.198'   # Test Plant
_port = '2208'


_timeout = '30'

if SET_LAB_FLAG:
    _ociuser = 'admin'
    _ocipass = 'admin'
else:
    _ociuser = 'admin@web.ngv.eircom.net'
    _ocipass = '&VQ|FrDb*)'

