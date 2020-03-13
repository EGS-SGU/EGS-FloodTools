# ---------------------------------------------------------------------------
# Script last modifed: by G Choma on March 13, 2013 
#       Implemented renaming of shapefiles according to convention established by R Landry 6 Mar 2013
#       Added Filename of current ShapeFile to Attribute Table
#       Added GUI select of  AOI and prepend AOI to ShapeFile filename
#
#
# Shapefile Naming Convention (all characters are lowercase) for NEODF webserver:
# 
# <region>_YYYYMMDDutmZZ_<polarization>_thr<flood_threshold>_<min_area_threshold>_m_e.shp
# 
# Mandatory parameters:
#       <region> : regions of interest (pre-defined acronyms)
#       YYYYMMDD : year, month, date of acquisition of source imagery (UTC).
#                  Example of February 5,2013: 20130205
#       ZZ : UTM Zone
# 	<polarization> : hh, hv, vv (for RADARSAT-1, always use hh)
# 	<flood_threshold> : flood threshold value (integer value)
# 	<min_area_threshold> : minimum polygon size preserved.
#                              If the value is of type real, use "p" to replace the period  (unit: hectare).
#                              Example: 2.5 would be represented as 2p5
# 
# Optional parameters
#       _m : add only if a mask has been used
#       _e : add only if the shapefile has been edited and/or is considered as final
#   Example: pas_20110721utm14_hv_thr9_2p5_m_e.shp
#
# ------------------------------------------------------------------------------------
# Author: Alice Deschamps alice.deschamps@nrcan.gc.ca (updated for the 2013 version of the Flood Tools)
# Usage:  5_Vector_Attribution_fromR1R2_Header(inShapeFile, inFile, polList)
# Setup:  1) Assumes user has set the Current Workspace in the Geoprocessing Environment.
#            In ArcMap, go to: Geoprocessing/Environments/ Workspace and ScratchWorkspace 
#            and set these to image date folder (for example \11April2011) and \Scratch respectively.
#         2) Assumes the specific directory structure created with SAR_folders.bat file.
#
# Description:
# This tool reads in header information from Radarsat-1 (.txt) or Radarsat-2 (.xml) header file and creates vector attribution. Make sure you select your final edited flood extent shapefile as an input. This tool creates vector attribution based on the Radarsat-1 (.txt) or Radarsat-2 (product.xml) header file.   In the case of multiple image frames, point to the first acquired images in the series.   
# This tool adds important sensor parameter information to the final edited polygon shapefile, recalculates the area attribute to take edits into consideration, adds filename as an attribute (used by MASAS) and copies the file to the \Final_Results folder.  
# The polarization information and AOI must be specified from a drop down lists.  The output file will automatically be name using the NEODF naming convention.
# ---------------------------------------------------------------------------
# Import system module
from xml.etree import ElementTree
import arcpy, string, os, shutil, re

# Use of traceback to return more information about the errors should they occur.
def trace():
    import sys, traceback
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0] 
    line = tbinfo.split(", ")[1]
    filename = sys.path[0] + os.sep + "5_Vector_Attribution_fromR1R2_Header.py"
    synerror = traceback.format_exc().splitlines()[-1]
    return line, filename, synerror

if __name__ == '__main__':

    try:
        inShapeFile = arcpy.GetParameterAsText(0) 	#final edited polygon shapefile
        inFile      = arcpy.GetParameterAsText(1) 	#for R1 is .txt, for R2 is .xml
        polList = str(arcpy.GetParameterAsText(2))	#user select from drop list
        AOIList = str(arcpy.GetParameterAsText(3))	#user select from drop list

        # extract file extension to determine if txt of xml processing is required.    
        fileType=os.path.splitext(inFile)[1] #extract the file extension


        if fileType==".txt": 	        #Header information extraction for Radarsat-1 text file	
            inFileOpen = open(inFile, 'r')
            inText=inFileOpen.read() 	#reads entire file as a list, splits on spaces
            textList=inText.split()
            
            #search keyword index ("RADARSAT", "START", "ORBIT", "BEAM") to find desired attribution values
            #search for satellite name and extract information
            searchSatelliteName=textList.index("RADARSAT")
            satelliteName=str(textList[searchSatelliteName])+ "-" + str(textList[searchSatelliteName+1])
            #search for Beam Mode and extract information
            searchBeamMode=textList.index("BEAM")
            beamMode=str(textList[searchBeamMode+3])[0] + str(textList[searchBeamMode+4])
            #search for Orbit (asc/desc) and extract information
            searchOrbit=textList.index("ORBIT")
            orbit=str(textList[searchOrbit+2])
            #search for UTC date/time and extract information
            searchDateTimeUTC=textList.index("START")
            dateUTC=(textList[searchDateTimeUTC+3]+ textList[searchDateTimeUTC+2] + textList[searchDateTimeUTC+4])
            timeUTC=(textList[searchDateTimeUTC+5]).rstrip()[0:8]

            
            inFileOpen.close() 	#when done extracting information close text file 


        elif fileType==".xml":		#Header information extraction for Radarsat-2 xml file
            with open(inFile,'rt') as f:
                tree = ElementTree.parse(f)
            rootText='.//{http://www.rsi.ca/rs2/prod/xml/schemas}'# // is for the tag level followed by the schema/root
            
            #searches for xml tags and extract associated text for attribution values
            satelliteName=str(tree.find(rootText + 'satellite').text)
            beamMode=str(tree.find(rootText + 'beamModeMnemonic').text)
            orbit=str(tree.find(rootText + 'passDirection').text)
            dateTimeUTC=str(tree.find(rootText + 'rawDataStartTime').text)
            timeUTC=str(dateTimeUTC[11:19])
            dateUTC=str(dateTimeUTC[0:10])
           
        else: 				# this will never execute, since input filetype limited by GUI
            arcpy.AddMessage("Wrong file type, fields will be empty!") 

    # List the extracted header file information.  These are the attributes that will be added to shapefile.
        arcpy.AddMessage("The satellite is: " + satelliteName)
        arcpy.AddMessage("The polarization you selected is: " + polList)	#user entered from the GUI
        arcpy.AddMessage("The AOI you selected is: " + AOIList) 		#user entered from the GUI
        arcpy.AddMessage("The beam mode is: " + beamMode)
        arcpy.AddMessage("The orbit is: " + orbit)
        arcpy.AddMessage("The UTC date is: " + dateUTC)
        arcpy.AddMessage("The UTC time is: "+ timeUTC)
        
    # Make new version of ShapeFile with naming convention for web delivery as per R Landry specification 
		
        myShapeFile = AOIList + '_' + os.path.basename(inShapeFile)
        myShapeFile = myShapeFile.lower()			# convert to lower case for web delivery
        myShapeFileExt  = ''
        if '.shp' in myShapeFile:		# contortions to split filename into name + extension
            myShapeFile = myShapeFile.replace('.shp','')
            myShapeFileExt = '.shp'

        myShapeFile = myShapeFile.replace('_utm','utm')
#        myShapeFile = re.sub(r'_mosaic_hh_|_mosaic_hv_|_mosaic_vv_|_mosaic_vh_','_', myShapeFile)
#        myShapeFile = re.sub(r'_mos_hh_|_mos_hv_|_mos_vv_|_mos_vh_','_', myShapeFile)
#        myShapeFile = re.sub(r'_mosaic_','_', myShapeFile)	# retain polarization afer reconsidering
#        myShapeFile = re.sub(r'_mos_','_', myShapeFile)	# retain polarization afer reconsidering 
        myShapeFile = myShapeFile.replace('_mos_','_')
        myShapeFile = myShapeFile.replace('_mosaic_','_')		# catches a rare (illegal) case
        myShapeFile = myShapeFile.replace('.','p').replace('ha','')	# converts 5.5ha to '5p5' as per RL
        myShapeFile = myShapeFile + myShapeFileExt			# add extension back in
        if len(myShapeFile) > 50:
            myShapeFile = myShapeFile[:50]	# truncate as necessary
            arcpy.AddMessage("*** Truncated ShapeFile filename to 50 characters: " + myShapeFile)

        newShapeFile = os.path.join( os.path.dirname(inShapeFile),'..','Final_Results',myShapeFile )

#        shutil.copy (inShapeFile, newShapeFile)			# not the way to do it!
        arcpy.Copy_management(inShapeFile,newShapeFile,"")
		
        inShapeFile = newShapeFile		# We add fields to the web version of the shapefile
        			
        # Process: Add Fields
        arcpy.AddField_management(inShapeFile , "Satellite", "TEXT", "", "", "15", "", "NON_NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(inShapeFile , "Pol", "TEXT", "", "", "10", "", "NON_NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(inShapeFile , "Beam", "TEXT", "", "", "10", "", "NON_NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(inShapeFile , "Orbit", "TEXT", "", "", "10", "", "NON_NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(inShapeFile , "Date_UTC", "TEXT", "", "", "15", "", "NON_NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(inShapeFile , "Time_UTC", "TEXT", "", "", "10", "", "NON_NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(inShapeFile , "Filename", "TEXT", "", "", "45", "", "NON_NULLABLE", "NON_REQUIRED", "")
        arcpy.AddMessage("New fields were added to your shapefile")
        
        # Process: Calculates Fields, fills them with important sensor parameters
        arcpy.CalculateField_management(inShapeFile, "Satellite", "'" +str(satelliteName) +"'", "PYTHON","")
        arcpy.CalculateField_management(inShapeFile, "Pol", "'" + str(polList) + "'", "PYTHON", "")
        arcpy.CalculateField_management(inShapeFile, "Beam", "'" + str(beamMode) + "'", "PYTHON", "")
        arcpy.CalculateField_management(inShapeFile, "Orbit", "'" + str(orbit) + "'", "PYTHON", "")
        arcpy.CalculateField_management(inShapeFile, "Date_UTC", "'" + str(dateUTC) + "'", "PYTHON", "") 
        arcpy.CalculateField_management(inShapeFile, "Time_UTC", "'" + str(timeUTC) + "'", "PYTHON", "")
        
        arcpy.CalculateField_management(inShapeFile, "Filename", "'" + myShapeFile + "'", "PYTHON", "")

        arcpy.AddMessage("Shapefile attribution completed based information from the R1/R2 header file")

        # Process: Updated the calculation in the Area_ha field
        arcpy.CalculateField_management(inShapeFile, "Area_ha", "!Shape!.area/10000", "PYTHON_9.3", "")
        arcpy.AddMessage("Your Area field has been updated to take edits into account!")

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
   

