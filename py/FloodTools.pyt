#! /usr/bin/env python
# -*- coding: Latin-1 -*-

__revision__ = "--REVISION-- : $Id: FloodTools.pyt 599 2016-10-24 19:27:28Z stolszcz $"

#==============================================================================#
# HISTORY                                                                      #
# -------                                                                      #
# Developed by V. Neufeld, September 2016.                                     #
#==============================================================================#


# Libraries
# =========
import arcpy

# Reload steps required to refresh memory if Catalog is open when changes are made
import FT0_FloodMaster                                    # get module reference for reload
reload(FT0_FloodMaster)                                   # reload step 1
from   FT0_FloodMaster import FT0_FloodMaster             # reload step 2

import FT1_R2ReadOrthoMosaic                              # get module reference for reload
reload(FT1_R2ReadOrthoMosaic)                             # reload step 1
from   FT1_R2ReadOrthoMosaic import FT1_R2ReadOrthoMosaic # reload step 2

import FT2_Scale16to8BitSet                               # get module reference for reload
reload(FT2_Scale16to8BitSet)                              # reload step 1
from   FT2_Scale16to8BitSet import FT2_Scale16to8BitSet   # reload step 2

import FT3_ExtractFloodExtentAndConvertToVector           # get module reference for reload
reload(FT3_ExtractFloodExtentAndConvertToVector)          # reload step 1
from   FT3_ExtractFloodExtentAndConvertToVector \
       import FT3_ExtractFloodExtentAndConvertToVector    # reload step 2

import FT4_FloodVegExtraction                               # get module reference for reload
reload(FT4_FloodVegExtraction)                              # reload step 1
from   FT4_FloodVegExtraction import FT4_FloodVegExtraction     # reload step 2

import FT5_OpenFloodVeg_merge                               # get module reference for reload
reload(FT5_OpenFloodVeg_merge)                              # reload step 1
from   FT5_OpenFloodVeg_merge import FT5_OpenFloodVeg_merge     # reload step 2

# C:\Python27\ArcGISx6410.3\python.exe FloodTools.pyt


class Toolbox(object):
    def __init__(self):
        """
        Part of the Python toolbox template, used to define the tool (tool name
        is the name of the class).

        A Python Toolbox can have more than one tool defined within it.  Each
        will have its own constructor like this that will uniiquely identify it.
        The tools referenced here are contained within external ".py" modules.

        Parameters:
            None


        Return Values:
            None


        Limit(s) and Constraint(s) During Use:
            None
        """
        self.label = "FloodTools"

        # List of tool classes associated with this toolbox
        self.tools = [FT0_FloodMaster,
                      FT1_R2ReadOrthoMosaic,
                      FT2_Scale16to8BitSet,
                      FT3_ExtractFloodExtentAndConvertToVector,
                      FT4_FloodVegExtraction,
                      FT5_OpenFloodVeg_merge]
        self.canRunInBackground = True  # Required for running 64-bit libraries
                                        # from 32-bit ArcCatalog


def main():
	print "In FloodTools.pyt main()..."


if __name__ == '__main__':
    main()