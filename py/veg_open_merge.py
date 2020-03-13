#! C:/Pythons27/ArcGISx6410.3/python.exe

################################################################################
# Name : veg_open_merge.py
"""
    Module used to merge the flooded vegetation and open water products

    Usage:
        -- Import flooded vegetation
        -- Import open water
        -- Merge products
        -- Filter to remove small holes and areas
        -- Export resulting merged flooded area product as a geotiff

    Limits and constraints:
        This method has only been tested
            -- in the Richelieu region
            -- using the following projection: 'UTM 18 D122'
"""
__revision__ = "--REVISION-- : $Id: veg_open_merge.py 255 2016-07-14 13:00:00Z jbennett $"
################################################################################
# Import public modules
import os
import sys
import string
import logging

import arcpy


# Import private modules
import EGS_utility

class MergeProcess:
    """
    Class used to merge the flooded vegetation and open water products.

    This class contains the methods required to generate a merged product from the flooded
    vegetation and open water products.
    The following functionality is performed by this class.
    -- Import flooded vegetation and open water products into a PCIPIX file
    -- Merge products
    -- Filter to remove small holes and areas
    -- Export resulting merged flooded area product as a geotiff

    Notes:
        This method has only been tested
            -- in the Richelieu region
            -- using the following projection: 'UTM 18 D122'
    """


    def __init__(self):
        """Initialisation of MergeProcess class

        Detailed description

        Parameters:

        """
        self.canRunInBackground = True

    def merge_filter_export(self, in_file, in_file2, out_file, out_file2, out_file3, hole_size):
        """
        Imports, merges, filters and exports flooded products.

        Import flood products into PCIPIX format, merge products, filters to remove holes / areas.
        Outputs resulting products as compressed geotif and shapefile.

        Merges image value polygons smaller than a user-specified
        threshold with the largest neighboring polygon

        Parameters:
            in_file    -- Input file1
            in_file2   -- Input file2
            out_file   -- Working PCIPIX file
            out_file2  -- Resuling output geotif
            hole_size  -- threshold for filter (hectares)

        Return value:
            Error statement if error occurs.

        """

        #import required PCI Geomatica modules
        import pci
        from pci.sieve import *
        from pci.fimport import *
        from pci.fexport import *
        from pci.thmrovr import *
        from pci.mosaic import *
        from pci.thmrmer import *
        from pci.model import *
        from pci.nspio import Report, enableDefaultReport
        from pci.exceptions import PCIException
        from pci.ras2poly import *
        import arcpy
        from osgeo import gdal, ogr, osr
        from gdalconst import GA_Update

        try:
            util        =       EGS_utility.EGSUtility()

            #Import first image (flooded vegetation) into PCIPIX file
            logging.info('       Executing: MergeProcess.merge_filter_export')
            fili        =       in_file
            filo        =       out_file
            dbiw        =       []
            poption     =       ""
            dblayout    =       ""           #Defaults to "BAND"
            Report.clear()
            fimport(fili, filo, dbiw, poption, dblayout)
            enableDefaultReport('term')
            logging.info('          Successfully completed MergeProcess.merge_filter_export: fimport')

            #Import second image (open water) into PCIPIX file
            new_chans   =       EGS_utility.EGSUtility().add_8_channel(out_file)
            fili        =       in_file2
            dbic        =       [1]     # use channel 1
            dbvs        =       []      # default, no cutline defined
            dblut       =       []      # default, no lookup table
            filo        =       out_file
            dboc        =       [int(new_chans[0])]     # overwrite channel 1
            blend       =       []      # default, no blending
            backval     =       []      # default, 0
            mosaic( fili, dbic, dbvs, dblut, filo, dboc, blend, backval )
            logging.info('          Successfully completed MergeProcess.merge_filter_export: mosaic')

            # Convert values using MODEL so 255 = 0
            file        =       out_file
            source_model = """if (%2 = 255) then
                                        %2 = 0
                                        endif"""
            model( file, source=source_model)

            #Merge two image together, possible use thmrovr for one step instead of two
            merge_chan  =       util.add_8_channel(out_file)
            fili        =       out_file    # input file
            filo        =       out_file    # output file will be created
            dbic        =       [1,int(new_chans[0])]   # input thematic raster channels
            dbib        =       []      # no bitmap mask
            dboc        =       [int(merge_chan[0])]
            omethod     =       "UNION"      # default, "UNION"
            thmrovr( fili, filo, dbic, dbib, dboc, omethod )
            logging.info('          Successfully completed MergeProcess.merge_filter_export: thmrovr')

            # Combine values using MODEL so zero = not flooded, 255 = flooded
            file        =       out_file
            source_model = """if (%3 >= 1) then
                                        %3 = 255
                                        endif"""
            model( file, source=source_model)

            #Determine filter size as pixel number
            filtered_chan   =       util.add_8_channel(out_file)
            pixelwidth      =       util.gdal_geotransform(out_file)[1]
            pixelheight      =      util.gdal_geotransform(out_file)[5]
            logging.info('          pixelwidth: ' + str(pixelwidth))
            logging.info('          pixelheight: ' + str(pixelheight))
            num_pixel       =       int((hole_size * 10000)/abs(pixelwidth *  pixelheight)) # hole_size is in hectares
            logging.info('          Number of pixels for threshold hole size: ' + str(num_pixel))

            #Filter in order to remove holes
            file        =       out_file
            dbic        =       [int(merge_chan[0])]
            dboc        =       [int(filtered_chan[0])]
            sthresh     =       [num_pixel]     # polygon size threshold in
            keepvalu    =       []      # no keep value
            connect     =       []      # default, 4-connection
            sieve( file, dbic, dboc, sthresh, keepvalu, connect )
            logging.info('          Successfully completed MergeProcess.merge_filter_export: sieve')
            #EGS_utility.EGSUtility().raster_his(out_file,int(filtered_chan[0]))

            #Export resulting product as a geotif
            fili        =       out_file
            filo        =       out_file2
            dbiw        =       []
            dbic        =       [int(filtered_chan[0])]
            dbib        =       []
            dbvs        =       []
            dblut       =       []
            dbpct       =       []
            ftype       =       "tif"
            foptions    =       "LZW"
            fexport( fili, filo, dbiw, dbic, dbib, dbvs, dblut, dbpct, ftype, foptions )
            logging.info('          Successfully completed MergeProcess.merge_filter_export: fexport')

            fili     = out_file         # input raster file
            dbic     = [int(filtered_chan[0])] # using channel 6 from irvine.pix
            filo     = out_file         # output file to be created
            smoothv  = ""               # default, YES vectors are smoothed
            dbsd     = ""               # defaults to "Created from Raster"
            ftype    = ""               # default, PIX
            foptions = ""               # output format options
            ras2poly(fili, dbic, filo, smoothv, dbsd, ftype, foptions)
            logging.info('          Successfully completed MergeProcess.merge_filter_export: ras2poly')

            # Export resulting product as a shapefile
            # PCI creates shapefile with projection 'UTM 18 S E008 ', compared to 'UTM 18 T D122'
            # These projections are the same projection, as E008 is the ellipsoid used by NAD 1983.
            # but opted for arcpy export
            fili        =       out_file
            filo        =       out_file3
            dbiw        =       []
            dbic        =       []
            dbib        =       []
            dbvs        =       [3]
            dblut       =       []
            dbpct       =       []
            ftype       =       "shp"
            foptions    =       ""
            #fexport( fili, filo, dbiw, dbic, dbib, dbvs, dblut, dbpct, ftype, foptions )
            arcpy.RasterToPolygon_conversion(out_file2, out_file3, "NO_SIMPLIFY", "")
            logging.info('          Successfully completed MergeProcess.merge_filter_export: arcpy.RasterToPolygon_conversion')


        except PCIException, e:
            EGS_utility.EGSUtility().error('merge_filter_export(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('merge_filter_export(): {:s}'.format(e))


