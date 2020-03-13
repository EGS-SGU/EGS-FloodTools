#! /usr/bin/env python
# -*- coding: Latin-1 -*-

__revision__ = "--REVISION-- : $Id: FT3_ExtractFloodExtentAndConvertToVector.py 838 2017-04-04 18:31:32Z stolszcz $"

#==============================================================================#
# HISTORY                                                                      #
# -------                                                                      #
# Originally developed as ArCGIS Toolbox                                       #
# "4_Extract_Flood_Extent_and_Convert_to_Vector.py" by A. Deschamps, converted #
# to Python Toolbox and altered by V. Neufeld, September 2016.                 #
#==============================================================================#


# Libraries
# =========
import arcpy
from   arcpy.sa import *
import argparse
import glob
import os
import shutil
import sys
import traceback


# ======= #
# Globals #
# ======= #


class FT3_ExtractFloodExtentAndConvertToVector(object):
    """
    Performs third step in creating Flood Product.

    Is the third tool called in the procedure used to generate Flood Products.
    Starting in the workspace root directory, creates all subdirectories it
    requires if they are not already present (OWFEP, Scratch), then processes
    one or more 8-bit filtered image files (HH, HV, VV, VH), selected from those
    that were produced by the FT2_Scale16to8BitSet tool and placed in the Scaled
    subdirectory.  Processing includes establishing which pixels represent
    flooded areas and jetisoning those that aren't, applying a 5x5 rectangular
    majority filter to smooth the results in an attempt to reduce the number of
    polygons that will be generated, converting from raster to vector polygon,
    eliminating non-flood regions from the vector polygon shapefile, then
    finally removing all flood polygons that are smaller than a specified
    minimum size.

    Instance Attributes
        label           : Shown in Label text box when Properties dialog box is
                          opened by right-clicking the tool in the Catalog Tree
                          and selecting the "Properties..." menu.

        description     : Shown in Description text box when Properties dialog
                          box is opened by right-clicking the tool in the
                          Catalog Tree and selecting the "Properties..." menu.

        category        : Toolset grouping to which this belongs.  Allows all
                          tools that belong to a shared theme to be grouped
                          together under a common umbrella.

        canRunInBackground
                        : Controls whether the tool can be run in the background
                          or requires the Results window to be opened and will
                          block other work from being performed in parallel
                          while this script is running.

    Class Attributes
        SUPPORTED_POLARIZATIONS
                        : List of all polarizations that are supported by the
                          tool.  Will not be able to process any file that does
                          not employ one of these polarizations.  Created as a
                          class variable so can be accessed by the
                          FT0_FloodMaster tool.

        DEFAULT_WATERTHRESHOLDS
                        : List of all default water thresholds that correspond
                          to the SUPPORTED_POLARIZATIONS.  If user does not
                          explicitly define the thresholds to be processed, the
                          defaults will be applied.  Created as a class variable
                          so can be accessed by the FT0_FloodMaster tool.

        idxChangeField  : An essential custom class attribute, is used to keep
                          track of the last parameter that was changed when
                          running the tool in GUI mode through ArcCatalog or
                          ArcMap.  It's value is set in the "updateParameters"
                          method and is employed in "updateMessages" to enable
                          previously disabled fields and to identify which
                          fields require validations to be performed on them
                          when they are changed.  This technique is meant to
                          mimic event handlers found in other programming
                          languages.  The variable will not work as required if
                          it is defined as an instance attribute, however it is
                          possible to use an equivalent global variable instead,
                          if desired.
    """
    # Class Variables (Custom)
    # ------------------------
    SUPPORTED_POLARIZATIONS   = ["HH", "HV", "VV", "VH"]
    DEFAULT_WATERTHRESHOLDS = [["HH", 10, 12],
                               ["HV",  4,  6],
                               ["VV",  4,  6],
                               ["VH", 10, 12]]
    idxChangeField          = None


    def __init__(self):
        """
        Part of the Python toolbox template, used to define the tool (tool name
        is the name of the class).

        A Python Toolbox can have more than one tool defined within it.  Each
        will have its own constructor like this that will uniquely identify it.


        Parameters:
            None


        Return Values:
            None


        Limit(s) and Constraint(s) During Use:
            The "canRunInBackground" MUST be set to 'True'.  If this is not
            done, will not run 64-bit version of Python in the "execute" method
            and the PCI Geomatica tools will not be available.
        """
        self.label              = "FT3_ExtractFloodExtentAndConvertToVector"
        self.description        = "Third step in generating Flood Product.  "  \
                                  "Transforms 8-bit scaled filtered SAR "      \
                                  "images to vector polygons, applying a 5x5 " \
                                  "rectangular majority smoothing filter and " \
                                  "minimum polygon size to generate "          \
                                  "reasonable results."
        self.canRunInBackground = False
##        self.category           = "FloodTools"


    def getParameterInfo(self):
        """
        Part of the Python toolbox template, used to define the parameters that
        are used throughout the tool.

        Is an essential method since it defines all parameters and their
        attributes that are necessary for proper tool functioning.  These
        parameters are used to create the data entry fields seen in the GUI and
        are exchanged through all of the methods fundamental to the Python tool.
        Their attributes define what dataypes they accept, how many values they
        will accept, whether or not they are mandatory, and their direction of
        exchange -- input or output.

        While GUI operations launched through ArcCatalog or ArcMap will
        automatically call this method, the method must be called by the command
        line implementation in function "main()" or by the unitest module when
        when preparing an object for testing.


        Parameters:
            None


        Return Values:
            Parameter[]  All Parameter objects defined and required for the
                         tool, and their values.


        Limit(s) and Constraint(s) During Use:
            None

            For more details refer to following links:
            Python Toolbox
            http://resources.arcgis.com/EN/HELP/MAIN/10.2/index.html#/The_Python_toolbox_template/001500000023000000/
            getParameterInfo Method
            http://resources.arcgis.com/en/help/main/10.2/index.html#//001500000028000000
            http://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/defining-parameters-in-a-python-toolbox.htm#ESRI_SECTION1_E2BAA5D4440D41D6AAB948922186905A
        """
        params = [None]*5

        params[0] = arcpy.Parameter(
                     displayName   = "Workspace",
                     name          = "workspace",
                     datatype      = "DEFolder",
                     parameterType = "Required",
                     direction     = "Input"
                     )
        params[0].value = None


        params[1] = arcpy.Parameter(
                        displayName   = "8-Bit Scaled Filtered SAR Image",
                        name          = "sarImage8Bit",
                        datatype      = "GPString",
                        parameterType = "Required",
                        direction     = "Input",
                        multiValue    = "True"
                     )
        params[1].enabled     = True
        params[1].value       = None
        params[1].filter.type = "ValueList"
        params[1].filter.list = []

        params[2] = arcpy.Parameter(
                     displayName   = "Water Thresholds",
                     name          = "waterThresholds",
                     datatype      = "GPValueTable",
                     parameterType = "Required",
                     direction     = "Input"
                     )
        # Limit the acceptable entries to the 4 possible polarization pairs
        params[2].columns               = [["GPString", "Polarization"],
                                           ["GPLong",   "MIN Threshold"],
                                           ["GPLong",   "MAX Threshold"]]
        params[2].values                = \
                FT3_ExtractFloodExtentAndConvertToVector.DEFAULT_WATERTHRESHOLDS
        params[2].parameterDependencies = \
                FT3_ExtractFloodExtentAndConvertToVector.SUPPORTED_POLARIZATIONS
        params[2].filters[0].type       = "ValueList"
        params[2].filters[0].list       = \
                FT3_ExtractFloodExtentAndConvertToVector.SUPPORTED_POLARIZATIONS
##        params[1].enabled = False

        params[3] = arcpy.Parameter(
                        displayName   = "Minimum Polygon Size (hectares)",
                        name          = "minPolygonSize",
                        datatype      = "GPDouble",
                        parameterType = "Required",
                        direction     = "Input"
                     )
        params[3].value = "2.5"

        params[4] = arcpy.Parameter(
                     displayName   = "Processing Mask",
                     name          = "processingMask",
                     datatype      = ["DEFeatureClass","DEFeatureDataset","DERasterDataset"],
##                     datatype      = ["DEFile","DERasterDataset"],
##                     datatype      = "DEFile",
                     parameterType = "Optional",
                     direction     = "Input"
                     )
##        params[4].filter.list = ["tif","img"]

        return params


    def isLicensed(self):
        """
        Part of the Python toolbox template, should be set to indicate whether
        or not the tool is licensed to execute.

        Is not being used in this implementation.  As ArcGIS documentation
        states:
            'It can be used to restrict the tool from being run if the
             appropriate licenses and extensions required to run other
             geoprocessing tools used by the Python toolbox tool are not
             available.'

            'If the isLicensed method returns False, the tool cannot be
             executed.  If the method returns True or the method is not used,
             the tool can be executed.'


        Parameters:
            None


        Return Values:
            True - Will always return True since licensing checks are not being
                   performed.  Might be implemented as follows, for example, if
                   licensing was an issue:

                   # Allow the tool to execute, only if the ArcGIS 3D Analyst
                   # extension is available.
                   try:
                       if arcpy.CheckExtension("3D") != "Available":
                           raise Exception
                   except Exception:
                       return False # tool cannot be executed
                   return True      # tool can    be executed


        Limit(s) and Constraint(s) During Use:
            None

            For more details refer to following links:
            Python Toolbox
            http://resources.arcgis.com/EN/HELP/MAIN/10.2/index.html#/The_Python_toolbox_template/001500000023000000/
            isLicensed Method
            http://resources.arcgis.com/en/help/main/10.2/index.html#//001500000025000000
        """
        return True


    def updateParameters(self, parameters):
        """
        Part of the Python toolbox template, called whenever a parameter has
        been changed.

        This method serves as a rough equivalent of the event handlers found in
        other programming languages.  Its purported use is to modify the values
        and properties of parameters before internal validation is performed.
        In practice, however, it has been found that making such changes here,
        programatically, does not achieve the desired results, so instead the
        method has been used to simply identify which parameter has just been
        changed and record its index value in the custom "idxChangeField" field.
        The application will next automatically call the "updateMessages" method
        which has been designed to examine the "idxChangeField" parameter and
        act on the change.


        Parameters:
            TYPE        NAME            DESCRIPTION
            Parameter[] parameters      All Parameter objects defined in the
                                        "getParameterInfo" method of the tool,
                                        and their values.  This includes both
                                        mandatory and optional parameters.  Will
                                        be assigned new values through the GUI's
                                        data entry fields which in turn will
                                        trigger a call to this method when a
                                        change has occurred.


        Return Values:
            None


        Limit(s) and Constraint(s) During Use:
            None

            For more details refer to following links:
            Python Toolbox
            http://resources.arcgis.com/EN/HELP/MAIN/10.2/index.html#/The_Python_toolbox_template/001500000023000000/
            updateParameters Method
            http://resources.arcgis.com/en/help/main/10.2/index.html#//00150000002m000000
            Parameters
            http://resources.arcgis.com/EN/HELP/MAIN/10.2/index.html#/Accessing_parameters_within_a_Python_toolbox/001500000037000000/
        """
        # Python toolboxes do not support conventional event handlers as seen in
        # other programming languages to react to changes in GUI controls.
        # Identify which control has changed now, for reference subsequently
        # within the "updateMessages" method.  If have loaded a workspace,
        # look for TIF images within the "Mosaic" subdirectory, if they exist,
        # and load them into the "16-Bit Polarized SAR Image" field, selecting
        # one as a default for processing.
        for i in range(0, len(parameters)):
            if parameters[i].hasBeenValidated == False:
                FT3_ExtractFloodExtentAndConvertToVector.idxChangeField = i
                break
        if FT3_ExtractFloodExtentAndConvertToVector.idxChangeField == 0:
            if parameters[0].value != None:
                self.load8BitSarImageField(parameters)
        return


    def updateMessages(self, parameters):
        """
        Part of the Python toolbox template, called after internal validation,
        can be used to modify the messages created by internal validation for
        each tool parameter.

        In this implementation, it:
        - confirms that the workspace exists, is accessible, contains the
          "Scaled" subdirectory and at least one TIF file within that directory
        - for each selected 8-bit filtered SAR image, ensures that corresponding
          water thresholds are defined and are valid
        - confirms that minimum polygon size is defined and is valid
        - if processing mask is defined, ensures that it exists and is
          accessible

        Parameters:
            TYPE        NAME            DESCRIPTION
            Parameter[] parameters      All Parameter objects defined in the
                                        "getParameterInfo" method of the tool,
                                        and their values.  This includes both
                                        mandatory and optional parameters.  Will
                                        be assigned new values through the GUI's
                                        data entry fields which in turn will
                                        trigger a call to this method.


        Return Values:
            None


        Limit(s) and Constraint(s) During Use:
            None

            For more details refer to following links:
            Python Toolbox
            http://resources.arcgis.com/EN/HELP/MAIN/10.2/index.html#/The_Python_toolbox_template/001500000023000000/
            updateMessages Method
            http://resources.arcgis.com/en/help/main/10.2/index.html#//00150000002m000000
            Parameters
            http://resources.arcgis.com/EN/HELP/MAIN/10.2/index.html#/Accessing_parameters_within_a_Python_toolbox/001500000037000000/
        """
        # Index of last changed field, identified in "updateParameters":
        # - Workspace
        if FT3_ExtractFloodExtentAndConvertToVector.idxChangeField == 0:
            if parameters[0].value != None:
                msgText = FT3_ExtractFloodExtentAndConvertToVector.validateWorkspace(str(parameters[0].value))
                if msgText:
                    parameters[0].setErrorMessage( msgText )
        # - Water Thresholds
        #   Changes to Workspace, SAR Image and Water Thresholds all effect
        #   this, but a click on a checkbox won't trigger the event until AFTER
        #   the control loses focus, which sucks.  See:
        #   http://support.esri.com/technical-article/000011771
        if FT3_ExtractFloodExtentAndConvertToVector.idxChangeField in [0,1,2]:
            msgText \
            = FT3_ExtractFloodExtentAndConvertToVector.validateWaterThresholds(
                    parameters[1], parameters[2])  # SAR files, Water Thresholds

            if msgText:
                if msgText.split(' ', 1)[0] == "ERROR:":
                    parameters[2].setErrorMessage( msgText )
                else:
                    parameters[2].setWarningMessage( msgText )
        # - Minimum Polygon Size
        elif FT3_ExtractFloodExtentAndConvertToVector.idxChangeField == 3:
            msgText \
            = FT3_ExtractFloodExtentAndConvertToVector.validateMinimumPolygonSize(parameters[3].value)
            if msgText:
                parameters[3].setErrorMessage( msgText )
        # - Processing Mask
        elif FT3_ExtractFloodExtentAndConvertToVector.idxChangeField == 4:
            if parameters[4].value != None:
                msgText = FT3_ExtractFloodExtentAndConvertToVector.validateProcessingMask(str(parameters[4].value))
                if msgText:
                    parameters[4].setErrorMessage( msgText )

        return


    def execute(self, parameters, messages):
        """
        Part of the Python toolbox template, used to produce the expected output
        of the tool.

        Orchestrates all of the steps required to produce output, called from
        the GUI when the user presses the OK button, or from function "main()"
        at the bottom of this module when command line interface has been
        defined and the script is run in batch.

        In this implementation, "execute" performs the following:
        - checks out and later returns ArcGIS Spatial Analyst tool
        - validates all incoming parameters
            - verifies that workspace directory exists, is accessible, and
              contains the "Scaled" subdirectory with at least 1 TIF file in it
            - verifies that all 8-bit SAR TIF files exist and are accessible
            - verifies that all required polarizations and water thresholds
              are present and properly defined
            - if a processing mask is to be applied, verifies that file exists
              and is accessible
        - creates "Scratch" and "OWFEP" (Open Water Flood Extent Polygons)
          folders if they do not already exist, and sets the arcpy
          working/scratch directories to point to "Scratch" for those tools that
          implictly require a working space for temporary files
        - assigns values to variables common to all images/files to be processed
          and created including SQL Where Clauses and temp file names
        - processes each selected 8-Bit Scaled Filtered SAR Image:
            - determines MIN and MAX water threshold values and generates range
            - processes each threshold value in range:
                - defines target shapefile name for each threshold value
                - applies CON tool to SAR image to identify flood pixels, those
                  that are <= threshold value
                - applies 5x5 moving rectangle "majority" filter to smooth out
                  pixel values and thereby reduce number of polygons to be
                  created
                - converts raster to vector polygon shapefile
                - eliminates polygons that represent non-flooded regions
                - calculates area in hectares for each flood polygon
                - removes polygons that are smaller than specified value and
                  saves resultant to target shapefile -- this shapefile will be
                  manually inspected by user to determine if it should be passed
                  to subsequent tools in the Flood Tools suite
        - deletes temporary files and directories created as part of
          intermediate processing


        Parameters:
            TYPE        NAME            DESCRIPTION
            Parameter[] parameters      All Parameter objects defined in the
                                        "getParameterInfo" method of the tool,
                                        and their values.  This includes both
                                        mandatory and optional parameters.  Will
                                        be assigned values through the GUI's
                                        data entry fields, or by function
                                        "main()".
            ???         messages        Not used in this instance, can be used
                                        to issue info/warning/error messages.
                                        Have used "arcpy" directly to serve this
                                        role.


        Return Values:
            - 0         Successfully completed.  Script will exit with status 0.
            - 1         Error encountered.  Check log/standard output for
                        details.  The script will exit with this value to
                        inform calling process that problem exists.


        Limit(s) and Constraint(s) During Use:
            None

            For more details refer to following links:
            Python Toolbox
            http://resources.arcgis.com/EN/HELP/MAIN/10.2/index.html#/The_Python_toolbox_template/001500000023000000/
            execute Method
            http://resources.arcgis.com/en/help/main/10.2/index.html#//001500000037000000
            Parameters
            http://resources.arcgis.com/EN/HELP/MAIN/10.2/index.html#/Accessing_parameters_within_a_Python_toolbox/001500000037000000/
            Messages
            http://resources.arcgis.com/en/help/main/10.2/index.html#//001500000036000000
            http://resources.arcgis.com/en/help/main/10.2/index.html#//001500000031000000
        """
        # Initialize status to ERROR, will be reset to SUCCESS if "try" completes
        status            = 1
        conObj            = None
        fsObj             = None
        scratchDir        = None
        tempRaster2Poly   = None
        tempPolyFloodOnly = None

        try:
            # Open up message log and progress bar
            # ------------------------------------
            arcpy.SetProgressor("default", "Flood Tools - Extract Flood Extent And Convert To Vector")
            arcpy.AddMessage("Python Version: " + sys.version)
            arcpy.AddMessage("Current Product License: " + arcpy.ProductInfo())

            # Ensure overwriting is permitted so the temp files can be reused
            # when more than 1 image is to be processed
            arcpy.env.overwriteOutput = True

            # Ensure required product licenses are available
            # ----------------------------------------------
            # ArcInfo term is deprecated, but is still code for "ArcGIS Advanced"
            checkResults = str(arcpy.CheckProduct("ArcInfo"))
            if checkResults not in ["Available","AlreadyInitialized"]:
                arcpy.AddError("ERROR:  Installation does not have required " \
                               "access to ArcGIS Advanced (ArcInfo) license.")
                return 1
            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")
            else:
                arcpy.AddError("ERROR:  Installation does not have required " \
                               "access to ArcGIS Spatial Analyst license.")
                return 1

            # Ensure mandatory parameters are present, validate where necessary
            # -----------------------------------------------------------------
            # NOTE:
            # While the ArcGIS GUI interface ensures mandatory parameters are
            # present before calling "execute", the command-line or call via the
            # "FT3_ExtractFloodExtentAndConvertToVector" object does not.
            arcpy.SetProgressorLabel("Validate Mandatory Parameters...")
            arcpy.AddMessage("Validate Mandatory Parameters")

            # Assign parameters to local variables
            # [Note: str() cast of None yields "None"]
            if parameters[0].value == None:
                workspace      = None
            else:
                workspace      = str(parameters[0].value)
            sarFileList        = parameters[1].values
            waterThresholds    = parameters[2].values
            minPolygonSize     = parameters[3].value
            if parameters[4].value == None:
                processingMask = None
            else:
                processingMask = str(parameters[4].value)

            # Validate Workspace
            arcpy.SetProgressorLabel("Validate Workspace...")
            arcpy.AddMessage("- Validate Workspace")
            msgText = FT3_ExtractFloodExtentAndConvertToVector.validateWorkspace(workspace)
            if msgText:
                arcpy.AddError( msgText )
                return 1

            # Validate List Of Selected SAR Images
            arcpy.SetProgressorLabel("Validate 8-Bit Scaled Filtered SAR Image Files...")
            arcpy.AddMessage("- Validate Scaled 8-Bit Filtered SAR Image Files")
            msgText = FT3_ExtractFloodExtentAndConvertToVector.validate8BitSARFiles(sarFileList)
            if msgText:
                arcpy.AddError( msgText )
                return 1

            # Validate Water Thresholds
            arcpy.SetProgressorLabel("Validate Water Thresholds...")
            arcpy.AddMessage("- Validate Water Thresholds")
            msgText = FT3_ExtractFloodExtentAndConvertToVector.validateWaterThresholds(
                            parameters[1], parameters[2])  # SAR files, Water Thresholds
            if msgText:
                # Ignore WARNINGS, only invalidate if ERROR
                if msgText.split(' ', 1)[0] == "ERROR:":
                    arcpy.AddError( msgText )
                    return 1

            # Validate Minimum Polygon Size
            arcpy.SetProgressorLabel("Validate Minimum Polygon Size...")
            arcpy.AddMessage("- Validate Minimum Polygon Size")
            msgText = FT3_ExtractFloodExtentAndConvertToVector.validateMinimumPolygonSize(minPolygonSize)
            if msgText:
                arcpy.AddError( msgText )
                return 1

            # Validate Processing Mask
            arcpy.SetProgressorLabel("Validate Processing Mask...")
            arcpy.AddMessage("- Validate Processing Mask\n")
            if processingMask:
                msgText = FT3_ExtractFloodExtentAndConvertToVector.validateProcessingMask(processingMask)
                if msgText:
                    arcpy.AddError( msgText )
                    return 1

            # Echo Final Parameters To Log
            # ----------------------------
            # Okay to proceed.  Feedback
            msgText =  "Parameter Values\n"       \
                       "- Workspace Directory  : %s\n" \
                       "- 8-Bit SAR Image Files:\n" % (workspace)
            for sarFileName in sarFileList:
                msgText += "  %s\n" % (str(sarFileName))
            msgText += "- Water Thresholds     :\n"
            for waterThreshold in waterThresholds:
                msgText += "  %s  %2d  %2d\n" % \
                           (waterThreshold[0], waterThreshold[1], waterThreshold[2])
            msgText += "- Minimum Polygon Size : %.2f\n" % (minPolygonSize)
            msgText += "- Processing Mask      : %s\n"   % (str(processingMask))
            arcpy.AddMessage(msgText)

            #-------------------------------------------------------------------
            #        Create Required Subdirectories And Common Variables
            #-------------------------------------------------------------------
            # Create "Scratch" and "OWFEP" subdirectories if they do not already
            # exist to create temporary and intermediate files in.
            arcpy.SetProgressorLabel("Create Subdirectories...")
            arcpy.AddMessage("Create Subdirectories")
            scratchDir = os.path.join(workspace, 'Scratch')
            owfepDir   = os.path.join(workspace, 'OWFEP')
            arcpy.AddMessage("- Scratch Folder: '%s'"   % (scratchDir))
            if not os.path.exists(scratchDir):
                os.mkdir(scratchDir)
            arcpy.AddMessage("- OWFEP Folder  : '%s'\n" % (owfepDir))
            if not os.path.exists(owfepDir):
                os.mkdir(owfepDir)

            # Set workspaces to scratch directory for tools like
            # "FocalStatistics" to save their working files to.
            arcpy.env.workspace        = scratchDir
            arcpy.env.scratchWorkspace = scratchDir

            # If processing mask exists, assign to "arcpy.env.mask" environment
            # setting, and define the filename element that will indicate
            # whether or not a processing mask has been applied (ie. file name
            # will include an "m").
            #
            # http://pro.arcgis.com/en/pro-app/tool-reference/environment-settings/mask.htm
            if processingMask:
                arcpy.env.mask   = processingMask
                filepartProcMask = "_m"
            else:
                arcpy.env.mask   = None
                filepartProcMask = ""

            # Where Clause used to remove insignificant flood areas
            whereClauseArea = '"Area_ha" >= ' + str(minPolygonSize)

            # Temporary Files
            # NOTE:
            # For calls to Spatial Analyst tools, will pass objects returned
            # from those calls to subsequent tools, rather than first save to a
            # temporary file and then pass that file.  Since objects are already
            # in memory, creation and later deletion of such files are
            # unneccessary steps.
            tempRaster2Poly   = os.path.join(scratchDir,"tempRaster2Poly.shp")
            tempPolyFloodOnly = os.path.join(scratchDir,"tempPolyFloodOnly.shp")
            tempOutShapefile = os.path.join(scratchDir,"tempOutShapefile.shp")

            #-------------------------------------------------------------------
            #                  Process All Selected SAR Images
            #-------------------------------------------------------------------
            arcpy.SetProgressorLabel("Process Scaled And Filtered SAR Images...")
            arcpy.AddMessage("Process Scaled And Filtered SAR Images")
            for i, sarImage in enumerate(sarFileList):
                # Get Water Threshold associated with current SAR image using
                # it's polarization as key.  Image file names will be similar
                # to:
                #
                #     20160510_232553_UTM14_mos_HH_8bit_MED3x3.tif
                #     0        1      2     3   4  5    6
                #
                # so polarization can be found at index value 3.
                sarBaseName = os.path.basename(sarImage)
                polarization = sarBaseName.split("_")[4]
                for waterThreshold in waterThresholds:
                    if polarization == waterThreshold[0]:
                        minThreshold   = waterThreshold[1]
                        maxThreshold   = waterThreshold[2]
                        thresholdRange = range(minThreshold, maxThreshold+1)
                        break
                # Feedback
                msgText = "- IMAGE [%d]\n"                        \
                          "  - Files\n"                           \
                          "    - Source 8-Bit SAR Image : %s\n"   \
                          "      - Polarization         : %s\n"   \
                          "      - Threshold Range      : %s\n\n" \
                          "    - Temp Files\n"                    \
                          "      - Raster-To-Polygon    : %s\n"   \
                          "      - Polygon Flood-Only   : %s\n" % \
                         (i, sarImage, polarization, thresholdRange,
                             tempRaster2Poly, tempPolyFloodOnly)
                arcpy.AddMessage(msgText)

                # Create flood vectors for all thresholds in range specified,
                # inclusively.
                for j in thresholdRange:
                    # Variable setup for automatic output file naming, SQL and whereClause
                    outBaseName  = "%s_thr_%d_%sha%s.shp" % \
                                   (sarBaseName[0:-16], j, str(minPolygonSize).replace('.','p'), filepartProcMask)
                    outShapefile     = os.path.join(owfepDir, outBaseName)
                    whereClauseWater = '"Value" > 0 AND "Value" <= ' + str(j)
                    msgText = "    - Target Flood Shapefile : %s\n"   \
                              "      - Threshold Upper Limit: %d\n"   \
                              "      - Where Clauses\n"               \
                              "        - Area               : %s\n"   \
                              "        - Water              : %s\n"   \
                              "      - Processing"                  % \
                              (outShapefile, j, whereClauseArea, whereClauseWater)
                    arcpy.AddMessage(msgText)

                    # Apply Con to raster to identify flooded pixels as those
                    # whose bit value lies between 0 and the current threshold
                    # value.
                    # http://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-analyst-toolbox/con-.htm
                    arcpy.SetProgressorLabel("Apply CON Tool To SAR Image To Identify Flood Pixels...")
                    arcpy.AddMessage("        - Apply CON Tool To SAR Image To Identify Flood Pixels")
                    conObj = Con(sarImage, 1, 0, whereClauseWater)

                    # Apply Focal Statistics to adjust cell values.  Smoothing
                    # is done by assigning the majority value of a 5x5
                    # rectangular window to each cell, used to reduce the number
                    # of 'holes' in the flood/non-flood regions, and therefore
                    # the number of polygons to be generated during the next
                    # step.
                    # http://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-analyst-toolbox/focal-statistics.htm
                    arcpy.SetProgressorLabel("Apply 5x5 Majority Focal Stats Filter To Flood Raster...")
                    arcpy.AddMessage("        - Apply 5x5 Majority Focal Stats Filter To Flood Raster")
                    fsObj = FocalStatistics(conObj, "Rectangle 5 5 CELL", "MAJORITY", "DATA")
                    del conObj # Recover memory

                    # Convert raster to polygon.  When a field is not specified
                    # for fourth parameter, the cell values of the input raster
                    # (the VALUE field) will become a column with the heading
                    # GRIDCODE in the attribute table of the output feature
                    # class.  By applying the CON tool earlier, these will
                    # either be 0 (no water) or 1 (water).
                    # http://pro.arcgis.com/en/pro-app/tool-reference/conversion/raster-to-polygon.htm
                    arcpy.SetProgressorLabel("Convert Flood Raster To Vector Polygon Shapefile...")
                    arcpy.AddMessage("        - Convert Flood Raster To Vector Polygon Shapefile")
                    arcpy.RasterToPolygon_conversion(fsObj, tempRaster2Poly, "NO_SIMPLIFY", "")
                    del fsObj # Recover memory

                    # Remove all non-flooded polygons (those with GRIDCODE = 0)
                    # and save to new shapefile.  This will also reduce the
                    # extent when the extremities consist of non-flooded regions.
                    # http://pro.arcgis.com/en/pro-app/tool-reference/analysis/select.htm
                    arcpy.SetProgressorLabel("Remove Non-Flooded Polygons From Shapefile...")
                    arcpy.AddMessage("        - Remove Non-Flooded Polygons From Shapefile")
                    arcpy.Select_analysis(tempRaster2Poly, tempPolyFloodOnly, "GRIDCODE > 0")

                    # Shape area will be in square metres.  Convert and save to
                    # hectares.  Will require field to be created for new value.
                    # http://pro.arcgis.com/en/pro-app/tool-reference/data-management/calculate-field.htm
                    arcpy.SetProgressorLabel("Add And Populate Area-In-Hectares Field...")
                    arcpy.AddMessage("        - Add And Populate Area-In-Hectares Field")
                    arcpy.AddField_management(tempPolyFloodOnly, "Area_ha", "FLOAT", "", "", "", "", "NON_NULLABLE", "NON_REQUIRED", "")
                    arcpy.CalculateField_management(tempPolyFloodOnly, "Area_ha", "!Shape!.area/10000", "PYTHON_9.3", "")
                    
                    # Final step: remove all flooded polygons smaller than
                    # specified minimum size.
                    msgText = "Create Final Shapefile With Flood Polygons >= %.2f Ha" % (minPolygonSize)
                    arcpy.SetProgressorLabel("%s..." % (msgText))
                    arcpy.AddMessage("        - %s\n" % (msgText))
                    arcpy.Select_analysis(tempPolyFloodOnly, tempOutShapefile, whereClauseArea)
                    arcpy.EliminatePolygonPart_management(tempOutShapefile,outShapefile, "AREA", str(minPolygonSize) + " Hectares","", "ANY")

            #-------------------------------------------------------------------
            #                               DONE
            #-------------------------------------------------------------------
            # If reach this point without Exception, assign a "Success" status
            # for return in "finally" block.
            status = 0


        except (Exception), ex:
            line, filename, err = self.trace()
            msgText  = "ERROR:  Encountered exception in 'FT3_ExtractFloodExtentAndConvertToVector.execute'.\n%s\n" % (ex)
            msgText += "        At line %s of file '%s'." % (str(line), filename)
            arcpy.AddError(msgText)
            # Assign a "Failure" status for return in "finally" block.
            status = 1

        finally:
            # Check in the Spatial Analyst extension
            arcpy.CheckInExtension("Spatial")

            # Clean up memory and temp files, if they exist (ie. created and not
            # previously removed before any exception redirection).  Will use
            # arcpy to do so rather than Python operating system functions
            # because the 'files' will actually consist of sets of files and
            # directories that share the same root names, and arcpy methods will
            # remove all related files.
            arcpy.SetProgressorLabel("Remove Temporary Files...")
            arcpy.AddMessage("Remove Temporary Files\n")
            try:
                try:
                    del conObj
                except:
                    pass
                try:
                    del fsObj
                except:
                    pass
                if tempRaster2Poly:
                    if arcpy.Exists(tempRaster2Poly):
                        arcpy.Delete_management(tempRaster2Poly, "")
                if tempPolyFloodOnly:
                    if arcpy.Exists(tempPolyFloodOnly):
                        arcpy.Delete_management(tempPolyFloodOnly, "")

                # Gather any remaining directory contents (eg. "info" directory
                # and log file, for example), then iterate and remove each item,
                # either by pruning directory trees or deleting individual files.
                if scratchDir:
                    contents = [os.path.join(scratchDir, i) for i in os.listdir(scratchDir)]
                    [shutil.rmtree(i) if os.path.isdir(i) else os.unlink(i) for i in contents]

            except (Exception), ex:
                line, filename, err = self.trace()
                msgText  = "WARNING:  Encountered exception in "                 \
                           "'FT3_ExtractFloodExtentAndConvertToVector.execute' " \
                           "while removing temporary files.\n%s\n" % (ex)
                msgText += "          At line %s of file '%s'." % (str(line), filename)
                arcpy.AddWarning(msgText)

            return status


    ############################################################################
    ##                         NON-STANDARD METHODS                           ##
    ############################################################################
    ## The methods that follow have been listed in alphabetical order and are ##
    ## supplemental to the above standard methods that ArcGIS requires and    ##
    ## provides in skeletal format whenever a Python Toolbox is created.      ##
    ############################################################################

    # ================ #
    # Instance Methods #
    # ================ #
    def load8BitSarImageField(self, parameters):
        """
        When user enters a value into the Workspace data entry field, will
        retrieve a list of all scaled filtered polarized SAR images found in the
        "Scaled" subdirectory and load them into the "Scaled Filtered 8-Bit SAR
        Image" list field.  It will also make a single default selection to be
        processed using the following rules:
        - If only 1 file exists, that file will be chosen.
        - If multiple files exist and one of them is for the "HH" polarization
          channel, that file will be chosen.  Otherwise the first file will be
          selected.

        Parameters:
            TYPE        NAME            DESCRIPTION
            Parameter[] parameters      List of Parameter objects created for
                                        this class.  Will use elements 0, 1
                                        (Workspace, Scaled Filtered 8-Bit SAR
                                        Image) of this list.

        Return Values:
            None

        Limit(s) and Constraint(s) During Use:
            None.
        """
        if parameters[0].value != None:
            parameters[1].filter.list \
            = glob.glob(os.path.join(str(parameters[0].value),'Scaled','*.tif'))
            if len(parameters[1].filter.list) == 1:
                parameters[1].values = parameters[1].filter.list
            elif len(parameters[1].filter.list) > 1:
                selectedFile = 0
                for i in range(len(parameters[1].filter.list)):
                    fileName = os.path.basename(parameters[1].filter.list[i])
                    if "_HH_8bit_" in fileName:
                        selectedFile = i
                        break
                parameters[1].values = [parameters[1].filter.list[selectedFile]]


    def trace(self):
        """
        Provides additional details about the line of code that has triggered
        an Exception, useful for debugging.

        Parameters:
            TYPE        NAME            DESCRIPTION
            None

        Return Values:
            String[]
            - A 3-element list that provides additional details about the line
              of code that has triggered an Exception.  This includes the line
              number, the file number and the Exception text.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        tb       = sys.exc_info()[2]
        tbinfo   = traceback.format_tb(tb)[0]
        line     = tbinfo.split(", ")[1]
        filename = os.path.join(sys.path[0], "FT3_ExtractFloodExtentAndConvertToVector.py")
        synerror = traceback.format_exc().splitlines()[-1]
        return line, filename, synerror


    # ============= #
    # Class Methods #
    # ============= #
    # NOTE: These have been created as Class rather than Instance methods to
    #       accomodate integration of this modules into the FT0_FloodTools
    #       wrapper.
    @staticmethod
    def validate8BitSARFiles(fileList):
        """
        Confirms that at least one scaled filtered polarized 8-bit SAR image has
        been selected, and that the selected items exist and the user has access
        privileges to them.  Returns an error message if not.

        Parameters:
            TYPE        NAME            DESCRIPTION
            String[]    fileList        A list of 8-bit SAR image paths and
                                        names that are to have their flood
                                        extents extracted and converted to
                                        vector format.

        Return Values:
            String
            -  None  List of 8-bit input files is valid.
            - !None  8-bit input file(s) was not passed, or the path to one of
                     its files does not exist or is not accessible.  Value
                     returned will be an error message that can be displayed to
                     the user or recorded in the Results window or log file.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        msgText = None
        if fileList == None or len(fileList) == 0:
            msgText = "ERROR:  No 8-bit SAR image file(s) have been selected."
        else:
            for filePath in fileList:
                filePath = str(filePath)
                if not os.path.isfile(filePath) or not os.access(filePath, os.R_OK):
                    msgText = "ERROR:  8-bit SAR image file '%s' does not " \
                              "exist or is not accessible." % (filePath)
                    break
        if msgText:
            return msgText
        else:
            return None


    @staticmethod
    def validateMinimumPolygonSize(minPolygonSize):
        """
        Confirms that minimum polygon size is defined, is a number, and is > 0.
        Returns an error message if not.

        Parameters:
            TYPE        NAME            DESCRIPTION
            Float       minPolygonSize  The minimum polygon size, used to filter
                                        out 'noise' in the flooded region,
                                        ensuring that only significantly large
                                        enough contiguous regions are included
                                        in the flood map.

        Return Values:
            String
            -  None  Minimum polygon size is valid.
            - !None  Minimum polygon size was not passed, is not a number or is
                     not > 0.  Value returned will be an error message that can
                     be displayed to the user or recorded in the Results window
                     or log file.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        msgText = None
        if minPolygonSize == None:
            msgText = "ERROR:  Minimum Polygon Size has not been defined."
        elif not isinstance(minPolygonSize, float):
            msgText = "ERROR:  Minimum Polygon Size '%s' is not a floating " \
                      "point number." % (str(minPolygonSize))
        elif minPolygonSize <= 0:
            msgText = "ERROR:  Minimum Polygon Size '%s' must be > 0." % \
                      (str(minPolygonSize))
        return msgText


    @staticmethod
    def validateProcessingMask(processingMask):
        """
        Confirms that optional processing mask, when defined, exists and that
        the user has access privileges.  Returns an error message if not.

        Parameters:
            TYPE        NAME            DESCRIPTION
            String      processingMask  The path and name of the processing mask
                                        file used to clip flood map to relevant
                                        regions.  Since mask is optional, this
                                        parameter may be none, in which case it
                                        will be considered to be valid.

        Return Values:
            String
            -  None  Processing mask is valid.
            - !None  Processing mask does not exist or it is not accessible.
                     Value returned will be an error message that can be
                     displayed to the user or recorded in the Results window or
                     log file.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        msgText = None
        if processingMask != None:
            if not os.path.isfile(processingMask) or not os.access(processingMask, os.R_OK):
                msgText = "ERROR:  Processing Mask '%s' does not exist or is " \
                          "not accessible." % (processingMask)
        return msgText


    @staticmethod
    def validateWaterThresholds(paramSARImages, paramWaterThresholds):
        """
        Performs extensive validations on water thresholds, automatically
        adjusting values where possible.  Steps performed:
        - rejects and removes unsupported polarizations
        - rejects and removes duplicate   polarizations
        - scans list of selected SAR images and ensures associated polarization/
          water thesholds are present, adding defaults for them if not, and
          issuing a fatal error if any image has an unsupported polarization
        - removes polarization/water mask records that do not have an associated
          SAR image
        - ensures that MIN/MAX water thresholds are present and are valid

        Parameters:
            TYPE        NAME            DESCRIPTION
            Parameter   paramSARImages  List of SAR images, if any that user has
                                        selected for processing.  By passing an
                                        Arcpy "Parameter" object, access is
                                        provided to all of its properties, most
                                        important of which is its "values".
            Parameter   paramWaterThresholds
                                        List of polarizations and water
                                        thresholds contained within a ValueTable.
                                        Prior to selecting SAR images, will
                                        initially contain all supported
                                        polarizations and their default
                                        thresholds.  After selecting SAR images,
                                        will only contain those items that are
                                        directly associated with the selected
                                        images.  By passing an Arcpy "Parameter"
                                        object, access is provided to all of its
                                        properties, most important of which are
                                        its "values" and "parameterDependencies".
                                        The object provides 'by reference'
                                        access to those properties so the list
                                        can be altered herein and have the
                                        changes show up in the GUI and calling
                                        function, a technique used to remove
                                        items that are incorrect, or add items
                                        that are missing.

        Return Values:
            String
            -  None  The list of polarizations and associated water thresholds
                     are valid.
            - !None  A problem was encountered with a polarization/water
                     threshold record.  Where possible, steps may have been
                     taken within this method to correct the problem, but the
                     caller will be made aware of what was done through this
                     value.  Value returned will either be a warning or error
                     message that can be displayed to the user or recorded in
                     the Results window or log file.  The message will either
                     start with key word "WARNING:" or "ERROR:", respectively,
                     that the caller can extract to determine what sort of alert
                     to issue.  In the former case, often a repair will have
                     been done herein, so the script execution can proceed; in
                     the latter case, execution cannot proceed without the user
                     making a change.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        msgText = None

        # List of Selected SAR files
        if paramSARImages:
            sarImages = paramSARImages.values
        else:
            sarImages = None
        # List of Water Thresholds, Valid Polarizations
        if paramWaterThresholds:
            waterThresholds    = paramWaterThresholds.values
            validPolarizations = paramWaterThresholds.parameterDependencies
        else:
            waterThresholds    = None
            validPolarizations = None

        # Check for Invalid Polarizations
        if waterThresholds and validPolarizations:
            for i, waterThreshold in enumerate(waterThresholds):
                if waterThreshold[0] not in validPolarizations:
                    msgText = "WARNING:  Invalid Polarization '%s'.  Must be " \
                              "one of '%s'.  Removed." %                       \
                              (waterThreshold[0], ','.join(validPolarizations))
                    del waterThresholds[i]
                    break
            # Reset ValueTable contents
            if msgText:
                paramWaterThresholds.values = waterThresholds

        # Check for Duplicate Polarizations, Remove latest if found
        if waterThresholds:
            for i in range(len(waterThresholds)-1, -1, -1):
                for j in range(i):
                    if waterThresholds[i][0] == waterThresholds[j][0]:
                        msgText = "WARNING:  Duplicate Polarization '%s'.  " \
                                  "Removed." % (waterThresholds[i][0])
                        del waterThresholds[i]
                        break
            # Reset ValueTable contents
            if msgText:
                paramWaterThresholds.values = waterThresholds

        # Check for Image Files that don't have Water Threshold defined.  File
        # names will be similar to:
        #
        #     20160510_232553_UTM14_mos_HH_8bit_MED3x3.tif
        #     0        1      2     3   4  5    6
        #
        # so polarization can be found at index value 3.
        if sarImages:
            for sarImage in sarImages:
                # Extract image polarization and determine if its water
                # thresholds are currently loaded.
                sarBaseName     = os.path.basename(sarImage)
                polarization    = sarBaseName.split("_")[4]
                thresholdExists = False
                if waterThresholds:
                    for waterThreshold in waterThresholds:
                        if polarization == waterThreshold[0]:
                            thresholdExists = True
                            break
                # If water mask thresholds have not been loaded for current
                # polarization, assign default values (if they exist)
                if thresholdExists == False:
                    for waterThreshold in FT3_ExtractFloodExtentAndConvertToVector.DEFAULT_WATERTHRESHOLDS:
                        if polarization == waterThreshold[0]:
                            if waterThresholds:
                                waterThresholds.append(waterThreshold)
                            else:
                                waterThresholds = [waterThreshold]
                            # Reset ValueTable contents
                            paramWaterThresholds.values = waterThresholds
                            thresholdExists = True
                            msgText = "ATTENTION:  Assigned default water " \
                                      "thresholds for polarization '%s'.  " \
                                      "Adjust its MIN/MAX values if "       \
                                      "incorrect." % (waterThreshold[0])
                            break
                # Image contains unsupported polarization.  Will require code
                # change to introduce -- trigger error.
                if thresholdExists == False:
                    msgText = "ERROR:  SAR Image '%s' employs unsupported "   \
                              "polarization '%s'.  Will require code change " \
                              "in order to use." % (sarBaseName, polarization)

        # Now that all images and thresholds have been scrutinized for potential
        # errors, clean up by removing any water mask thresholds that do not
        # have a corresponding image loaded.
        if sarImages and waterThresholds:
            for i in range(len(waterThresholds)-1, -1, -1):
                thresholdExists = False
                for sarImage in sarImages:
                    polarization = os.path.basename(sarImage).split("_")[4]
                    if polarization == waterThresholds[i][0]:
                        thresholdExists = True
                        break
                if thresholdExists == False:
                    del waterThresholds[i]
            # Reset ValueTable contents
            paramWaterThresholds.values = waterThresholds

        # Final check.  Ensure MIN/MAX water thresholds are defined.
        for waterThreshold in waterThresholds:
            if waterThreshold[1] == None:
                msgText = "ERROR:  MIN water threshold is missing for " \
                          "polarization '%s'." % (waterThreshold[0])
            elif waterThreshold[1] < 0:
                msgText = "ERROR:  MIN water threshold '%d' must be >= 0 for " \
                          "polarization '%s'." %                               \
                          (waterThreshold[1], waterThreshold[0])
            elif waterThreshold[2] == None:
                msgText = "ERROR:  MAX water threshold is missing for " \
                          "polarization '%s'." % (waterThreshold[0])
            elif waterThreshold[2] < 0:
                msgText = "ERROR:  MAX water threshold '%d' must be >= 0 for " \
                          "polarization '%s'." %                               \
                          (waterThreshold[2], waterThreshold[0])
            elif waterThreshold[1] > waterThreshold[2]:
                msgText = "ERROR:  MIN water threshold '%d' must be <= "      \
                          "MAX water threshold '%d' for polarization '%s'." % \
                          (waterThreshold[1], waterThreshold[2], waterThreshold[0])

        if msgText:
            return msgText
        else:
            return None


    @staticmethod
    def validateWorkspace(workspace):
        """
        Confirms that Workspace directory and Scaled subdirectories exist, the
        user has access privileges, and that at least 1 SAR image is present
        within the Scaled directory.  Returns an error message if not.

        Parameters:
            TYPE        NAME            DESCRIPTION
            String      workspace       The path and name of the workspace
                                        directory below which all flood work
                                        is to take place and the Mosaic
                                        subdirectory and its polarized SAR
                                        images can be found.

        Return Values:
            String
            -  None  Workspace is valid and contains desired SAR images.
            - !None  Workspace was not passed, its path does not
                     exist or it is not accessible, or Scaled subdirectory does
                     not exist, is not accessible. or does not contain scaled
                     filtered polarized SAR images.  Value returned will be an
                     error message that can be displayed to the user or recorded
                     in the Results window or log file.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        msgText = None
        if workspace == None or len(workspace) == 0:
            msgText = "ERROR:  Workspace has not been defined."
        elif not os.path.isdir(workspace) or not os.access(workspace, os.R_OK):
            msgText = "ERROR:  Workspace '%s' does not exist or is not " \
                      "accessible." % (workspace)
        else:
            scaledDir = os.path.join(workspace, "Scaled")
            if not os.path.isdir(scaledDir) or not os.access(scaledDir, os.R_OK):
                msgText = "ERROR:  Scaled directory '%s' in which scaled " \
                          "filtered polarized 8-bit SAR images are to be " \
                          "found does not exist or is not accessible." %   \
                          (scaledDir)
            else:
                sarImageList = glob.glob(os.path.join(scaledDir,"*.tif"))
                if sarImageList == None or len(sarImageList) == 0:
                    msgText = "ERROR:  Scaled directory '%s' does not " \
                              "contain 'tif' file SAR images." % (scaledDir)
        return msgText


def main():
    """
        Allows FT3_ExtractFloodExtentAndConvertToVector Tool to be executed from
        commmand line instead of GUI.

        Function "main()" allows the FT3_ExtractFloodExtentAndConvertToVector
        module to be run as a script in batch, called from the command line or
        managing script rather than through a Toolbox in ArcCatalog or ArcMap,
        thereby bypassing the GUI interface provided by the Toolbox.  In this
        way, the application can be added to a processing chain, overseen by an
        orchestrating parent process, without requiring manual intervention
        between steps.  It uses argparse to exchange parameters with the command
        line.

        Usage:
            FT3_ExtractFloodExtentAndConvertToVector.py [-h] -img8 IMAGE8BIT
                                                        [-mask PROCESSINGMASK]
                                                        [-mps MINPOLYGONSIZE]
                                                        -ws WORKSPACE
                                                        [-wt WATERTHRESHOLD]

        Parameters:
            Parameters that take a file name will accept either relative or
            absolute paths.

            -h,                         Optional
            --help
                                        Show this help message and exit.

            -img8 IMAGE8BIT,                Mandatory
            --image8bit IMAGE8BIT
                                        8-bit Scaled Filtered Image(s).  One or
                                        more 8-bit scaled filtered images
                                        produced by the "FT2_Scale16to8BitSet"
                                        tool.  These images should reside in the
                                        'Scaled' subdirectory, and each should
                                        represent a different polarization
                                        channel (HH, HV, VV, VH).  When more
                                        than one image is passed, must be as a
                                        quoted semi-colon delimitted string.
                                        Example:
                                        "D:\Floods\QC_Richelieu\20110507_225926_F6F\Scaled\20110507_225926_UTM18_mos_HH_8bit_MED3x3.tif;D:\Floods\QC_Richelieu\20110507_225926_F6F\Scaled\20110507_225926_UTM18_mos_HV_8bit_MED3x3.tif"

            -mask PROCESSINGMASK,       Optional
            --procmask PROCESSINGMASK
                                        Processing Mask.  Optional mask used to
                                        clip the flood extent to a buffer
                                        surrounding the subject water body /
                                        Area Of Interest, thereby restricting
                                        output to a specific region.  Can either
                                        be a raster or vector.  If raster format
                                        (.img, .tif, or grid), must be of type
                                        integer where 1='area to process' and
                                        the remainder is set to NO DATA (zero
                                        values will not work).  If not passed,
                                        water found throughout the full frame /
                                        mosiac will be incorporated in the final flood product.
                                        Example:
                                        D:\Floods\BaseData\QC\ProcessingMask\QC_Richelieu_Mask_7p5km.shp

            -mps MINPOLYGONSIZE,        Optional
            --minpolysize MINPOLYGONSIZE
                                        Minimum Polygon Size (ha).  Establishes
                                        a minimum area, in hectares, that a
                                        water polygon must meet or exceed to be
                                        incorporated in the final flood product.
                                        Used to exclude what could be considered
                                        'noise' and retain areas of significance
                                        within the image.  To keep all polygons,
                                        simply set the value to 0.  Is required
                                        by the tool, however if not passed, will
                                        default to a value of 2.5.
                                        Example:
                                        2.0

            -ws WORKSPACE,              Mandatory
            --workspace WORKSPACE
                                        Workspace.  Root directory that contains
                                        the 'Scaled' subdirectory where the
                                        "FT2_Scale16to8BitSet" tool has placed
                                        scaled filtered SAR images during the
                                        second step of producing a Flood
                                        Product.  Script will create
                                        subdirectories 'OWFEP' and 'Scratch' if
                                        they are not already present, and will
                                        transform the scaled filtered images
                                        identified by the "-img" flag from
                                        raster into vector polygon shapefiles
                                        that represent the flooded regions.  A
                                        separate shapefile will be produced for
                                        each different water threshold value.
                                        Example:
                                        D:\Floods\QC_Richelieu\20110507_225926_F6F

            -wt WATERTHRESHOLD,
            --waterthreshold WATERTHRESHOLD
                                        Water Threshold(s).  Sets of
                                        polarizations and corresponding minimum
                                        and maximum water thresholds that will
                                        be used to create a series of output
                                        flood products.  A set is required for
                                        each polarization identified by the
                                        "-pol" flag (or for the default
                                        polarization established by the tool
                                        when "-pol" isn't passed).  The minimum
                                        and maximum water thresholds define the
                                        endpoints for a range of thresholds that
                                        will be used to generate products.  Bit
                                        values from 0 to each threshold will be
                                        classified as water in the 8-bit images
                                        to be created.  While these are required
                                        by the tool, if not passed, default
                                        values will be assigned as follows:
                                        - ['HH', 10, 12]
                                        - ['HV', 4, 6]
                                        - ['VV', 4, 6]
                                        - ['VH', 10, 12]
                                        When passed, must be expressed as nested
                                        Python list(s) within double-quotes.
                                        Examples:
                                        "[['HH', 10, 12]]"
                                        "[['HH', 10, 12], ['HV', 4, 6]]"


        Return Values:
            Check on Windows OS with "echo %ERRORLEVEL%" after run.
            0       Successfully completed
            1       Error encountered during run.  Check messages issued to
                    standard output for details.
            2       Returned by "argparse" when mandatory parameter has not been
                    passed.


        Examples:
            Process Single Image, Use Defaults
            ----------------------------------
            C:\Python27\ArcGISx6410.3\python.exe FT3_ExtractFloodExtentAndConvertToVector.py ^
            -ws "D:\Floods\QC_Richelieu\20110507_225926_F6F" ^
            -img "D:\Floods\QC_Richelieu\20110507_225926_F6F\Scaled\20110507_225926_UTM18_mos_HH_8bit_MED3x3.tif"

            Process Multiple Images, Pass All Optional Parameters
            -----------------------------------------------------
            C:\Python27\ArcGISx6410.3\python.exe FT3_ExtractFloodExtentAndConvertToVector.py ^
            -ws "D:\Floods\QC_Richelieu\20110507_225926_F6F" ^
            -img "D:\Floods\QC_Richelieu\20110507_225926_F6F\Scaled\20110507_225926_UTM18_mos_HH_8bit_MED3x3.tif;D:\Floods\QC_Richelieu\20110507_225926_F6F\Scaled\20110507_225926_UTM18_mos_HV_8bit_MED3x3.tif"
            -wt "[['HH', 9, 13], ['HV', 3, 7]]" ^
            -mps 3.0 ^
            -mask "D:\Floods\BaseData\ProcessingMask\ON_AlbanyRiverForks_7p5km_smooth.tif"

        Limit(s) and Constraint(s) During Use:
            Must be submitted through 64-bit Python.
    """
    # SAMPLE CALLS FOR TESTING
    #
    # GET USAGE / HELP (MUST Use 64-bit Python)
    # C:\Python27\ArcGISx6410.3\python.exe FT3_ExtractFloodExtentAndConvertToVector.py -h
    #
    # CONVERT BOTH HH AND HV IMAGES TO 8-BIT
    # C:\Python27\ArcGISx6410.3\python.exe FT3_ExtractFloodExtentAndConvertToVector.py ^
    # -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" ^
    # -img "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Mosaic\20160510_232540_UTM16_mos_HH_8bit_MED3x3.tif;E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Scaled\20160510_232540_UTM16_mos_HV_8bit_MED3x3.tif"
    #
##C:\Python27\ArcGISx6410.3\python.exe FT3_ExtractFloodExtentAndConvertToVector.py -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" -img "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Scaled\20160510_232540_UTM16_mos_HH_8bit_MED3x3.tif;E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Scaled\20160510_232540_UTM16_mos_HV_8bit_MED3x3.tif"
##C:\Python27\ArcGISx6410.3\python.exe FT3_ExtractFloodExtentAndConvertToVector.py -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" -img "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Scaled\20160510_232540_UTM16_mos_HH_8bit_MED3x3.tif" -wt "[['HH', 11, 12]]"

    DEBUG = False   # Set to True to see incoming parameters before "execute"
##    DEBUG = True    # Set to True to see incoming parameters before "execute"
    try:
        if DEBUG:
            print 'Argument List:\n', str(sys.argv)

        # Get Command Line Arguments (if running in batch and not through GUI)
        parser = argparse.ArgumentParser(
                            formatter_class=argparse.RawTextHelpFormatter,
                            description=
                            "Converts 8-bit scaled filtered SAR images to " +
                            "series of vector polygon\n"                    +
                            "shapefiles that represent flooded regions at " +
                            "various water threshold values, as\n"          +
                            "third step in producing Flood Product.\n",
                            epilog=
                            "Examples:\n"                                                                               +
                            "- Process Single Image, Use Defaults\n"                                                    +
                            "  C:\\Python27\\ArcGISx6410.3\\python.exe FT3_ExtractFloodExtentAndConvertToVector.py ^\n" +
                            "  -ws \"D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\" ^\n"                               +
                            "  -img \"D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\\Scaled\\20110507_225926_UTM18_mos_HH_8bit_MED3x3.tif\"\n\n" +
                            "- Process Multiple Images, Pass All Optional Parameters\n"                                 +
                            "  C:\\Python27\\ArcGISx6410.3\\python.exe FT3_ExtractFloodExtentAndConvertToVector.py ^\n" +
                            "  -ws \"D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\" ^\n"                               +
                            "  -img \"D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\Scaled\\20110507_225926_UTM18_mos_HH_8bit_MED3x3.tif;"       +
                            "D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\\Scaled\\20110507_225926_UTM18_mos_HV_8bit_MED3x3.tif\"\n"            +
                            "  -wt \"[['HH', 9, 13], ['HV', 3, 7]]\" ^\n"                                               +
                            "  -mps 3.0 ^\n"                                                                            +
                            "  -mask \"D:\\Floods\\BaseData\\QC\\ProcessingMask\\QC_Richelieu_Mask_7p5km.shp\"\n\n")
        parser.add_argument('-img8', '--image8bit',
                            required=True, action='store', dest='image8bit',
                            help="8-bit Scaled Filtered Image(s).  One or more 8-bit\n"    +
                                 "scaled filtered images produced by the\n"                +
                                 "\"FT2_Scale16to8BitSet\" tool.  These images should\n"   +
                                 "reside in the 'Scaled' subdirectory, and each should\n"  +
                                 "represent a different polarization channel (HH, HV,\n"   +
                                 "VV, VH).  When more than one image is passed, must be\n" +
                                 "as a quoted semi-colon delimitted string.\n"             +
                                 "Example:\n"                                              +
                                 "\"D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\\Scaled\\20110507_225926_UTM18_mos_HH_8bit_MED3x3.tif;" +
                                 "D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\\Scaled\\20110507_225926_UTM18_mos_HV_8bit_MED3x3.tif\"\n")
        parser.add_argument('-mask', '--procmask',
                            required=False, action='store', dest='processingmask',
                            help="Processing Mask.  Optional mask used to clip the flood\n"  +
                                 "extent to a buffer surrounding the subject water body /\n" +
                                 "Area Of Interest, thereby restricting output to a\n"       +
                                 "specific region.  Can either be a raster or vector.  If\n" +
                                 "raster format (.img, .tif, or grid), must be of type\n"    +
                                 "integer where 1='area to process' and the remainder is\n"  +
                                 "set to NO DATA (zero values will not work).  If not\n"     +
                                 "passed, water found throughout the full frame / mosiac\n"  +
                                 "will be incorporated in the final flood product.\n"        +
                                 "Example:\n"                                                +
                                 "D:\\Floods\\BaseData\\QC\\ProcessingMask\\QC_Richelieu_Mask_7p5km.shp\n")
        parser.add_argument('-mps', '--minpolysize',
                            required=False, action='store', dest='minpolygonsize',
                            help="Minimum Polygon Size (ha).  Establishes a minimum area,\n" +
                                 "in hectares, that a water polygon must meet or exceed\n"   +
                                 "to be incorporated in the final flood product.  Used to\n" +
                                 "exclude what could be considered 'noise' and retain\n"     +
                                 "areas of significance within the image.  To keep all\n"    +
                                 "polygons, simply set the value to 0.  Is required by\n"    +
                                 "the tool, however if not passed, will default to a\n"      +
                                 "value of 2.5.\n"                                           +
                                 "Example:\n"                                                +
                                 "2.0\n")
        parser.add_argument('-ws', '--workspace',
                            required=True, action='store', dest='workspace',
                            help="Workspace.  Root directory that contains the 'Scaled'\n"    +
                                 "subdirectory where the \"FT2_Scale16to8BitSet\" tool has\n" +
                                 "placed scaled filtered SAR images during the second\n"      +
                                 "step of producing a Flood Product.  Script will create\n"   +
                                 "subdirectories 'OWFEP' and if 'Scratch' they are not\n"     +
                                 "already present, and will transform the scaled filtered\n"  +
                                 "images identified by the \"-img\" flag from raster into\n"  +
                                 "vector polygon shapefiles that represent the flooded\n"     +
                                 "regions.  A separate shapefile will be produced for\n"      +
                                 "each different water threshold value.\n"                    +
                                 "Example:\n"                                                 +
                                 "D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\n")
        parser.add_argument('-wt', '--waterthreshold',
                            required=False, action='store', dest='waterthreshold',
                            help="Water Threshold(s).  Sets of polarizations and\n"           +
                                 "corresponding minimum and maximum water thresholds that\n"  +
                                 "will be used to create a series of output flood\n"          +
                                 "products.  A set is required for each polarization\n"       +
                                 "identified by the \"-pol\" flag (or for the default\n"      +
                                 "polarization established by the tool when \"-pol\" isn't\n" +
                                 "passed).  The minimum and maximum water thresholds\n"       +
                                 "define the endpoints for a range of thresholds that\n"      +
                                 "will be used to generate products.  Bit values from 0\n"    +
                                 "to each threshold will be classified as water in the\n"     +
                                 "8-bit images to be created.  While these are required\n"    +
                                 "by the tool, if not passed, default values will be\n"       +
                                 "assigned as follows:\n"                                     +
                                 str(FT3_ExtractFloodExtentAndConvertToVector.DEFAULT_WATERTHRESHOLDS).replace("[[","- [").replace("]]","]").replace("], ","]\n- ") + "\n" +
                                 "When passed, must be expressed as nested Python list(s)\n"  +
                                 "within double-quotes.\n"                                    +
                                 "Examples:\n"                                                +
                                 "\"[['HH', 10, 12]]\"\n"                                     +
                                 "\"[['HH', 10, 12], ['HV', 4, 6]]\"\n")
        cmdLineFlags = parser.parse_args()


        # Create FT3_ExtractFloodExtentAndConvertToVector object and initialize
        # its parameters.  Make sure relative paths are expressed as absolute
        # paths or may get error.
        #
        # Since "images" may be a semi-colon delimitted string, must first
        # convert each member of string is in absolute path format, easiest done
        # by first converting to list, setting each list member, then converting
        # back to delimiited string.
        ft3Obj = FT3_ExtractFloodExtentAndConvertToVector()
        params = ft3Obj.getParameterInfo()

        params[0].value = os.path.abspath(cmdLineFlags.workspace)
        images          = cmdLineFlags.image8bit.split(';')
        for i in range(0, len(images)):
            images[i] = os.path.abspath(images[i])
        params[1].value = ';'.join(images)

        if cmdLineFlags.waterthreshold:
            # Convert string argument to nested list objects, then use
            # validation method to ensure that any missing items are assigned
            # defaults.
            params[2].values = eval(cmdLineFlags.waterthreshold)
            FT3_ExtractFloodExtentAndConvertToVector.validateWaterThresholds(
                            params[1], params[2])  # SAR files, Water Thresholds

        if cmdLineFlags.minpolygonsize:
            params[3].value = float(cmdLineFlags.minpolygonsize)
        if cmdLineFlags.processingmask:
            params[4].value = os.path.abspath(cmdLineFlags.processingmask)


        if DEBUG:
            print "- Parameters To Be Passed To \"execute\" Method:"
            for param in params:
                print "  - "   + param.displayName
                print "    - TYPE : " + str(param.datatype)
                print "    - VALUE: " + str(param.value)

        # Submit job and return exit status to OS (can be checked with echo
        # %ERRORLEVEL% in Windows).  All arcpy.AddMessage, arcpy.AddWarning and
        # arcpy.AddError messages issued in "execute" will be sent to stdout
        # when run in batch.
        if DEBUG:
            print "- Call \"execute\":\n"
        status = ft3Obj.execute(params, None)
        if status:
            exit(1) # Failure
        else:
            exit(0) # Success


    except Exception as ex:
        logText = "ERROR:  Encountered exception in 'main':\n" \
                  "        %s." % (ex)
        print logText
        exit(1)


if __name__ == '__main__':
    main()