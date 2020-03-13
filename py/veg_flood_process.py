#! C:/Python27/ArcGISx6410.3/python.exe

################################################################################
# Name : veg_flood_process.py
"""
    Module used for derive vegetation flood area products from RADARSAT-2 datasets

    Usage:
        -- Filter data
        -- Scale data from linear to DB
        -- Threshold data
        -- Combine vegetation products
        -- Export resulting flooded vegetation area product as a geotiff

    Limits and constraints:
        This method has only been tested
            -- on RADARSAT-2 standard and wide beam modes.
            -- in the Richelieu region
            -- using the following projection: 'UTM 18 D122'
"""
__revision__ = "--REVISION-- : $Id: veg_flood_process.py 255 2016-07-14 13:00:00Z jbennett $"
################################################################################
# Import public modules
import os
import sys
import string
#from osgeo import gdal
import gdal
from gdalconst import *
import logging
import numpy

#import required PCI Geomatica modules
from pci.fimport import *
from pci.ortho2  import *
from pci.automos import *
from pci.fexport import *
from pci.saringest import *
from pci.fgamma import *
from pci.thr import thr
from pci.pcimod import *
from pci.model import *
from pci.poly2bit import *
from pci.iib import *
from pci.iia import *
from pci.blo import *
from pci.his import *
from pci.nspio import Report, enableDefaultReport
from pci.sarseg import *
from pci.api import datasource as ds
from pci.mas import mas
from pci.map import *
from pci.clr import *
from pci.exceptions import PCIException
from pci.hisdump import *
from pci.grdpol import *

canRunInBackground = True

# Import private modules
import EGS_utility

class VegFloodProcess:
    """
    Class used to derive vegetation flood area products from RADARSAT-2 datasets.

    This class contains the methods required to generate vegetation flood
    area product from RADARSAT-2 datasets.The following functionality is performed by this class.
    -- Filter data
    -- Scale data from linear to DB
    -- Threshold data
    -- Combine vegetation products
    -- Export resulting flooded vegetation area product as a geotiff

    Notes:
        This method has only been tested
            -- on RADARSAT-2 standard and wide beam modes.
            -- in the Richelieu region
            -- using the following projection: 'UTM 18 D122'
    """


    def __init__(self):
        """Initialisation of VegFloodProcess class

        Detailed description

        Parameters:

        """
        self.canRunInBackground = True

    def filter_sar(self, in_file, in_chan = 1, filter_size = 5, num_looks = 4.0):
        """
        SAR image Filter to reduce speckle and also preserve edge

        Remove high-frequency noise (speckle) while preserving high-frequency features (edges).
        The input is a PCIPIX file containing a 32 bit HH imagery. An addition channel is created
        containing the results.

        Note:
            PCI's developers are going to try to add a 'last segment created' (lasc) parameter for
            this function in the next release, thereby enabling cleaner and more reliable automation.

        Parameters:
            in_file -- Input file
            in_chan -- Input channel
            filter_size -- Filter size
            num_looks -- Number of looks

        Return value:
            Newly create channel # when successful, Error statement otherwise.

        Limits and constraints:

        """
        try:
            logging.info('       Executing: VegFloodProcess.filter_sar')
            util = EGS_utility.EGSUtility()
            new_chans = util.add_32_channel(in_file)
            file    =       in_file
            dbic    =       [in_chan]
            dboc    =       [int(new_chans[0])]     # filtered results (overwrite DBIC)
            flsz    =       [filter_size,filter_size]   # filter size
            mask    =       []   # area to filter
            nlook   =       [num_looks]   # number of looks
            imagefmt =      'POW'   # amplitude image format
            fgamma( file, dbic, dboc, flsz, mask, nlook, imagefmt )
            logging.info('          Successfully completed VegFloodProcess.filter_sar: fgamma')
            return new_chans[0]

        except PCIException, e:
            EGS_utility.EGSUtility().error('filter_sar(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('filter_sar(): {:s}'.format(e))


    def scale_sar(self, in_file, in_chan = "3"):
        """
        Scale from linear to DB

        Scale the filtered image from linear to DB. The input is a PCIPIX file containing a
        filtered 32 bit HH imagery. An addition channel is created containing the results.

        Parameters:
            in_file -- Input file
            in_chan -- Input channel


        Return value:
            Newly create channel # when successful, Error statement otherwise.

        Limits and constraints:

        """
        try:
            logging.info('       Executing: VegFloodProcess.scale_sar')
            util = EGS_utility.EGSUtility()
            new_chans = util.add_32_channel(in_file)
            file     =      in_file
            source   =      "%" + new_chans[0] + "= 10*log10(%" + in_chan + ")"
            undefval =      [0]
            model (file, source, undefval)
            logging.info('          Successfully completed VegFloodProcess.scale_sar: model')
            return new_chans[0]

        except PCIException, e:
            EGS_utility.EGSUtility().error('scale_sar(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('scale_sar(): {:s}'.format(e))


    def threshold_values(self, in_file, band = 4, veg_bitmap = 8):
        """
        Calculates open water and flooded vegetation threshold

        Calculates low threshold for open water areas for Edge preservation filter results
        Calculates high threshold for flooded tree areas for Edge preservation filter results
        The input is a PCIPIX file containing a filtered and scaled imagery.
        Bitmaps are added to PCIPIX representing open water and flood vegeatation areas

        Note:
            PCI's developers are going to try to add a 'last segment created' (lasc) parameter for
            this function in the next release, thereby enabling cleaner and more reliable automation.

        Parameters:
            in_file -- Input file
            band -- Input band
            veg_thr -- Minimum threshold for vegetation flooded area
            openwater_thres -- Maximum threshold for open water flooded areas

        Return value:
            Open water and flooded vegetation threshold values when successful,
            Error statement otherwise.

        Limits and constraints:

        """

        try:
            logging.info('       Executing: VegFloodProcess.threshold_values')
            # Find min and max of band

            imstat = EGS_utility.EGSUtility().gdal_stat(in_file,band)
            mean_pixel = imstat[2]
            std_pixel = imstat[3]
            print mean_pixel
            print std_pixel
            #mean_pixel, std_pixel =  EGS_utility.EGSUtility().numpy_stat(in_file,band)
            file    =       in_file
            dbic    =       [band]
            mask    =       [veg_bitmap]     # process under bitmap 9
            hisw    =       []      # no specific histogram window
            hisform =       ''      # default HITCENTER
            #hisdump ( file, dbic, mask, hisw, hisform, imstat )
            print 'ssss'
            print imstat
            print 'fff'
            #raster_his(in_file, band,rep_file)
            logging.info('          Successfully completed VegFloodProcess.threshold_values: thr')
            return [mean_pixel, std_pixel]

        except PCIException, e:
            EGS_utility.EGSUtility().error('threshold_values(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('threshold_values(): {:s}'.format(e))

    def threshold_sar(self, in_file, band = 4, veg_thr = -3.5, openwater_thres = -12.5):
        """
        Threshold high and low

        Apply low threshold for open water areas for Edge preservation filter results
        Apply high threshold for flooded tree areas for Edge preservation filter results
        The input is a PCIPIX file containing a filtered and scaled imagery.
        Bitmaps are added to PCIPIX representing open water and flood vegeatation areas

        Note:
            PCI's developers are going to try to add a 'last segment created' (lasc) parameter for
            this function in the next release, thereby enabling cleaner and more reliable automation.

        Parameters:
            in_file -- Input file
            band -- Input band
            veg_thr -- Minimum threshold for vegetation flooded area
            openwater_thres -- Maximum threshold for open water flooded areas

        Return value:
            Newly create vegetation and open water bitmap segment # when successful,
            Error statement otherwise.

        Limits and constraints:

        """

        try:
            logging.info('       Executing: VegFloodProcess.threshold_sar')
            # Find min and max of band
            imstat = EGS_utility.EGSUtility().gdal_stat(in_file,band)
            max_pixel = imstat[1]
            min_pixel = imstat[0] + 1

            # Create and name newly created segment, 'thr' does not rename segments
            dataset = ds.open_dataset(in_file, ds.eAM_WRITE)
            veg_seg = dataset.create_bitmap() #  Get the number of the newly created bitmap segment
            file=in_file
            dbsl=[veg_seg]
            dbsn="vegflood"
            dbsd="Veg Flood seg"
            mas(file, dbsl, dbsn, dbsd)
            logging.info('          Successfully completed VegFloodProcess.threshold_sar: mas')

            # Threshold for flood vegetation
            file    =       in_file
            dbic    =       [band]
            #dbob    =       []      # create new bitmap
            dbob    =       [veg_seg]
            tval    =       [veg_thr,max_pixel]  # threshold range (min,max)
            comp    =       'OFF'   # threshold values from 9 to 11
            dbsn    =       'vegflood'       # output segment name
            dbsd    =       'Veg Flood seg'     # output segment description
            Report.clear()
            thr( file, dbic, dbob, tval, comp, dbsn, dbsd )
            enableDefaultReport('term')
            logging.info('          Successfully completed VegFloodProcess.threshold_sar: thr')


            # Create and name newly created segment, 'thr' does not rename segments
            water_seg = dataset.create_bitmap() #  Get the number of the newly created bitmap segment
            file=in_file
            dbsl=[water_seg]
            dbsn="openwate"
            dbsd="Open Water seg"
            mas(file, dbsl, dbsn, dbsd)
            logging.info('          Successfully completed VegFloodProcess.threshold_sar: mas')

            # Threshold for open water
            file    =       in_file
            dbic    =       [band]
            #dbob    =       []      # create new bitmap
            dbob    =       [water_seg]
            tval    =       [min_pixel,openwater_thres]  # threshold range (min,max)
            comp    =       'OFF'   # threshold values
            dbsn    =       'openwate'       # output segment name
            dbsd    =       'Open Water seg'     # output segment description
            Report.clear()
            thr( file, dbic, dbob, tval, comp, dbsn, dbsd )
            enableDefaultReport('term')
            logging.info('          Successfully completed VegFloodProcess.threshold_sar: thr')
            return [veg_seg, water_seg]

        except PCIException, e:
            EGS_utility.EGSUtility().error('threshold_sar(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('threshold_sar(): {:s}'.format(e))


    def vegcover2bit(self, in_file, out_file, veg_channel = 4, size_pixel = 10):
        """
        IIA Veg Cover Shapefile to ortho file

        Parameters:
            in_file -- Input file
            out_file -- Output file
            veg_channel -- Vegetation land cover (vector)
            size_pixel -- Pixel size

        Return value:
            Newly create vegetation land cover bitmap segment # when successful,
            Error statement otherwise.

        Limits and constraints:

        """
        try:
            logging.info('       Executing: VegFloodProcess.vegcover2bit')
            util = EGS_utility.EGSUtility()
            bitmap_ids_before = util.bitmap_list(out_file) # Run bitmap_list to get a list of IDs from before poly2bit
            fili    =       in_file
            dbvs    =       [veg_channel]               # polygon layer
            filo    =       out_file
            dbsd    =       ""                 # use default, "Bitmap polygons gridded from vector"
            pixres  =       [size_pixel,size_pixel]  # make 10 meter square pixels
            ftype   =       "PIX"             # output format type
            foptions =      ""                # output options
            Report.clear()
            poly2bit( fili, dbvs, filo, dbsd, pixres, ftype, foptions )
            logging.info('          Successfully completed VegFloodProcess.vegcover2bit: poly2bit')

            enableDefaultReport('term')
            bitmap_ids_after = util.bitmap_list(out_file) # Run bitmap_list to get a list of IDs from after poly2bit
            bit_seg = list(set(bitmap_ids_after)-set(bitmap_ids_before)) # Get the difference between the two lists
            return bit_seg[0]

        except PCIException, e:
            EGS_utility.EGSUtility().error('vegcover2bit(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('vegcover2bit(): {:s}'.format(e))


    def import_vegcover(self, in_file, out_file):
        """
        IIA Veg Cover Shapefile to ortho file

        Parameters:
            in_file -- Input file
            out_file -- Output file

        Return value:
            Error statement if error occurs.

        Limits and constraints:

        """
        try:
            logging.info('       Executing: VegFloodProcess.import_vegcover')
            fili    =       in_file    # input file
            filo    =       out_file      # output file
            dbsl    =       [1]  # input segments to transfer
            dbos    =       []     # overwrite existing segment 1
            iia( fili, filo, dbsl, dbos )
            logging.info('          Successfully completed VegFloodProcess.import_vegcover: iia')

        except PCIException, e:
            EGS_utility.EGSUtility().error('import_vegcover(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('import_vegcover(): {:s}'.format(e))

    def import_vector(self, in_file, out_file):
        """
        IIA Vector Shapefile to ortho file

        Parameters:
            in_file -- Input file
            out_file -- Output file

        Return value:
            Error statement if error occurs.

        Limits and constraints:

        """
        try:
            logging.info('       Executing: VegFloodProcess.import_vector')
            util = EGS_utility.EGSUtility()
            #vector_ids_before = util.vector_list(out_file) # Run vector_list to get a list of IDs

            fili    =       in_file    # input file
            filo    =       out_file      # output file
            dbsl    =       [1]  # input segments to transfer
            dbos    =       []     # overwrite existing segment 1
            iia( fili, filo, dbsl, dbos )
            logging.info('          Successfully completed VegFloodProcess.import_vector: iia')
            #bitmap_ids_after = util.bitmap_list(out_file) # Run bitmap_list to get a list of IDs from after poly2bit
            #vec_seg = list(set(vector_ids_after)-set(vector_ids_before)) # Get the difference between the two lists
            #return vec_seg[0]
        except PCIException, e:
            EGS_utility.EGSUtility().error('import_vector(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('import_vector(): {:s}'.format(e))

    def combine_veglayers(self, in_file, flood_veg = 2, open_water = 3, veg_land_cover = 5):
        """
        Performs bitmap logical operation on bitmaps to created Flood Vegetation layer

        Parameters:
            in_file         -- Input file
            flood_veg       -- Bit segment of detected flood vegetation
            open_water      -- Bit segment of open water
            veg_land_cover  -- Bit segment of Vegetation land cover


        Return value:
            Newly create combined flooded vegetation bitmap segment # when successful,
            Error statement otherwise.

        Limits and constraints:

        """
        try:
            logging.info('       Executing: VegFloodProcess.combine_veglayers')
            file    =   in_file    # input file name
            logfunc =   'OR'            # logical operation
            dbsn    =   'com_fl'         # segment name
            dbsd    =   'Combine Flood'    # segment descriptor
            dbib    =   [flood_veg, open_water] # input bitmaps
            dbob    =   []              # output bitmap
            lasc    =   []
            blo( file, logfunc, dbsn, dbsd, dbib, dbob, lasc )
            logging.info('          Successfully completed VegFloodProcess.combine_veglayers: blo')

            file    =   in_file    # input file name
            logfunc =   'AND'            # logical operation
            dbsn    =   'FVe'         # segment name
            dbsd    =   'Flood Veg'    # segment descriptor
            dbib    =   [veg_land_cover,lasc[0]]          # input bitmaps
            dbob    =   []              # output bitmap
            lasc    =   []
            blo( file, logfunc, dbsn, dbsd, dbib, dbob, lasc )
            logging.info('          Successfully completed VegFloodProcess.combine_veglayers: blo')
            return lasc[0]

        except PCIException, e:
            EGS_utility.EGSUtility().error('combine_veglayers(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('combine_veglayers(): {:s}'.format(e))


    def export_vegflood(self, in_file, out_file, veg_chan):
        """
        Export flooded vegetation as a geotiff

        Parameters:
            in_file  -- Input file
            out_file -- Out file
            veg_chan -- Bit segment of vegetation land cover

        Return value:
            Error statement if error occurs.

        Limits and constraints:

        """
        try:
            os.remove(out_file)
        except OSError:
            pass

        util        =       EGS_utility.EGSUtility()
        new_chans   =       util.add_8_channel(in_file)

        try:
            logging.info('       Executing: VegFloodProcess.export_vegflood')
            file = in_file
            dboc =  [int(new_chans[0])]
            valu =  [0]
            dbow =  []
            clr( file, dboc, valu, dbow )
            logging.info('          Successfully completed VegFloodProcess.export_vegflood: clr')

            file = in_file
            dbib = [veg_chan]      # Select bitmaps for encoding
            dboc = [int(new_chans[0])]      # Select channel to be encoded
            valu = [1]    # Specify gray level values
            map( in_file, dbib, valu, dboc )
            logging.info('          Successfully completed VegFloodProcess.export_vegflood: map')

            fili    =       in_file
            filo    =       out_file
            dbiw    =       []
            dbic    =       [int(new_chans[0])]
            dbib    =       []
            dbvs    =       []
            dblut   =       []
            dbpct   =       []
            ftype   =       "tif"
            foptions        = ""
            fexport( fili, filo, dbiw, dbic, dbib, dbvs, dblut, dbpct, ftype, foptions )
            logging.info('          Successfully completed VegFloodProcess.export_vegflood: fexport')

        except PCIException, e:
            EGS_utility.EGSUtility().error('export_vegflood(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('export_vegflood(): {:s}'.format(e))

