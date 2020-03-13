# ---------------------------------------------------------------------------
# Script last modifed on: November 30, 2012 (updated for the 2013 version of the Flood Tools)
# Author: Alice deschamps alice.deschamps@nrcan.gc.ca
# Usage: 4_Extract_Flood_Extent_and_Convert_to_Vector (inRaster, minThr, maxThr, minHa, {mask})
# Setups: 1) Assumes user has set the Current Workspace in the Geoprocessing Environment. In ArcMap, go to: Geoprocessing/Environments/ Workspace and ScratchWorkspace, set these to image date folder (for example \11April2011) and \Scratch respectively.
# 2) Assumes a specific directory structure created with SAR_folders.bat file.
#
# Description: Extracts open flooded water areas from a SAR image based on user specified threshold range and minimum polygon size. This tool starts with the scaled 8 bit and filtered SAR image (from step1) and creates single or multiple outputs and automatically names the file. The processing mask is optional and can be a raster or a vector. If raster, value 1= 'area to process' and the remaining of the raster is set to NO DATA (zero values will not work). When processing is done without a mask the entire image is processed. 
#The outputs are polygon shapefile of open water flood extent for every thresholds specifed between the min and max values.  The outputs tool goes to the \Results folder.
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
    filename = sys.path[0] + os.sep + "2_Extract_Flood_Extent_and_Convert_to_Vector.py"
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
        inRaster = arcpy.GetParameterAsText(0) #single channel 8bit filtered SAR image (from Step1)
        minThr = arcpy.GetParameterAsText(1) # Integer value that specifies the upper threshold range 
        maxThr = arcpy.GetParameterAsText(2) # Integer value that specifies the lower threshold range
        minHa = arcpy.GetParameterAsText(3) # Integer or decimal value that specifies minimum flood polygon size (ha). Use 0 to keep all.
        arcpy.env.mask = arcpy.GetParameterAsText(4) # Vector or raster mask. The processing mask is optional

        # Local variable
        outCon1=os.path.join(arcpy.env.scratchWorkspace,"outCon")
        outFocalStats1=os.path.join(arcpy.env.scratchWorkspace,"outFocalStats")
        Raster2poly=os.path.join(arcpy.env.scratchWorkspace,"Raster2poly.shp")
        Raster2polyCode0=os.path.join(arcpy.env.scratchWorkspace,"Raster2polyCode0.shp")

        #if processing mask empty adds nothing to output filname, if not empty adds "m" for mask to output filname!!
        if arcpy.env.mask == None:
            proMask= ""
        else:
            proMask= "_m"
            
        # This statement creates a list that will be used in FOR loop.  The minThr and maxThr are used to define the range.
        myList=range((int(minThr)), (int(maxThr)+1))
        
        #Checks if output folder exist, if it does not creates it
        if not arcpy.Exists(os.path.join(arcpy.env.workspace, 'Results')):
            arcpy.CreateFolder_management(arcpy.env.workspace, 'Results')
            
        # Process: will extract flood vectors for all thresholds in range specified inclusively.
        for i in myList:
            #Variable setup for automatic output file naming, SQL and whereClause
            outputShapefile= os.path.join(arcpy.env.workspace,'Results',(os.path.basename(inRaster)[0:-16]+ "_thr" + str(i) + "_" + str(minHa).replace('.','p') + "ha" + str(proMask)+ ".shp"))
            whereClause = '"Area_ha" >=' + minHa
            waterSql = '"Value" > 0 AND "Value" <=' + str(i)

            # Lists the input file and values for SQL and whereClause currently being processed by loop
            arcpy.AddMessage("The name and location of your input image is: " + inRaster)
            arcpy.AddMessage("The threshold SQL is: " + waterSql)
            arcpy.AddMessage("The minimum hectare size you selected is:" + whereClause)
            arcpy.AddMessage("The name and location of your output image is: " + outputShapefile)

            # Process: Con (needs spatial analyst license)
            arcpy.AddMessage("Open raster flood extent map is being created...")
            outCon = Con(inRaster, 1, 0 , waterSql)
            outCon.save(outCon1)
            
            # Process: Focal Statistics (5x5 Mode)
            arcpy.AddMessage("Raster flood extent map is being filtered...")
            outFocalStats = FocalStatistics(outCon, "Rectangle 5 5 CELL", "MAJORITY", "DATA")
            outFocalStats.save(outFocalStats1)
            
            # Process: Convert Raster to Polygon
            arcpy.AddMessage("Converting raster flood extent map to vector...")
            arcpy.RasterToPolygon_conversion(outFocalStats1, Raster2poly, "NO_SIMPLIFY", "")

            arcpy.AddMessage("Calculating area in hectares for the flooded polygons and applying minimum polygon size...")        
            # Process: Select Gridcode >0
            arcpy.Select_analysis(Raster2poly, Raster2polyCode0, "GRIDCODE >0")

            # Process: Add Field to Calculate Area 
            arcpy.AddField_management(Raster2polyCode0, "Area_ha", "FLOAT", "", "", "", "", "NON_NULLABLE", "NON_REQUIRED", "")

            # Process: Calculate Field: Area in Ha
            arcpy.CalculateField_management(Raster2polyCode0, "Area_ha", "!Shape!.area/10000", "PYTHON_9.3", "")
            
            # Process: Select min polygon size
            arcpy.Select_analysis(Raster2polyCode0, outputShapefile, whereClause)

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
        if arcpy.Exists(outCon1):
            arcpy.Delete_management(outCon1, "")
        if arcpy.Exists(outFocalStats1):
            arcpy.Delete_management(outFocalStats1, "")
        if arcpy.Exists(Raster2poly):
            arcpy.Delete_management(Raster2poly, "")
        if arcpy.Exists(Raster2polyCode0):
            arcpy.Delete_management(Raster2polyCode0, "")
        arcpy.AddMessage("Intermediate files deleted!")
        
        # Check in the Spatial Analyst extension
        arcpy.CheckInExtension("Spatial")

