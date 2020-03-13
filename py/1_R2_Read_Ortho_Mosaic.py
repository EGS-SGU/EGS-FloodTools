import os
import sys
import string
import glob
import zipfile
import arcview
import arcpy
from arcpy import env

#	2-fold modifications from 2013 version:
#	  changes to run  under GEomatica 2015, mainly ORTHO to ORTHO2
#	  directly call PCI functions from python, rather than indirectly from EASI
#

arcpy.AddMessage("Python Version: "+ sys.version)

from pci.fimport import *
from pci.ortho2  import *
from pci.automos import *
from pci.fexport import *
from pci.automos import *


mode = arcpy.ProductInfo()
arcpy.AddMessage('Current Product License: ' + mode)    

# --------------------------------------------------------------------------
#  define environmental variable WORKFLOW_DATA to point to root directory
#  e.g.  set WORKFLOW_DATA=F:\EMERG\Tests_RD\George\2012_Tools\bat_files\
# --------------------------------------------------------------------------
WORKFLOW_DATA = arcpy.env.workspace
arcpy.AddMessage(WORKFLOW_DATA)
scriptPath=WORKFLOW_DATA + "\\"
arcpy.AddMessage( 'Script Path ' + scriptPath )
inMapCoord = arcpy.GetParameterAsText(2)
inDEMfile  = arcpy.GetParameterAsText(3)
#inNumLooks = arcpy.GetParameterAsText(4)
#inPixSpacing = arcpy.GetParameterAsText(5)
inPixSpacing = arcpy.GetParameterAsText(4)

#-------------------------------------------------------------------------
#                 Copy and unzip RS2 data segments to RAW folder
#-------------------------------------------------------------------------

ZipFolder = arcpy.GetParameterAsText(0)	                # Source directory with zipped data products
arcpy.AddMessage('Zipfolder: ' + ZipFolder)
#ListZipFiles = glob.glob(os.path.join(ZipFolder, '*'))	# Create list of zip files to process
ListZipFiles = glob.glob(os.path.join(ZipFolder, '*.zip'))	# Create list of zip files to process
ExtractDir = arcpy.GetParameterAsText(1)                # Target directory for unzipped files

for files in ListZipFiles:

    ZipFilePath = files		# the path for each zip file

#if...else statement: if unzipped file already exists in output directory, extraction will not be executed.
#                     Otherwise, zip files will be unzipped.
    if os.path.exists(os.path.join(ExtractDir, os.path.splitext(os.path.basename(ZipFilePath))[0])) == True:
        arcpy.AddMessage("File " + "'" + os.path.splitext(os.path.basename(ZipFilePath))[0] + "'" + " already exists.")

    else:
        arcpy.AddMessage('zipfilePath: ' + ZipFilePath)
        File = zipfile.ZipFile(ZipFilePath)
        File.extractall(ExtractDir)
        arcpy.AddMessage("File " + "'" + os.path.basename(ZipFilePath) + "'" + " has been unzipped.")
        File.close()                                    # essential to close file if you want to delete it
# --------        os.remove(ZipFilePath)                          # delete zip file to conserve disk space

#arcpy.AddMessage("All files unzipped.")


os.chdir(scriptPath)

scriptPathRaw = scriptPath + 'Raw\\'
scriptPathRaw = os.path.join(arcpy.env.workspace,'Raw\\')
listD = os.listdir(scriptPathRaw)
#arcpy.AddMessage(listD)

justDirs = [ d for d in listD if os.path.isdir(os.path.join(scriptPathRaw,d))]
numSegments = len(justDirs)
arcpy.AddMessage("Processing " + str(numSegments) + " scenes")

#-------------------------------------------------------------------------
#                 IMPORT and ORTHO each RS2 segment
#-------------------------------------------------------------------------

   
if not arcpy.Exists(os.path.join(arcpy.env.workspace, 'Orthos')):
    arcpy.CreateFolder_management(arcpy.env.workspace, 'Orthos')      # create Ortos subdirectory

if justDirs == []: 
    arcpy.AddMessage('Nothing to process, jusDirs is Empty')
    sys.exit("Aborting...")	
for dir in justDirs:
    file01 =  os.path.join(arcpy.env.workspace,'Raw\\',dir,'product.xml')
    arcpy.AddMessage(file01)
    parseName = dir.rsplit('_')
    productSat  = parseName[0]
    productBeam = parseName[4]
    productDate = parseName[5]
    productTime = parseName[6]
    fileID = productSat + '_' + productBeam + '_' + productDate + '_' + productTime
    fileIDpix = fileID + '.pix'
    file02 =  os.path.join(arcpy.env.workspace,'Raw\\',fileIDpix)
    arcpy.AddMessage(file02)

	
    dbiw = []
    poption = "NEAR"
    dblayout = "BAND"
    fimport(file01, file02, dbiw, poption, dblayout)
    arcpy.AddMessage('Completed FIMPORT process')

    orthoDir =  os.path.join(arcpy.env.workspace,'Orthos\\')
    DEMfile =  inDEMfile
    ortho_report = orthoDir + 'ortho.rpt'
    pixelSize = '12.5,12.5'
    pixelSize = inPixSpacing
    sampling  = 4
#    numLooks  = inNumLooks
    mapUnits  =  inMapCoord
    orthoProduct  = orthoDir + "o" + fileIDpix

# -------------------------------------------------------------------------------------------    
    mfile    = file02					# Input image file name
    dbic     = [1,2]					# input HH + incidence angle channels
    mmseg    = [3]					# use the last math segment
    dbiw     = []					# Use all image
    srcbgd   = "NONE"
    filo = orthoProduct					# Uses the default file name
    ftype    = "PIX"					# use the PCIDSK format
    foptions = "BAND"
    outbgd   = [0]
    ulx    = ''                            
    uly    = ''
    lrx    = ''
    lry    = ''
    edgeclip = [0]         				# clip image by 10 percent
    tipostrn = ""
    mapunits = inMapCoord
    arcpy.AddMessage("mapunits " + mapunits)
    arcpy.AddMessage("inPixSpacing " + inPixSpacing)
    ORTHO_PXSZ = inPixSpacing.split(",")
###    mapunits = u'UTM 14 D122'
    bxpxsz   = ORTHO_PXSZ[0]
    bypxsz   = ORTHO_PXSZ[1]
    filedem  = DEMfile					# input DEM file
    dbec     = [1]					# use 1st DEM channel
#        backelev = [-150]
##    backelev = []
    backelev = [150]
#        elevref  = "MSL"         		# Elevation values referenced to mean sea level (Geoid)
##    elevref  = ""		  		# Elevation values referenced to mean sea level (Geoid)
    elevref  = "MSL"		  		# Elevation values referenced to mean sea level (Geoid)
    elevunit = "METER"
#   elfactor = [300,1.0]				# Specifies the offset only
    elfactor = []					# Specifies the offset only
    proc     = ""
#    sampling = [1]          				# Ortho correction is computed for every pixel
    sampling = [4]          				# Ortho correction is computed for every pixel
#    resample = "NEAR"       				# Nearest neighbour
    resample = "BILIN"      		
    
    ortho2(mfile, dbic, mmseg, dbiw, srcbgd, filo,  ftype,
          foptions, outbgd, ulx, uly, lrx, lry, edgeclip, tipostrn, mapunits, bxpxsz, bypxsz, filedem, dbec,
          backelev, elevref, elevunit, elfactor, proc, sampling, resample)

    arcpy.AddMessage('Completed ORTHO2 process')

parseName = dir.rsplit('_')
productDate = parseName[5]
productTime = parseName[6]
productPol  = ['_',parseName[7],parseName[8]]	# offset to index by 1,2

parseMap = inMapCoord.rsplit(' ')
UTMnn = '_' + parseMap[0] + parseMap[1]

#-------------------------------------------------------------------------
#                 MOSAIC the orthorectified segments if more than one
#-------------------------------------------------------------------------

if not arcpy.Exists(os.path.join(arcpy.env.workspace, 'Mosaic')):
    arcpy.CreateFolder_management(arcpy.env.workspace, 'Mosaic')      # create Mosaic subdirectory
	
if numSegments == 1: 				# NO mosaic, copy single segment ortho to mosaic directory

    scriptPathMosaic = os.path.join(arcpy.env.workspace,'Mosaic\\')  # Python
    mosaicProductPIX = scriptPathMosaic + productDate + UTMnn + '_mos.pix'

    FILI     = orthoProduct
    FILO     = mosaicProductPIX
    DBIW     = []
    DBIC     = [1,2]
    DBIB     = []
    DBVS     = []
    DBLUT    = []
    DBPCT    = []
    FTYPE    = "PIX"
    FOPTIONS = ""
    fexport(FILI, FILO, DBIW, DBIC, DBIB, DBVS, DBLUT, DBPCT, FTYPE, FOPTIONS)

elif numSegments >= 1: 				# mosaic muliple segments of pass

    scriptPathMosaic = os.path.join(arcpy.env.workspace,'Mosaic\\')
    mosaicProduct    = scriptPathMosaic + productDate + UTMnn + '_mos.pix'

    MFILE    = orthoDir
    DBICLIST ="1,2"
    MOSTYPE  ="FULL"
    FILO     = mosaicProduct
    FTYPE    ="PIX"
    FOPTIONS ="BAND"
    CLRMOS   ="YES"
    STARTIMG =""
    RADIOCOR ="NONE"
    BALMTHD  ="NONE"
    BALOPT   =[0]
    FILI_REF =""
    LOCLMASK ="NONE"
    GLOBFILE =""
    GLOBMASK =[]
    CUTMTHD  ="ENTIRE"
#    CUTMTHD="MINDIFF"  EASI setting
    FILVIN   =""
    DBIV     =[0]
    FILVOUT  = ""
    DBOV     =[0]
    DBLUTO   =""
#    BLEND    =[2]    # EASI setting
    BLEND    =[0]
    BACKVAL  =[0.0]
    TEMPDIR  =""
    automos( MFILE, DBICLIST, MOSTYPE, FILO, FTYPE, FOPTIONS, CLRMOS, STARTIMG, RADIOCOR, BALMTHD, BALOPT,
            FILI_REF, LOCLMASK, GLOBFILE, GLOBMASK, CUTMTHD, FILVIN, DBIV, FILVOUT,
            DBOV, DBLUTO, BLEND, BACKVAL, TEMPDIR)

    arcpy.AddMessage('Completed AUTOMOS process')

#-------------------------------------------------------------------------
#                 EXPORT each mosaic polarization to separate TIF file 
#-------------------------------------------------------------------------

for channel in [1,2]:
	
    scriptPathMosaic = os.path.join(arcpy.env.workspace,'Mosaic\\')   # Python
    mosaicProduct    = scriptPathMosaic + productDate + UTMnn + '_mos.pix'
    mosaicProductTIF = scriptPathMosaic + productDate + UTMnn + '_mos_' + productPol[channel] + '.tif'
    arcpy.AddMessage("Writing channel " + str(channel) + " to " + mosaicProductTIF)
    ftype   = '"'+'TIF'
    foption = '"'+'WORLD'

# Export to a tif 
    FILI = mosaicProduct
    FILO = mosaicProductTIF
    DBIW     = []
    DBIC     = [channel]
    DBIB     = []
    DBVS     = []
    DBLUT    = []
    DBPCT    = []
    FTYPE    = "TIF"
    FOPTIONS = "WORLD"
    fexport(FILI, FILO, DBIW, DBIC, DBIB, DBVS, DBLUT, DBPCT, FTYPE, FOPTIONS)

#-------------------------------------------------------------------------
#                 DONE                                               
#-------------------------------------------------------------------------



