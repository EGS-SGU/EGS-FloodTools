#####################################################################################################################################
# Name : ortho_mosaic.py
"""
Module used to import, orthorectify, mosaic and export of radarsat images

    Usage:
        -- import RADARSAT-2 data
        -- orthorectification 
        -- mosaic
        -- export

    Limit(s) and constraint(s):

"""
__revision__ = "--REVISION-- : $Id: ortho_mosaic.py 219 255 2016-04-06 13:00:00Z jbennett $"
#####################################################################################################################################
# Public modules
import logging

#import required PCI Geomatica modules
from pci.fimport import *
from pci.ortho2  import *
from pci.automos import *
from pci.fexport import *
from pci.nspio import Report, enableDefaultReport
from pci.saringest import *
from pci.exceptions import PCIException

# Import private modules
import EGS_utility

class OrthoMosaic():
    """
    Class used to import, orthorectify, mosaic and export of radarsat images

    Detailed description


    """

    def __init__ (self):
        """Initialisation of OrthoMosaic class

        Detailed description

        Parameters:

        """


    def import_file(self, in_file, out_file):
        """
        Import Image and auxiliary information

        Detailed description
            Imports the image and all auxiliary information from a source file
            to a newly created PCIDSK file
        Parameters:
            in_file  -- Input file
            out_file -- Output file

        Return value:
            Error statement if error occurs.

        Limits and constraints:
        
        """
        try:
            logging.info('       Executing: OrthoMosaic.import_file')
            dbiw = []
            poption = "NEAR"
            dblayout = "BAND"
            fimport(in_file, out_file, dbiw, poption, dblayout)
            logging.info('          Successfully completed OrthoMosaic.import_file: fimport')
        
        except PCIException, e:
            EGS_utility.EGSUtility().error('import_file(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('import_file(): {:s}'.format(e))       


    def import_sar(self, in_file, out_file):
        """
        Import RADARSAT-2 SIGMA data

        Import RADARSAT-2 imagery and metadata into PCIPIX format. Outputs 
        32 bit HH imagery along with associated metadata to PCIPIX file

        Notes:
            This method has only been tested on RADARSAT-2 standard and wide beam modes.

        Parameters:
            in_file -- Input file
            out_file -- Output file

        Return value:
            Error statement if error occurs.

        """
        try:
            logging.info('       Executing: OrthoMosaic.import_sar')
            fili    =       in_file
            filo    =       out_file
            dbiw    =       []
            poption =       'NEAR'
            dblayout =      'BAND'
            calibtyp =      'SIGMA'
            saringest(fili, filo, dbiw, poption, dblayout, calibtyp)
            logging.info('          Successfully completed OrthoMosaic.import_sar: saringest')

        except PCIException, e:
            EGS_utility.EGSUtility().error('import_sar(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('import_sar(): {:s}'.format(e)) 

    
    def orthorectify(self, in_file, out_file, DEM, pixelSpacing_x,pixelSpacing_y, proj):
        """
        Method for orthorectification of radarsat2 image

        Orthorectify RADARSAT-2 imagery contained in a PCIPIX file.
        Outputs the Orthorectified results into a newly created PCIPIX file

        Parameters:
            in_file         -- Input file
            out_file        -- Output file
            DEM             -- DEM file
            pixelSpacing_x  -- x pixel spacing
            pixelSpacing_x  -- y pixel spacing
            proj            -- data projection

        Return value:
            Error statement if error occurs.

        Limits and constraints:
        
        """

        try:    
            logging.info('       Executing: OrthoMosaic.orthorectify')
            mfile       = in_file                   # Input image file name
            dbic        = [1,2]                     # input HH + incidence angle channels
            mmseg       = [3]                       # use the last math segment
            dbiw        = []                        # Use all image
            srcbgd      = "NONE"
            filo        = out_file                  # Uses the default file name
            ftype       = "PIX"                     # Use the PCIDSK format
            foptions    = "BAND"
            outbgd      = [0]
            ulx         = ''                            
            uly         = ''
            lrx         = ''
            lry         = ''
            edgeclip    = [0]                         
            tipostrn    = ""
            mapunits    = proj
            bxpxsz      = str(pixelSpacing_x)
            bypxsz      = str(pixelSpacing_y)
            filedem     = DEM                    
            dbec        = [1]                    
            backelev    = []
            elevref     = ""
            elevunit    = "METER"
            elfactor    = []                        # Specifies the offset only
            proc        = ""
            sampling    = [4]                       # Ortho correction is computed for every pixel
            resample    = "BILIN"              
            Report.clear() 
            ortho2(mfile, dbic, mmseg, dbiw, srcbgd, filo,  ftype,
                   foptions, outbgd, ulx, uly, lrx, lry, edgeclip, tipostrn, mapunits, bxpxsz, bypxsz, filedem, dbec,
                   backelev, elevref, elevunit, elfactor, proc, sampling, resample)
            enableDefaultReport('term') 
            logging.info('          Successfully completed OrthoMosaic.orthorectify: ortho2')

        except PCIException, e:
            EGS_utility.EGSUtility().error('orthorectify(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('orthorectify(): {:s}'.format(e)) 
        

    def mosaic(self, in_dir, out_file):
        """Method for mosaic of radarsat2 image

        Detailed description
        Creates image mosaic from a set of georeferenced images

        Parameters:
            in_dir         -- Input directory
            out_file        -- Output file

        Return value:
            Error statement if error occurs.
            
        Limits and constraints:
        
        """
        try:
            logging.info('       Executing: OrthoMosaic.mosaic')
            mfile       = in_dir
            dbiclist    ="1,2"
            mostype     ="FULL"
            filo        = out_file
            ftype       ="PIX"
            foptions    ="BAND"
            clrmos      ="YES"
            startimg    =""
            radiocor    ="NONE"
            balmthd     ="NONE"
            balopt      =[0]
            fili_ref    =""
            loclmask    ="NONE"
            globfile    =""
            globmask    =[]
            cutmthd     ="ENTIRE"
            filvin      =""
            dbiv        =[0]
            filvout     = ""
            dbov        =[0]
            dbluto      =""
            blenc       =[0]
            backval     =[0.0]
            tempdir     =""
            
            automos(mfile, dbiclist, mostype, file, ftype, foptions, clrmos, startimg, radiocor, balmthd, balopt,
                    fili_ref, loclmask, globfile, globmask, cutmthd, filvin, dbiv, filvout,
                    dbov, dbluto, blenc, backval, tempdir)
            logging.info('          Successfully completed OrthoMosaic.mosaic: automos')

        except PCIException, e:
            EGS_utility.EGSUtility().error('mosaic(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('mosaic(): {:s}'.format(e)) 


    def export_file(self, in_file, out_file, ftype, foption):
        """
        Exports image data

        Detailed description
            Transfers the specified image and auxiliary information from a source file
            to an output file of a different data type

        Parameters:
            in_file     -- Input file
            out_file    -- Output file
            ftype       -- Specifies the file format for the new output file
            foption     -- Specifies the file creation options


        Return value:
            Error statement if error occurs.
            
        Limits and constraints:
        
        """
        try:
            logging.info('       Executing: OrthoMosaic.export_file')            
            fili     = in_file
            filo     = out_file
            dbiw     = []
            dbic     = [1,2]
            dbib     = []
            dbvs     = []
            dblut    = []
            dbpct    = []
            ftype    = ftype
            foptions = foption
            fexport(fili, filo, dbiw, dbic, dbib, dbvs, dblut, dbpct, ftype, foptions)
            logging.info('          Successfully completed OrthoMosaic.export_file: fexport')

        except PCIException, e:
            EGS_utility.EGSUtility().error('export_file(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('export_file(): {:s}'.format(e)) 

            
    def sarseg_EGS(self, in_file):
        """
        Segment SAR image

       Detailed description
            Segments a SAR image into regions using an algorithm based on the RGW image segmentation algorithm. 
            Segmentation seeks to overcome speckle by identifying regions of constant backscatter.
        Parameters:
            in_file     -- Input file

        Return value:
            Error statement if error occurs.
            
        Limits and constraints:

        """
        try:
            logging.info('       Executing: OrthoMosaic.sarseg_EGS')            
            file    =       in_file
            dbicim  =       [1]     # use calibrated sigma-nought intensity from ch3
            dbocseg =       [2]     # store segment IDs into channel 4
            dbocwrk =       [3]     # store segment means into channel 5
            maxiter =       []      # disregard number of iterations
            edgthr  =       []      # use default value of 4.6
            sobthr  =       []      # use default value of 0
            dosrd   =       ""      # detect small regions
            sthresh =       []      # include regions of any size
            sarseg (file, dbicim, dbocseg, dbocwrk, maxiter, edgthr, sobthr, dosrd, sthresh )
            logging.info('          Successfully completed OrthoMosaic.sarseg_EGS: sarseg')

        except PCIException, e:
            EGS_utility.EGSUtility().error('sarseg_EGS(): {:s}'.format(e))
        except ValueError as e:
            EGS_utility.EGSUtility().error('sarseg_EGS(): {:s}'.format(e)) 