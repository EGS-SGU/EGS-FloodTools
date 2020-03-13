#---------------------------------------------------------------------------
# Script last modifed on: November 30, 2012 (updated for the 2013 version of the Flood Tools)
# Author: Alice deschamps alice.deschamps@nrcan.gc.ca
# Usage: 3_Enhance_8bit_Web_Python_Tool (inRaster, No_STDEV)
# Setups: 1) Assumes user has set the Current Workspace in the Geoprocessing Environment. In ArcMap, go to: Geoprocessing/Environments/ Workspace and ScratchWorkspace, set these to image date folder (for example \11April2011) and \Scratch respectively.
# 2) Assumes a specific directory structure created with SAR_folders.bat file.
# 
# Description: This tool starts with the 8 bit scaled SAR image (from Step1) and trims the right tail of the histogram based on user entered value. Default value is set to 3 STDEV, for a stronger enhancement use 2 or 2.5 STDEV.  The result is a new enhanced images for the webserver. The outputs tool goes to the \Final_Results folder.
# ---------------------------------------------------------------------------
# Import system module
import arcpy
from arcpy import env
from arcpy.sa import *
import sys, string, os, re
arcpy.env.overwriteOutput = True

# Use of traceback to return more information about the errors should they occur.
def trace():
    import sys, traceback
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0] 
    line = tbinfo.split(", ")[1]
    filename = sys.path[0] + os.sep + "4_Enhance_8bit_for_Web.py"
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
        inRaster = arcpy.GetParameterAsText(0)#single channel 8 bit unfiltered SAR image (from Step 1)
        No_STDEV = arcpy.GetParameterAsText(1)#STDEV used for right tail trim
        Sensor = arcpy.GetParameterAsText(2)#Prompt user to select from list RS1 or RS2

        # Local variable
        enhImage1=os.path.join(arcpy.env.scratchWorkspace, "enhImage1")
            
        # Creates a raster object
        myRasterObj=arcpy.Raster(inRaster)

        #Checks if output folders exist, if it does not creates them
        if not arcpy.Exists(os.path.join(arcpy.env.workspace, 'Final_results')):
            arcpy.CreateFolder_management(arcpy.env.workspace, 'Final_results')
        if not arcpy.Exists(os.path.join(arcpy.env.workspace, 'Results')):
            arcpy.CreateFolder_management(arcpy.env.workspace, 'Results')
            
        # Variable setup for automatic output file naming
        outputRaster = os.path.join(arcpy.env.workspace, 'Final_Results', (Sensor + "_" + (os.path.splitext(os.path.basename(inRaster))[0] + "_" + str(No_STDEV).replace('.','p') + "STDEV_" + "enh.tif")))
        outputRaster = outputRaster.lower()
        outputRaster = re.sub('_utm.*?_mos_' , '_', outputRaster)
        
        # Lists the input file, output file and stdev selected for enhancement    
        arcpy.AddMessage("Name of file to enhance: \n" + inRaster)
        arcpy.AddMessage("Name and location of your enhanced image is: \n" + outputRaster)
        arcpy.AddMessage("Number of Standard Deviations on the right side to trim histogram: " + No_STDEV)

        # Process: Extracts Image statistics and displays value for user.
        arcpy.AddMessage("Extracting statistics from image...")
        imageMin=int(arcpy.GetRasterProperties_management(inRaster, "MINIMUM").getOutput(0))
        arcpy.AddMessage("Image MIN value: " + str(imageMin))
        imageMean=float(arcpy.GetRasterProperties_management(inRaster, "MEAN").getOutput(0))
        arcpy.AddMessage("Image MEAN value=" + str(imageMean))
        imageMax=int(arcpy.GetRasterProperties_management(inRaster, "MAXIMUM").getOutput(0))
        arcpy.AddMessage("Image Max value=" + str(imageMax))
        imageSTDEV=float(arcpy.GetRasterProperties_management(inRaster, "STD").getOutput(0))
        arcpy.AddMessage("Image STDEV value=" + str(imageSTDEV))

        # Process: calculates a linear stretch with right tail trim
        arcpy.AddMessage ("Enhancing image.....")
        enhImage = ((myRasterObj - imageMin) / ((imageMean + float(No_STDEV) * imageSTDEV) - imageMin)) * 255
        enhImage.save(enhImage1)

        # Process: Trimming vales >255 and converting to tif
        arcpy.AddMessage ("Converting to tif for final output...")
        outCon1= Con(enhImage1, enhImage1, 255, "VALUE < 255")
        outCon1.save(enhImage1)
        arcpy.CopyRaster_management(enhImage1, outputRaster, "", "", "", "NONE", "NONE", "8_BIT_UNSIGNED")
        
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
        if arcpy.Exists(enhImage1):
            arcpy.Delete_management(enhImage1, "")
        arcpy.AddMessage ("Intermediate files deleted!")
        
        # Check in the Spatial Analyst extension
        arcpy.CheckInExtension("Spatial")


