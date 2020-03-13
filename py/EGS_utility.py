#! C:/Pythons27/ArcGISx6410.3/python.exe

################################################################################
# Name : EGS_utility.py
"""
    Module containing utilities that are required for EGS processing of RADARSAT-2 imagery.

    Usage:
        -- Creates a list of the channel numbers for a specified PCIPIX file
        -- Compares two lists of channels and determines the difference
        -- Add 8 bit channel to PCIPIX file.
        -- Add 32 bit channel to PCIPIX file.
        -- Get geotransform within file.
        -- Logs differences in vector files
        -- Logs differences in raster files
        -- Logs histogram
        -- Setup logger
        -- Issue error message.
    Limits and constraints:

"""
__revision__ = "--REVISION-- : $Id: EGS_utility.py 255 2016-07-14 13:00:00Z jbennett $"
################################################################################

# Import public modules
import os
import sys

import logging
import ConfigParser


#import arcpy


#import required PCI Geomatica modules

##from pci.api import datasource as ds
##from pci.pcimod import pcimod
##from pci.exceptions import PCIException
##from pci.his import *
##from pci.nspio import Report, enableDefaultReport
##from osgeo import gdal, ogr, osr
##from gdalconst import *
##import numpy



class EGSUtility:
    """
    Class containing methods for EGS processing.

    This class contains methods that are used by EGS processing.
    The following functionality is performed by this class.
    -- Creates a list of the channel numbers for a specified PCIPIX file
    -- Compares two lists of channels and determines the difference
    -- Add 8 bit channel to PCIPIX file.
    -- Add 32 bit channel to PCIPIX file.
    -- Get geotransform within file.
    -- Logs differences in vector files
    -- Logs differences in raster files
    -- Logs histogram
    -- Setup logger
    -- Issue error message.

    Notes:
         PCI's developers are going to try to add a 'last segment created' (lasc)
         parameter for several required functions in the next release,
         thereby enabling cleaner and more reliable automation.
         Until this happens, several functions within this class act as a
         substitute.

    """


    def __init__(self):
        """Initialisation of EGSUtility class

        Detailed description

        Parameters:

        """
        self.canRunInBackground = True



    def bitmap_list(self, in_file): # This function opens the dataset and gets a list of bitmap ids
        """
        Creates a list of the bitmap IDs

        Note:
            PCI's developers are going to try to add a 'last segment created' (lasc) parameter for
            this function in the next release, thereby enabling cleaner and more reliable automation.

        Parameters:
            in_file -- Input file

        Return value:
            Bitmap list # when successful, Error statement otherwise.

        Limits and constraints:

        """
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
##        from gdalconst import *
        import numpy

        try:
            logging.info('          Executing: EGSUtility.bitmap_list')
            dataset = ds.open_dataset(in_file, ds.eAM_WRITE)
            return dataset.bitmap_ids

        except PCIException, e:
            self.error('bitmap_list(): {:s}'.format(e))
        except ValueError as e:
            self.error('bitmap_list(): {:s}'.format(e))


    def vector_list(self, in_file): # This function opens the dataset and gets a list of vector ids
        """
        Creates a list of the vector IDs

        Note:
            PCI's developers are going to try to add a 'last segment created' (lasc) parameter for
            this function in the next release, thereby enabling cleaner and more reliable automation.

        Parameters:
            in_file -- Input file

        Return value:
            Vector list # when successful, Error statement otherwise.

        Limits and constraints:

        """

        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
##        from gdalconst import *
        import numpy

        try:
            logging.info('          Executing: EGSUtility.vector_list')
            dataset = ds.open_dataset(in_file, ds.eAM_WRITE)
            return dataset.get_vector_io_ids

        except PCIException, e:
            self.error('vector_list(): {:s}'.format(e))
        except ValueError as e:
            self.error('vector_list(): {:s}'.format(e))

    def create_chan_list(self, in_file):
        """
        Creates a list of the channel numbers and their associated descriptions

        Note:
            PCI's developers are going to try to add a 'last segment created' (lasc) parameter for
            this function in the next release, thereby enabling cleaner and more reliable automation.

        Parameters:
            in_file -- Input file

        Return value:
            Channel list # when successful, Error statement otherwise.

        Limits and constraints:

        """
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
##        from gdalconst import *
        import numpy

        try:
            logging.info('          Executing: EGSUtility.create_chan_list')
            pix = ds.open_dataset(in_file, ds.eAM_WRITE)

            # Read metadata from file
            aux_pix = pix.aux_data

            # Get number of channels
            chans = aux_pix.chan_count
            i = 1
            chan_list = []

            while i <= chans:
                chan_desc = aux_pix.get_chan_description(i)
                list_update = str(i) + "-" +chan_desc
                chan_list.append(list_update)
                i += 1
            return chan_list

        except PCIException, e:
            self.error('create_chan_list(): {:s}'.format(e))
        except ValueError as e:
            self.error('create_chan_list(): {:s}'.format(e))


    def compare_list(self, list_before, list_after):
        """
        Compares two lists of channels and determines the difference.
        It then returns the channel number of the newly added channel

        Note:
            PCI's developers are going to try to add a 'last segment created' (lasc) parameter for
            this function in the next release, thereby enabling cleaner and more reliable automation.

        Parameters:
            list_before -- Channels before
            list_after -- Channels after

        Return value:
            Newly created channel number, error statement otherwise.

        Limits and constraints:

        """
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
##        from gdalconst import *
        import numpy

        try:
            logging.info('          Executing: EGSUtility.compare_list')
            new_chans = []
            for b1, a1 in map(None, list_after, list_before):
                    if b1 != a1:
                        new_chans.append(b1.split("-",1)[0])
            return new_chans

        except PCIException, e:
            self.error('compare_list(): {:s}'.format(e))
        except ValueError as e:
            self.error('compare_list(): {:s}'.format(e))


    def add_8_channel(self, in_file):
        """
        Add 8 bit channel to file

        Note:
            PCI's developers are going to try to add a 'last segment created' (lasc) parameter for
            this function in the next release, thereby enabling cleaner and more reliable automation.

        Parameters:
            in_file -- Input file

        Return value:
            Newly created channel number, error statement otherwise.

        Limits and constraints:

        """
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
##        from gdalconst import *
        import numpy

        try:
            logging.info('          Executing: EGSUtility.add_8_channel')
            file    =       in_file
            pciop   =       'ADD'
            pcival  =       [1,0,0,0]
            list_before = self.create_chan_list(in_file)  # Create the list of channels before running pcimod
            pcimod(file, pciop, pcival)
            list_after = self.create_chan_list(in_file)  # Create the list of channels after running pcimod
            new_chans = self.compare_list(list_before, list_after)  # Compare the list from before and after running pcimod
            return new_chans

        except PCIException, e:
            self.error('add_8_channel(): {:s}'.format(e))
        except ValueError as e:
            self.error('add_8_channel(): {:s}'.format(e))


    def add_32_channel(self, in_file):
        """
        Add 8 bit channel to file

        Note:
            PCI's developers are going to try to add a 'last segment created' (lasc) parameter for
            this function in the next release, thereby enabling cleaner and more reliable automation.

        Parameters:
            in_file -- Input file

        Return value:
            Newly created channel number, error statement otherwise.

        Limits and constraints:

        """
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
##        from gdalconst import *
        import numpy

        try:
            logging.info('          Executing: EGSUtility.add_32_channel')
            file    =       in_file
            pciop   =       'ADD'
            pcival  =       [0,0,0,1]
            list_before = self.create_chan_list(in_file)  # Create the list of channels before running pcimod
            pcimod(file, pciop, pcival)
            list_after = self.create_chan_list(in_file)  # Create the list of channels after running pcimod
            new_chans = self.compare_list(list_before, list_after)  # Compare the list from before and after running pcimod
            return new_chans

        except PCIException, e:
            self.error('add_32_channel(): {:s}'.format(e))
        except ValueError as e:
            self.error('add_32_channel(): {:s}'.format(e))


    def numpy_stat(self, in_file, band_num):
        """
        Get Statistics on band within file

        Parameters:
            in_file  -- Input file
            band_num -- Band to obtain stats

        Return value:
            Statistics on band within file, error statement otherwise.
        """
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
##        from gdalconst import *
        import numpy

        try:
            logging.info('          Executing: EGSUtility.numpy_stat')
            stats = []
            src_ds = gdal.Open(in_file, GA_Update) # should be GA_ReadOnly , test
            if src_ds is None:
                logging.error('          Unable to open: ' + in_file)
                sys.exit(1)
            srcband = src_ds.GetRasterBand(band_num)
            if srcband is None:
                logging.error('          No band #: ', band_num)
            stats = srcband.GetStatistics( True, True )
            if stats is None:
                logging.error('          No stats for band # ', band_num)
            #b1 = BandReadAsArray(srcband)
            #return (numpy.mean(b1), numpy.std(b1))
        except ValueError as e:
            self.error('numpy_stat(): {:s}'.format(e))


    def gdal_stat(self, in_file, band_num):
        """
        Get Statistics on band within file

        Parameters:
            in_file  -- Input file
            band_num -- Band to obtain stats

        Return value:
            Statistics on band within file, error statement otherwise.
        """
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
        from gdalconst import GA_Update
        import numpy

        try:
            logging.info('          Executing: EGSUtility.gdal_stat')
            stats = []
            src_ds = gdal.Open(in_file, GA_Update) # should be GA_ReadOnly , test
            if src_ds is None:
                logging.error('          Unable to open: ' + in_file)
                sys.exit(1)
            srcband = src_ds.GetRasterBand(band_num)
            if srcband is None:
                logging.error('          No band #: ', band_num)
            stats = srcband.GetStatistics( True, True )
            if stats is None:
                logging.error('          No stats for band # ', band_num)
            return (stats)

        except ValueError as e:
            self.error('gdal_stat(): {:s}'.format(e))


    def gdal_geotransform(self, in_file):
        """
        Get geotransform within file

        Parameters:
            in_file -- Input file

        Return value:
            geotransform of file, error statement otherwise.
        """
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
        from gdalconst import GA_Update
        import numpy

        try:
            logging.info('          Executing: EGSUtility.gdal_geotransform')
            stats = []
            src_ds = gdal.Open(in_file, GA_Update) # should be GA_ReadOnly , test
            if src_ds is None:
                logging.error('          Unable to open: ' + in_file)
                sys.exit(1)
            geotransform = src_ds.GetGeoTransform()
            pixelwidth = geotransform[1]
            return (geotransform)

        except ValueError as e:
            self.error('gdal_geotransform(): {:s}'.format(e))

    def test_vector(self, ref_file, in_file,rep_file):
        """
        Logs differences in vector files.

        Parameters:
            ref_file -- reference vector file
            in_file  -- input vector file
            rep_file -- report file
        Return value:
            Logs resulting difference in vector files, error statement otherwise.
        """
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
##        from gdalconst import *
        import numpy
        import arcpy

        try:
            logging.info('')
            logging.info('          Executing: EGSUtility.test_vector')
            logging.info('          Compare ref: ' + ref_file)
            logging.info('          Compare product: ' + in_file)
            logging.info('          Report file: ' + rep_file)
            if os.path.exists(rep_file):
                os.remove(rep_file)
            arcpy.FeatureCompare_management(ref_file, in_file, 'FID', 'ALL', '', '', 0, 0,\
                                          '', '', 'CONTINUE_COMPARE', rep_file)

            # open results file, output results to log file
            with open(rep_file) as infile:
                for line in infile:
                    logging.info(line)
                infile.close()

        except ValueError as e:
            self.error('test_vector(): {:s}'.format(e))

    def test_raster(self, ref_file, in_file, rep_file):
        """
        Logs differences in raster files.

        Parameters:
            ref_file -- reference raster file
            in_file  -- input raster file
            rep_file -- report file

        Return value:
            Logs resulting difference in raster files, error statement otherwise.
        """

        try:
            logging.info('')
            logging.info('          Executing: EGSUtility.test_raster')
            logging.info('          Compare ref: ' + ref_file)
            logging.info('          Compare product: ' + in_file)
            logging.info('          Report file: ' + rep_file)
            if os.path.exists(rep_file):
                os.remove(rep_file)
            arcpy.CalculateStatistics_management(ref_file, "", "", "",\
                                     "SKIP_EXISTING")
            arcpy.CalculateStatistics_management(in_file, "", "", "",\
                                     "SKIP_EXISTING")
            arcpy.RasterCompare_management(ref_file,in_file,"RASTER_DATASET",\
                          "","CONTINUE_COMPARE",rep_file,"","","")

            # open results file, output results to log file
            with open(rep_file) as infile:
                for line in infile:
                    logging.info(line)
                infile.close()

        except ValueError as e:
            self.error('test_raster(): {:s}'.format(e))

    def raster_his(self, in_file, band, mask, rep_file):
        """
        Logs histogram.

        Parameters:
            in_file  -- input file
            band     -- band
            rep_file -- report file
        Return value:
            Logs histogram for input raster image, error statement otherwise.
        """
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
        from pci.his import his
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
##        from gdalconst import *
        import numpy

        try:
            logging.info('')
            logging.info('          Executing: EGSUtility.raster_his')
            logging.info('          Compare product: ' + in_file)
            logging.info('          Band: ' + str(band))
            if os.path.exists(rep_file):
                os.remove(rep_file)
            file    =       in_file
            dbic    =       [band]     # 8-bit unsigned
            gmod    =       'ON'    # show graphic mode
            cmod    =       'OFF'   # no cumulative mode
            pcmo    =       'OFF'   # no percentage mode
            nsam    =       []      # no number of samples
            trim    =       []      # no trimming
            hisw    =       []      # no specific histogram window
            mask    =       [mask]      # process entire image
            imstat_list = []
            imstat = imstat_list
            Report.clear()
            enableDefaultReport(rep_file)
            his( file, dbic, gmod, cmod, pcmo, nsam, trim, hisw, mask, imstat)
            enableDefaultReport('term') # this will close the report file
            # open results file, output results to log file
            #with open(rep_file) as infile:
            #    for line in infile:
            #        logging.info(line)
            #    infile.close()
            #logging.info(imstat)
            return imstat
        except PCIException, e:
            self.error('raster_his(): {:s}'.format(e))
        except ValueError as e:
            self.error('raster_his(): {:s}'.format(e))

    def setup_logger(self, in_file, verbose):
        """
        Setup logging information

        Setup logging information so it is written to the log file and the console

        Parameters:
            in_file -- Input file
            level   -- Level of log detail

        Return value:
            Error statement if error occurs.

        Limits and constraints:

        """

        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
##        from pci.his import *
        from pci.nspio import Report, enableDefaultReport
        from osgeo import gdal, ogr, osr
##        from gdalconst import *
        import numpy

        try:
            logging.basicConfig(filename=in_file,level=logging.DEBUG)
            if verbose:
                console = logging.StreamHandler()
                console.setLevel(logging.INFO)
                formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
                console.setFormatter(formatter)
                logging.getLogger('').addHandler(console)

        except ValueError as e:
            self.error('setup_logger(): {:s}'.format(e))

    def error(self, msg):
        '''Issue error message'''
        # Experimental stuff on the subject of the best communication strategy
        # between this module (the 'library')

        # Case 1: arcpy.AddError() + sys.exit()
        #    AddError() does not stop execution, and sys.exit() is not clean conceptually
        # arcpy.AddError(msg)
        # sys.exit(1)

        # Case 2: arcpy.ExecuteError()
        #    Works, but probably not ideal conceptually: perhaps ExecuteError is best reserved
        #    for geoprocessing errors only (i.e. those that happen when running Arc built-in tools, e.g. Buffer)?
        # raise arcpy.ExecuteError(msg)

        # Case 3: via exception (use a dedicated exception class?)
        #raise ValueError(msg)
        logging.debug('      ' + msg)