# ---------------------------------------------------------------------------
# Script last modifed on: November 30, 2012 (updated for the 2013 version of the Flood Tools)
# Author: Alice deschamps alice.deschamps@nrcan.gc.ca
# Usage: 2_Scale_16to_8bit_set0 (inRaster)
# Setups: 1) Assumes user has set the Current Workspace in the Geoprocessing Environment. In ArcMap, go to: Geoprocessing/Environments/ Workspace and ScratchWorkspace, set these to the image date folder (for example \11April2011) and \Scratch respectively.
#2) Assumes a specific directory structure created with SAR_folders.bat file.
#
# Description: Scales image from  16bit to and 8bit. This tool starts with a 16 bit SAR image (exported from PCI as geotif) and creates 2 outputs and automatically names the files.  
#	*The first output is a 3x3 filtered 8bit SAR  image to be used for flood extraction in Step 2.  The output for this file goes in the \Results folder. 
#	*The second output is an un-filtered 8bit SAR image for web enhancement in Step 4.  The output for this files goes to the \Final_Results folder.
# ---------------------------------------------------------------------------
# Import system module
import arcpy
from arcpy import env
from arcpy.sa import *
import sys, string, os
arcpy.env.overwriteOutput = True

# Use of traceback to return more information about the errors should they occur.
def trace():
    import sys, traceback
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0] 
    line = tbinfo.split(", ")[1]
    filename = sys.path[0] + os.sep + "1_Scale_16to_8bit_set0.py"
    synerror = traceback.format_exc().splitlines()[-1]
    return line, filename, synerror

if __name__ == '__main__':

    try:
        # Check out any necessary licenses
        if arcpy.CheckProduct("ArcInfo") == "Unavailable":
            arcpy.AddError("ArcInfo Licensing Issue")
            raise LicenseError
        if arcpy.CheckExtension("Spatial") == "Available":
            arcpy.CheckOutExtension("Spatial")
        else:
            arcpy.AddError("Spatial Analyst Licensing Issue")
            raise LicenseError

        # Script arguments
        in16Raster = arcpy.GetParameterAsText(0)# single channel 16bit SAR image(HH or HV) exported from PCI as geotif.

        # Local variable
        inRastC=os.path.join(arcpy.env.scratchWorkspace,"inRastC")
        scImage1=os.path.join(arcpy.env.scratchWorkspace,"scImage1")
        fsMedRaster=os.path.join(arcpy.env.scratchWorkspace,"fsMedRaster")
        
        #Checks if output folders exist, if it does not creates them
        if not arcpy.Exists(os.path.join(arcpy.env.workspace, 'Final_results')):
            arcpy.CreateFolder_management(arcpy.env.workspace, 'Final_results')
        if not arcpy.Exists(os.path.join(arcpy.env.workspace, 'Results')):
            arcpy.CreateFolder_management(arcpy.env.workspace, 'Results')

        # Variable setup for automatic output file naming    
        outNFRaster= os.path.join(arcpy.env.workspace, 'Final_Results', (os.path.splitext(os.path.basename(in16Raster))[0] + "_8bit.tif"))
        outFRaster= os.path.join(arcpy.env.workspace, 'Results', (os.path.splitext(os.path.basename(in16Raster))[0] + "_8bit_MED3x3.tif"))

        # Lists the input/output file name and location
        arcpy.AddMessage("Name and location of your input file to scale: \n" + in16Raster)
        arcpy.AddMessage("Name and locationof your filtered scaled 8bit image is: \n" + outFRaster)
        arcpy.AddMessage("Name and location of your non-filtered scaled 8bit image is: \n" + outNFRaster)

        # Process: Copy Raster, this is done because grids have internal stats.
        arcpy.AddMessage ("Converting to GRID to extract statistics...")
        arcpy.CopyRaster_management(in16Raster, inRastC, "", "", "0", "NONE", "NONE", "")

        # Process: Extracts Image statistics and displays value for user.
        arcpy.AddMessage ("Extracting Statistics...")
        imageMin=int(arcpy.GetRasterProperties_management(inRastC, "MINIMUM").getOutput(0))
        arcpy.AddMessage("Image MIN value=" + str(imageMin))
        imageMax=int(arcpy.GetRasterProperties_management(inRastC, "MAXIMUM").getOutput(0))
        arcpy.AddMessage("Image Max value=" + str(imageMax))

        # Local variable, creates a raster object
        myRasterObj = arcpy.Raster(inRastC)

        # Process: Raster math to scale image
        # note:  Output is a float, we are adding 0.5 to make sure the next tool rounds properly since copy raster simply truncate value.
        arcpy.AddMessage("Scaling image as GRID image....")
        scImage = ((myRasterObj - imageMin) * 255 / (imageMax - imageMin) + 0.5)
        scImage.save(scImage1)
               
        # Process: Copy Raster, rounds off digits and now image is in the range 0-255. Also assigns NoData to 256 for a tif.
        arcpy.AddMessage("Creating Non-Filtered 8bit TIF image...")
        arcpy.CopyRaster_management(scImage1, outNFRaster, "", "", "", "NONE", "NONE", "8_BIT_UNSIGNED")

        # Process: Focal Statistics (3x3 median)
        arcpy.AddMessage("Creating Filtered 8bit GRID image...")
        neighborhood = NbrRectangle(3, 3, "CELL")
        outFocalStatistics = FocalStatistics(outNFRaster, neighborhood, "MEDIAN", "DATA")
        outFocalStatistics.save(fsMedRaster)

        #Process: Copy Raster to create an 8bit tif.
        # The input image has a Min-max range of 0-255 but NoData is -32868 and therefore defaulted to 16bit in a GRID.
        # Using copy Raster does not change the data range but converts to TIF and assigns NoData value to 256, therefore is an 8bit.
        arcpy.AddMessage("Creating Filtered 8bit TIF image ...")
        arcpy.CopyRaster_management(fsMedRaster, outFRaster, "", "", "", "NONE", "NONE", "8_BIT_UNSIGNED")
           
    except arcpy.ExecuteError:
        #Return Geoprocessing tool specific errors
        line, filename, err = trace()
        arcpy.AddError("Geoprocessing error on " + line + " of " + filename + " :")
        for msg in range(0, arcpy.GetMessageCount()):
            if arcpy.GetSeverity(msg) == 2:
                arcpy.AddReturnMessage(msg)
    except:
        #Returns Python and non-tool errors
        line, filename, err = trace()
        arcpy.AddError("Python error on " + line + " of " + filename)
        arcpy.AddError(err)
        
    finally:
        # Process: Delete intermediate files
        if arcpy.Exists(inRastC):
            arcpy.Delete_management(inRastC, "")
        if arcpy.Exists(scImage1):
            arcpy.Delete_management(scImage1, "")
        if arcpy.Exists(fsMedRaster):
            arcpy.Delete_management(fsMedRaster, "")
        arcpy.AddMessage("Intermediate files deleted!")
        
        # Check in the Spatial Analyst extension
        arcpy.CheckInExtension("Spatial")
    
