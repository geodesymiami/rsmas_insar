#!/usr/bin/env python
# coding: utf-8

# In[103]:


#!/usr/bin/env python3
############################################################
# Program is part of MinSAR                                #
# Copyright (c) 2023, Falk Amelung                         #
############################################################

import datetime
import os
import sys
import argparse

import mintpy
from mintpy.defaults.template import STEP_LIST
from mintpy.utils.arg_utils import create_argument_parser
EXAMPLE = """example:
  smallbaselineApp.py                         # run with default template 'smallbaselineApp.cfg'
"""
    
def create_parser(subparsers=None):
    synopsis = 'Plotting of InSAR, GPS and Seismicity data'
    epilog = EXAMPLE
    parser = argparse.ArgumentParser(description='Plot InSAR, GPS and seismicity data\n')

    parser.add_argument('dataDir', help='Directory with InSAR data.\n')
    parser.add_argument('--seismicity', dest='flag_seismicity', action='store_true', default=True,
                        help='flag to add seismicity')
    parser.add_argument('--noseismicity', dest='flag_noseismicity', action='store_true',default=False,
                        help='flag to remove seismicity')
    parser.add_argument('--plotType',  default='timeseries',
                        help='Type of plot: timeseries, ifgram or shaded_relief (Default: timeseries).')
    
    inps = parser.parse_args()
    
    if inps.flag_noseismicity:
       inps.flag_seismicity = False
    del inps.flag_noseismicity

    #inps.argv = iargs if iargs else sys.argv[1:]

    return inps

def is_jupyter():
    jn = True
    try:
        get_ipython()
    except:
        jn = False
    return jn

def main(iargs=None):
    print('iargs:', iargs)
    # inps = cmd_line_parse(iargs)
    inps = create_parser(iargs)

    print('inps:',inps)

###########################################################################################

if __name__ == '__main__':

    if is_jupyter():
       cmd = 'test_parse.py MaunaLoaSenDT87 --plotType ifgram --seismicity'
       cmd = 'test_parse.py MaunaLoaSenDT87 --plotType ifgram --noseismicity'
       cmd = 'test_parse.py MaunaLoaSenDT87'
       cmd = 'test_parse.py --help'

       cmd = cmd.rstrip()
       sys.argv = cmd.split(' ')

    main(sys.argv[1:])
    


# In[104]:


get_ipython().run_line_magic('tb', '')

