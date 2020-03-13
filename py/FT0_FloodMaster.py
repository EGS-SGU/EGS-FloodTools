#! /usr/bin/env python
# -*- coding: Latin-1 -*-

__revision__ = "--REVISION-- : $Id: FT0_FloodMaster.py 727 2016-12-12 16:09:54Z vneufeld $"

#==============================================================================#
# HISTORY                                                                      #
# -------                                                                      #
# Developed by V. Neufeld, September 2016.                                     #
#==============================================================================#


# Libraries
# =========
import arcpy
import argparse
import os
import sys
import time

# Reload steps required to refresh memory if Catalog is open when changes are made
import FT1_R2ReadOrthoMosaic                              # get module reference for reload
reload(FT1_R2ReadOrthoMosaic)                             # reload step 1
from   FT1_R2ReadOrthoMosaic import FT1_R2ReadOrthoMosaic # reload step 2

import FT2_Scale16to8BitSet                               # get module reference for reload
reload(FT2_Scale16to8BitSet)                              # reload step 1
from   FT2_Scale16to8BitSet  import FT2_Scale16to8BitSet  # reload step 2

import FT3_ExtractFloodExtentAndConvertToVector           # get module reference for reload
reload(FT3_ExtractFloodExtentAndConvertToVector)          # reload step 1
from   FT3_ExtractFloodExtentAndConvertToVector \
       import FT3_ExtractFloodExtentAndConvertToVector    # reload step 2


# ======= #
# Globals #
# ======= #


class FT0_FloodMaster(object):
    """
    Acts as a convenient interface to launch and manage the first 3 tools in the
    Flood Tools suite, used to produce flood products:
    - FT1_R2ReadOrthoMosaic
    - FT2_Scale16to8BitSet
    - FT3_ExtractFloodExtentAndConvertToVector

    Through this interface, can run just one tool to accomplish what the 3 tools
    listed above do.  Furthermore, it is possible to select and process multiple
    polarization channelsin one run, assigning different water threshold ranges
    customized for each, rather than have to run the tool separately for every
    channel. After examining the final output in the 'OWFEP' folder (ie. Open
    Water Flood Extent Product), it is always possible to supplement the results
    by running the individual tools separately, such as "FT2_Scale16to8BitSet"
    to process polarization channels that were not originally selected, and/or
    "FT3_ExtractFloodExtentAndConvertToVector" to select a different water
    threshold range, if the original selections of "FT0_FloodMaster" did not
    produce satisfactory results.

    The tool runs in ArcGIS background mode, required to accommodate the mix of
    32-bit and 64-bit processing that it performs.  It is possible to monitor
    progress through the "Current Session->Messages" branch of the "Results"
    panel in ArcCatalog or ArcMap.  It supports both a GUI and command-line
    interface, the latter useful for incorporating it within a larger batch
    script.

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
    idxChangeField  = None


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
        self.label              = "FT0_FloodMaster"
        self.description        = "Runs All Flood Tools"
        self.canRunInBackground = True
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
        """
        params = [None]*10

        params[0] = arcpy.Parameter(
                     displayName   = "Workspace",
                     name          = "workspace",
                     datatype      = "DEFolder",
                     parameterType = "Required",
                     direction     = "Input"
                     )
        params[0].value = None

        params[1] = arcpy.Parameter(
                     displayName   = "DEM Filename",
                     name          = "demFilename",
                     datatype      = ["DEFile","DERasterDataset"],
                     parameterType = "Required",
                     direction     = "Input"
                     )
##        params[1].filter.list = ["tif","img"]

        params[2] = arcpy.Parameter(
                        displayName   = "Ortho Projection",
                        name          = "orthoProjection",
                        datatype      = "GPString",
                        parameterType = "Required",
                        direction     = "Input"
                     )
        params[2].filter.type = "ValueList"
        params[2].filter.list = FT1_R2ReadOrthoMosaic.PREDEFINED_PROJECTIONS
        params[2].value       = "CanLCC      E008"
        # UTM Zone# + D122 which is PCI Geomatica code for NAD 83 (eg. "UTM 14 D122")
        # http://www.pcigeomatics.com/geomatica-help/references/proj_r/proj3n149.html

        params[3] = arcpy.Parameter(
                        displayName   = "Ortho Pixel Spacing",
                        name          = "orthoPixelSpacing",
                        datatype      = "GPString",
                        parameterType = "Required",
                        direction     = "Input"
                     )
        params[3].value   = "12.5,12.5"

        params[4] = arcpy.Parameter(
                        displayName   = "16-Bit Polarized SAR Image",
                        name          = "sarImage16Bit",
                        datatype      = "GPString",
##                        parameterType = "Required",
                        direction     = "Input",
                        multiValue    = "True"
                     )
        params[4].enabled     = True
        params[4].value       = None
        params[4].filter.type = "ValueList"
        params[4].filter.list = []

        params[5] = arcpy.Parameter(
                        displayName   = "Constrast Stretch",
                        name          = "constrastStretch",
                        datatype      = "GPString",
                        parameterType = "Required",
                        direction     = "Input"
                     )
        params[5].filter.type = "ValueList"
        params[5].filter.list = FT2_Scale16to8BitSet.SUPPORTED_CONTRASTSTRETCH
        params[5].value       = params[5].filter.list[0]    # "Min-Max Range"

        params[6] = arcpy.Parameter(
                        displayName   = "8-Bit Scaled Filtered SAR Image",
                        name          = "sarImage8Bit",
                        datatype      = "GPString",
                        parameterType = "Required",
                        direction     = "Input",
                        multiValue    = "True"
                     )
        params[6].enabled     = True
        params[6].value       = None
        params[6].filter.type = "ValueList"
        params[6].filter.list = []

        params[7] = arcpy.Parameter(
                     displayName   = "Water Thresholds",
                     name          = "waterThresholds",
                     datatype      = "GPValueTable",
                     parameterType = "Required",
                     direction     = "Input"
                     )
        # Limit the acceptable entries to the 4 possible polarization pairs
        params[7].columns               = [["GPString", "Polarization"],
                                           ["GPLong",   "MIN Threshold"],
                                           ["GPLong",   "MAX Threshold"]]
        params[7].values                = \
                FT3_ExtractFloodExtentAndConvertToVector.DEFAULT_WATERTHRESHOLDS
        params[7].parameterDependencies = \
                FT3_ExtractFloodExtentAndConvertToVector.SUPPORTED_POLARIZATIONS
        params[7].filters[0].type       = "ValueList"
        params[7].filters[0].list       = \
                FT3_ExtractFloodExtentAndConvertToVector.SUPPORTED_POLARIZATIONS

        params[8] = arcpy.Parameter(
                        displayName   = "Minimum Polygon Size (hectares)",
                        name          = "minPolygonSize",
                        datatype      = "GPDouble",
                        parameterType = "Required",
                        direction     = "Input"
                     )
        params[8].value = "2.5"

        params[9] = arcpy.Parameter(
                     displayName   = "Processing Mask",
                     name          = "processingMask",
                     datatype      = ["DEFeatureClass","DEFeatureDataset","DERasterDataset"],
##                     datatype      = ["DEFile","DERasterDataset"],
##                     datatype      = "DEFile",
                     parameterType = "Optional",
                     direction     = "Input"
                     )
##        params[9].filter.list = ["tif","img"]


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
        # within the "updateMessages" method.
        for i in range(0, len(parameters)):
            if parameters[i].hasBeenValidated == False:
                FT0_FloodMaster.idxChangeField = i
                break

        # If user has defined a new projection that is not part of the
        # predefined list, add it to list now in this method, before validations
        # take place in "updateMessages" so it won't be rejected.  Note that the
        # Python "append" method does not appear to work in this context, so
        # appending has been done as shown.
        #
        # If have changed workspace or projection, define:
        # - the list of 16-bit SAR files that will be made available to the
        #   "FT2_Scale16to8BitSet" tool
        # - the list of 8-bit SAR files that will be made available to the
        #   "FT3_ExtractFloodExtentAndConvertToVector" tool
        # - the list of water thresholds that will be made available to the
        #   "FT3_ExtractFloodExtentAndConvertToVector" tool
        #
        # If have changed selection of 16-bit SAR files to be processed, define
        # the latter 2 items of the above.
        #
        # If have changed selection of 8-bit SAR files to be processed, define
        # the last item of the above.
        #

        if FT0_FloodMaster.idxChangeField == 2:
            if parameters[2].value not in parameters[2].filter.list:
                parameters[2].filter.list += [parameters[2].value]

        if FT0_FloodMaster.idxChangeField in [0,2]:
            if parameters[0].value != None and parameters[2].value != None:
                self.loadOrthoMosaicFilesField(parameters)
                self.load8BitSarImageField(parameters)
                self.loadWaterThresholds(parameters)

        elif FT0_FloodMaster.idxChangeField == 4:
            self.load8BitSarImageField(parameters)
            self.loadWaterThresholds(parameters)

        elif FT0_FloodMaster.idxChangeField == 5:
            self.loadWaterThresholds(parameters)

        return


    def updateMessages(self, parameters):
        """
        Part of the Python toolbox template, called after internal validation,
        can be used to modify the messages created by internal validation for
        each tool parameter.

        In this implementation, it:
        - confirms that the workspace exists, is accessible, and that at least 1
          SAR ZIP file is present within the directory
        - confirms that the pixel spacing consists of a comma-delimited pair of
          numbers
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
        if FT0_FloodMaster.idxChangeField == 0:
            if parameters[0].value:
                # Verify that workspace exists, is accessible, and has at least
                # 1 ZIP file present.
                zipFiles = FT1_R2ReadOrthoMosaic.validateWorkspace(str(parameters[0].value))
                if zipFiles == None:
                    msgText = "ERROR:  Workspace does not contain ZIP " \
                              "files, or do not have access privileges."
                    parameters[0].setErrorMessage( msgText )
        # - Pixel Spacing
        elif FT0_FloodMaster.idxChangeField == 3:
            if parameters[3].value != None:
                msgText = FT1_R2ReadOrthoMosaic.validatePixelSpacing(str(parameters[3].value))
                if msgText:
                    parameters[3].setErrorMessage( msgText )

        # - Water Thresholds
        #   Changes to Workspace, SAR Image and Water Thresholds all effect
        #   this, but a click on a checkbox won't trigger the event until AFTER
        #   the control loses focus, which sucks.  See:
        #   http://support.esri.com/technical-article/000011771
        elif FT0_FloodMaster.idxChangeField == 7:
            msgText \
            = FT3_ExtractFloodExtentAndConvertToVector.validateWaterThresholds(
                    parameters[6], parameters[7])  # SAR Files, Water Thresholds
            if msgText:
                if msgText.split(' ', 1)[0] == "ERROR:":
                    parameters[7].setErrorMessage( msgText )
                else:

                    parameters[7].setWarningMessage( msgText )
        # - Minimum Polygon Size
        elif FT0_FloodMaster.idxChangeField == 8:
            msgText \
            = FT3_ExtractFloodExtentAndConvertToVector.validateMinimumPolygonSize(parameters[8].value)
            if msgText:
                parameters[8].setErrorMessage( msgText )
        # - Processing Mask
        elif FT0_FloodMaster.idxChangeField == 9:
            if parameters[9].value != None:
                msgText = FT3_ExtractFloodExtentAndConvertToVector.validateProcessingMask(str(parameters[9].value))
                if msgText:
                    parameters[9].setErrorMessage( msgText )

        return


    def execute(self, parameters, messages):
        """
        Part of the Python toolbox template, used to produce the expected output
        of the tool.

        Orchestrates all of the steps required to produce output, called from
        the GUI when the user presses the OK button or from function "main()" at
        the bottom of this module when command line interface has been defined
        and the script is run in batch from the command line.

        In this implementation, "execute" performs the following:
        - validates all incoming parameters
            - verifies that workspace directory exists, is accessible, and
              contains ZIP files
            - verifies that DEM file exists and is accessible
            - verifies that Projection has been passed
            - verifies that Pixel Spacing has been passed and consists of
              comma-delimited pair of numbers
            - verifies that at least one 16-bit polarized SAR Image file has
              been selected
            - verifies that at least one 8-bit scaled and filtered SAR Image
              file has been selected
            - verifies that all required polarizations and water thresholds
              are present and properly defined
            - if a processing mask is to be applied, verifies that file exists
              and is accessible
        - calls "FT1_R2ReadOrthoMosaic" tool to:
            - create "Raw" directory if it doesn't exist, move ZIP files to that
              directory and unpacks them
            - create "Orthos" directory if it doesn't exist, and uses DEM to
              generate orthorectified versions of raw RADARSAT images and
              reprojects
            - create "Mosaic" directory if it doesn't exist, and mosaics
              individual orthorectified images together
            - create separate mosaicked images for each polarization channel
              (eg. HH, HV) for passing to second tool in suite
        - calls "FT2_Scale16to8BitSet" tool to:
            - create "Scratch", "Scaled" and "Scaled_Unfiltered" folders if they
              do not already exist, and sets the arcpy working/scratch
              directories to point to "Scratch" for those tools that implictly
              require a working space for temporary files
            - process each selected 16-Bit SAR Image:
                - gathers MIN and MAX 16-bit pixel values
                - stretches image to only include non-NoData values and translates
                  each pixel to 8-bit equivalent values
                - creates non-filtered image for inclusion in map (brighter so
                  better for visual products)
                - applies 3x3 moving rectangle "median" filter to smooth out to
                  smooth out pixel values and reduce speckles in image that will
                  be passed to downstream 3rd tool in suite
            - deletes temporary files/directories
        - calls "FT3_ExtractFloodExtentAndConvertToVector" tool to:
            - create "Scratch" and "OWFEP" (Open Water Flood Extent Polygons)
              folders if they do not already exist, and sets the arcpy
              working/scratch directories to point to "Scratch" for those tools
              that implictly require a working space for temporary files
            - process each selected 8-Bit Scaled Filtered SAR Image:
                - determines MIN and MAX water threshold values and generates
                  range
                - processes each threshold value in range:
                    - defines target shapefile name for each threshold value
                    - applies CON tool to SAR image to identify flood pixels,
                      those that are <= threshold value
                    - applies 5x5 moving rectangle "majority" filter to smooth
                      out pixel values and thereby reduce number of polygons to
                      be created
                    - converts raster to vector polygon shapefile
                    - eliminates polygons that represent non-flooded regions
                    - calculates area in hectares for each flood polygon
                    - removes polygons that are smaller than specified value and
                      saves resultant to target shapefile -- this shapefile will
                      be manually inspected by user to determine if it should be
                      passed to subsequent tools in the Flood Tools suite
            - deletes temporary files/directories

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
        try:
            # Open up message log and progress bar
            # ------------------------------------
            arcpy.SetProgressor("default", "Flood Tools - Master")
            arcpy.AddMessage("Python Version: " + sys.version)
            arcpy.AddMessage("Current Product License: " + arcpy.ProductInfo())


            # Ensure mandatory parameters are present, validate where necessary
            # -----------------------------------------------------------------
            # NOTE:
            # While the ArcGIS GUI interface ensures mandatory parameters are
            # present before calling "execute", the command-line or call via the
            # "FT1_R2ReadOrthoMosaic" object does not.

            arcpy.SetProgressorLabel("Validate Mandatory Parameters...")
            arcpy.AddMessage("Validate Mandatory Parameters")

            # Assign parameters to local variables
            # [Note: str() cast of None yields "None"]
            if parameters[0].value == None:
                workspace         = None
            else:
                workspace         = str(parameters[0].value)
            if parameters[1].value == None:
                demFilename       = None
            else:
                demFilename       = str(parameters[1].value)
            orthoProjection       = parameters[2].value
            if parameters[3].value == None:
                orthoPixelSpacing = None
            else:
                orthoPixelSpacing = str(parameters[3].value)
            sarFileList16Bit      = parameters[4].values
            sarFileList8Bit       = parameters[6].values
            waterThresholds       = parameters[7].values
            minPolygonSize        = parameters[8].value
            if parameters[9].value == None:
                processingMask    = None
            else:
                processingMask    = str(parameters[9].value)

            # Validate Workspace Directory
            arcpy.SetProgressorLabel("Validate Workspace Directory...")
            arcpy.AddMessage("- Validate Workspace Directory")
            if workspace != None:
                zipFiles = FT1_R2ReadOrthoMosaic.validateWorkspace(workspace)
                if zipFiles == None:
                    msgText = "ERROR:  Workspace Directory does not exist, " \
                              "does not contain ZIP files, or do not have "  \
                              "access privileges."
                    arcpy.AddError( msgText )
                    return 1
            else:
                arcpy.AddError( "ERROR:  Workspace Directory is missing." )
                return 1

            # Validate DEM File
            arcpy.SetProgressorLabel("Validate DEM File...")
            arcpy.AddMessage("- Validate DEM File")
            if demFilename != None:
                if not os.path.isfile(demFilename) or not os.access(demFilename, os.R_OK):
                    msgText = "ERROR:  DEM File path does not exist or do not " \
                              "have read access:\n        %s" %                 \
                              (demFilename)
                    arcpy.AddError( msgText )
                    return 1
            else:
                arcpy.AddError( "ERROR:  DEM File is missing." )
                return 1

            # Validate Orthorectified Projection
            arcpy.SetProgressorLabel("Validate Ortho Projection...")
            arcpy.AddMessage("- Validate Ortho Projection")
            if orthoProjection == None:
                arcpy.AddError( "ERROR:  Ortho Projection is missing." )
                return 1

            # Validate Orthorectified Pixel Spacing
            arcpy.SetProgressorLabel("Validate Ortho Pixel Spacing...")
            arcpy.AddMessage("- Validate Ortho Pixel Spacing")
            if orthoPixelSpacing != None:
                msgText = FT1_R2ReadOrthoMosaic.validatePixelSpacing(orthoPixelSpacing)
                if msgText:
                    return 1
            else:
                arcpy.AddError( "ERROR:  Ortho Pixel Spacing is missing." )
                return 1

            # Validate List Of Selected 16-Bit Polarized SAR Images
            # NOTE:
            # Cannot use "FT2_Scale16to8BitSet.validate16BitSARFiles" to
            # validate since that method assumes that "FT1_R2ReadOrthoMosaic"
            # has already been run to generate the files -- at this point the
            # list just contains what's expected, not what's been created, so
            # can only ensure that at least one selection has been made.
            arcpy.SetProgressorLabel("Validate 16-Bit Polarized SAR Image Files...")
            arcpy.AddMessage("- Validate 16-Bit Polarized SAR Image Files")
            if parameters[4].value == None:
                arcpy.AddError( "ERROR:  16-SAR Polarized SAR Image is missing." )
                return 1

            # Validate List Of Selected 8-Bit Scaled Filtered SAR Images
            # NOTE:
            # Cannot use "FT3_ExtractFloodExtentAndConvertToVector.validate8BitSARFiles"
            # to validate since that method assumes that "FT2_Scale16to8BitSet"
            # has already been run to generate the files -- at this point the
            # list just contains what's expected, not what's been created, so
            # can only ensure that at least one selection has been made.
            arcpy.SetProgressorLabel("Validate 8-Bit Scaled Filtered SAR Image Files...")
            arcpy.AddMessage("- Validate 8-Bit Scaled Filtered SAR Image Files")
            if parameters[6].value == None:
                arcpy.AddError( "ERROR:  8-Bit Scaled Filtered Image is missing." )
                return 1

            # Validate Water Thresholds
            arcpy.SetProgressorLabel("Validate Water Thresholds...")
            arcpy.AddMessage("- Validate Water Thresholds")
            if parameters[7].value != None:
                msgText = FT3_ExtractFloodExtentAndConvertToVector.validateWaterThresholds(
                                parameters[6], parameters[7])  # SAR files, Water Thresholds
                if msgText:
                    # Ignore WARNINGS (will run with assigned corrections), only
                    # invalidate if ERROR
                    if msgText.split(' ', 1)[0] == "ERROR:":
                        return 1
            else:
                arcpy.AddError( "ERROR:  Water Thresholds are missing." )
                return 1

            # Validate Minimum Polygon Size
            arcpy.SetProgressorLabel("Validate Minimum Polygon Size...")
            arcpy.AddMessage("- Validate Minimum Polygon Size")
            if minPolygonSize != None:
                msgText = FT3_ExtractFloodExtentAndConvertToVector.validateMinimumPolygonSize(minPolygonSize)
                if msgText:
                    return 1
            else:
                arcpy.AddError( "ERROR:  Minimum Polygon Size is missing." )
                return 1

            # Validate Optional Processing Mask
            arcpy.SetProgressorLabel("Validate Processing Mask...")
            arcpy.AddMessage("- Validate Processing Mask\n")
            if processingMask:
                msgText = FT3_ExtractFloodExtentAndConvertToVector.validateProcessingMask(processingMask)
                if msgText:
                    return 1


            # Echo Final Parameters To Log
            # ----------------------------
            # Okay to proceed.  Feedback
            msgText  = "Parameter Values\n"                    \
                       "- Workspace Directory             :\n" \
                       "  %s\n"                                \
                       "  - ZIP Files                     :\n" % (workspace)
            for zippedFile in zipFiles:
                msgText += "    %s\n" % (zippedFile)
            msgText += "- DEM File Name                   :\n"    \
                       "  %s\n"                                   \
                       "- Ortho Projection                : %s\n" \
                       "- Ortho Pixel Spacing             : %s\n" \
                       "- 16-Bit Polarized SAR Images     :\n" %  \
                       (demFilename, orthoProjection, orthoPixelSpacing)
            for sarFile in sarFileList16Bit:
                msgText += "  %s\n" % (sarFile)
            msgText += "- 8-Bit Scaled Filtered SAR Images:\n"
            for sarFile in sarFileList8Bit:
                msgText += "  %s\n" % (sarFile)
            msgText += "- Water Thresholds                :\n"
            for waterThreshold in waterThresholds:
                msgText += "  %s  %2d  %2d\n" % \
                           (waterThreshold[0], waterThreshold[1], waterThreshold[2])
            msgText += "- Minimum Polygon Size            : %.2f\n" \
                       "- Processing Mask                 : %s\n" % \
                       (minPolygonSize, processingMask)
            arcpy.AddMessage(msgText)


            # Launch External Flood Tools
            # ---------------------------
            # NOTE:
            # Generally can pass 'value/values' attributes directly from
            # Parameter objects from this tool to the called tools since they
            # are the same type.  The exception is for directory/file paths
            # which need to be cast as strings or will trigger an error.  The
            # reason is that in this tool, the files don't always already exist
            # so are declared as String types here, whereas in the tools that
            # are called, the files are expected to have been created at the
            # time of the call so have been declared as other types like Raster.

            #-------------------------------------------------------------------
            #                       FT1_R2ReadOrthoMosaic
            #-------------------------------------------------------------------
            ft1Obj    = FT1_R2ReadOrthoMosaic()
            ft1Params = ft1Obj.getParameterInfo()

            ft1Params[0].value = str(parameters[0].value) # Workspace
            ft1Params[1].value = str(parameters[1].value) # DEM Filename
            ft1Params[2].value = parameters[2].value      # Ortho Projection
            ft1Params[3].value = parameters[3].value      # Ortho Pixel Spacing

            # Submit job and return exit status to OS (can be checked with echo
            # %ERRORLEVEL% in Windows).  All arcpy.AddMessage, arcpy.AddWarning
            # and arcpy.AddError messages issued in "execute" will be sent to
            # the Results window.
            arcpy.SetProgressorLabel("Launch 'FT1_R2ReadOrthoMosaic' Tool...")
            arcpy.AddMessage("Launch 'FT1_R2ReadOrthoMosaic' Tool")
            status = ft1Obj.execute(ft1Params, None)
            if status != 0:
                arcpy.AddError("'FT1_R2ReadOrthoMosaic' tool returned with "    \
                               "error status = %d.  Aborting 'FT0_FloodTools'." \
                               % (status))
                return status
            else:
                arcpy.AddMessage("'FT1_R2ReadOrthoMosaic' tool returned with " \
                                 "success status = %d." % (status))

            #-------------------------------------------------------------------
            #                       FT2_Scale16to8BitSet
            #-------------------------------------------------------------------
            ft2Obj    = FT2_Scale16to8BitSet()
            ft2Params = ft2Obj.getParameterInfo()

            ft2Params[0].value  = str(parameters[0].value) # Workspace
            ft2Params[1].values = parameters[4].values     # 16-Bit SAR Images
            ft2Params[2].value  = parameters[5].value      # Contrast Stretch

            # Submit job and return exit status to OS (can be checked with echo
            # %ERRORLEVEL% in Windows).  All arcpy.AddMessage, arcpy.AddWarning
            # and arcpy.AddError messages issued in "execute" will be sent to
            # the Results window.
            arcpy.SetProgressorLabel("Launch 'FT2_Scale16to8BitSet' Tool...")
            arcpy.AddMessage("\nLaunch 'FT2_Scale16to8BitSet' Tool")
            status = ft2Obj.execute(ft2Params, None)
            if status != 0:
                arcpy.AddError("'FT2_Scale16to8BitSet' tool returned with "     \
                               "error status = %d.  Aborting 'FT0_FloodTools'." \
                               % (status))
                return status
            else:
                arcpy.AddMessage("'FT2_Scale16to8BitSet' tool returned " \
                                 "with success status = %d." % (status))

            #-------------------------------------------------------------------
            #              FT3_ExtractFloodExtentAndConvertToVector
            #-------------------------------------------------------------------
            ft3Obj    = FT3_ExtractFloodExtentAndConvertToVector()
            ft3Params = ft3Obj.getParameterInfo()

            ft3Params[0].value  = str(parameters[0].value) # Workspace
            ft3Params[1].values = parameters[6].values     # 8-Bit SAR Images
            ft3Params[2].values = parameters[7].values     # Water Thresholds
            ft3Params[3].value  = parameters[8].value      # Minimum Polygon Size
            if parameters[9].value:                        # Processing Mask [Optional]
                ft3Params[4].value = str(parameters[9].value)

            # Submit job and return exit status to OS (can be checked with echo
            # %ERRORLEVEL% in Windows).  All arcpy.AddMessage, arcpy.AddWarning
            # and arcpy.AddError messages issued in "execute" will be sent to
            # the Results window.
            arcpy.SetProgressorLabel("Launch 'FT3_ExtractFloodExtentAndConvertToVector' Tool...")
            arcpy.AddMessage("\nLaunch 'FT3_ExtractFloodExtentAndConvertToVector' Tool")
            status = ft3Obj.execute(ft3Params, None)
            if status != 0:
                arcpy.AddError("'FT3_ExtractFloodExtentAndConvertToVector' " \
                               "tool returned with error status = %d.  "     \
                               "Aborting 'FT0_FloodTools'."                  \
                               % (status))
                return status
            else:
                arcpy.AddMessage("'FT3_ExtractFloodExtentAndConvertToVector' " \
                                 "tool returned with success status = %d." % (status))

            #-------------------------------------------------------------------
            #                      Successfully Completed
            #-------------------------------------------------------------------
            return 0

        except (Exception), ex:
            msgText = "ERROR:  Encountered exception in 'FT0_FloodTools.execute'.\n%s" % (ex)
            raise Exception( msgText )



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
        Generates a list of files expected to be created by the
        "FT2_Scale16to8BitSet" tool that will act as source files for the
        "FT3_ExtractFloodExtentAndConvertToVector" tool, and assigns them to
        the associated field.

        This method is dependent on both a valid Workspace and the files that
        have been selected in the 16-Bit Polarized SAR Image field.  It will be
        called each time the 16-Bit Polarized SAR Image field is changed, and
        will populate the 8-Bit Scaled Filtered SAR Image field with a list of
        files, one for each of selected 16-Bit Polarized SAR Image.  All 8-Bit
        Images will initally be selected for processing, to match those 16-Bit
        Images that have been chosen.

        Parameters:
            TYPE        NAME            DESCRIPTION
            Parameter[] parameters      List of Parameter objects created for
                                        this class.  Will use elements 0, 4, 5
                                        (Workspace, 16-Bit Polarized SAR Image,
                                        8-Bit Scaled Filtered SAR Image) of this
                                        list.

        Return Values:
            None.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        # Cycle through list of all selected 16-Bit Polarized SAR Images and
        # generate corresponding list of 8-Bit Scaled Filtered SAR Images,
        # to serve as input to "FT3_ExtractFloodExtentAndConvertToVector".
        # The general format of the file names to be created will be:
        #
        #    WORKSPACE\Scaled\YYYYMMDD_PROJECTIONCODE_mos_POLARIZATION_8bit_MED3x3.tif
        #
        # For example, for 16-Bit Polarized SAR Image files:
        #
        #    E:\FloodTest\ON_AlbanyRiverForks_UTM16\20160510_232540_W2\Mosaic\20160510_UTM16_mos_HH.tif
        #    E:\FloodTest\ON_AlbanyRiverForks_UTM16\20160510_232540_W2\Mosaic\20160510_UTM16_mos_HV.tif
        #
        # in workspace directory:
        #
        #    E:\FloodTest\ON_AlbanyRiverForks_UTM16\20160510_232540_W2
        #
        # two files would be generated with paths and names similar to the
        # following:
        #
        #    E:\FloodTest\ON_AlbanyRiverForks_UTM16\20160510_232540_W2\Scaled\20160510_UTM16_mos_HH_8bit_MED3x3.tif
        #    E:\FloodTest\ON_AlbanyRiverForks_UTM16\20160510_232540_W2\Scaled\20160510_UTM16_mos_HV_8bit_MED3x3.tif
        #
        # All files that are expected to be generated will be displayed,
        # and all will be selected by default to match the 16-Bit Image
        # selections.  If no 16-Bit Images have been selected, then the 8-Bit
        # Image list will be empty.
        #
        # The rules used to generate the file names are based on those found in
        # the "execute" method of tool "FT2_Scale16to8BitSet", so if those rules
        # change, the algorithm here will need to be adjusted accordingly.
        #
        if parameters[4].value != None:
            workspace       = str(parameters[0].value)
            sarFileTemplate = os.path.join(workspace, "Scaled", "%s_8bit_MED3x3.tif")
            sarFiles        = []
            for orthoMosaicFile in parameters[4].values:
                mosFileBaseName = os.path.splitext(os.path.basename(orthoMosaicFile))[0]
                sarFiles.append(sarFileTemplate % mosFileBaseName)

            # Load the 8-Bit Image list field, selecting all as default
            parameters[6].filter.list = sarFiles
            parameters[6].values      = sarFiles
        else:
            # No 16-Bit Images selected, so empty 8-Bit Image list
            parameters[6].filter.list = []
            parameters[6].value       = None

        return


    def loadOrthoMosaicFilesField(self, parameters):
        """
        Generates a list of files expected to be created by the
        "FT1_R2ReadOrthoMosaic" tool that will act as source files for the
        "FT2_Scale16to8BitSet" tool, and assigns them to the associated field.

        This method is dependent on both a valid Workspace and Orthorectified
        Projection being defined, and on which ZIP files are present in the
        Workspace.  It will be called each time the Workspace or Ortho
        Projection fields are changed, and will populate the 16-Bit Polarized
        SAR Image field with a list of files, selecting one as default with
        preference given to the "HH" polarixation, if present.

        Parameters:
            TYPE        NAME            DESCRIPTION
            Parameter[] parameters      List of Parameter objects created for
                                        this class.  Will use elements 0, 2, 4
                                        (Workspace, Ortho Projection, 16-Bit
                                        Polarized SAR Image) of this list.

        Return Values:
            None.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        # Get name of LAST Zip file.  The name of the directory in which its
        # scene files will be unpacked will be used to establish which file
        # names will be created by "FT1_R2ReadOrthoMosaic" and used as input to
        # "FT2_Scale16to8BitSet".  The general format of the file names to be
        # created will be:
        #
        #    WORKSPACE\Mosaic\YYYYMMDD_PROJECTIONCODE_mos_POLARIZATION.tif
        #
        # For example, for ZIP file:
        #
        #    RS2_OK75572_PK671521_DK599905_W2_20160510_232553_HH_HV_SGF.zip
        #
        # in workspace directory:
        #
        #    E:\FloodTest\ON_AlbanyRiverForks_UTM16\20160510_232540_W2
        #
        # two files would be generated with paths and names similar to the
        # following:
        #
        #    E:\FloodTest\ON_AlbanyRiverForks_UTM16\20160510_232540_W2\Mosaic\20160510_232540_UTM16_mos_HH.tif
        #    E:\FloodTest\ON_AlbanyRiverForks_UTM16\20160510_232540_W2\Mosaic\20160510_232540_UTM16_mos_HV.tif
        #
        # All files that are expected to be generated will be displayed, with
        # the "HH" polarization file selected by default, if "HH" exists, or the
        # first file otherwise.
        #
        # The rules used to generate the file names are based on those found in
        # the "execute" method of tool "FT1_R2ReadOrthoMosaic", so if those
        # rules change, the algorithm here will need to be adjusted accordingly.
        #
        workspace = str(parameters[0].value)
        zipFiles  = FT1_R2ReadOrthoMosaic.validateWorkspace(workspace)
        if zipFiles != None:
            lastZipFile     = zipFiles[-1]
            sceneDir        = os.path.splitext(os.path.basename(lastZipFile))[0]
            pathParts       = sceneDir.split('_')
            productDate     = pathParts[5]
            productTime     = pathParts[6]
            projParts       = str(parameters[2].value).split()
            projCode        = ''.join(projParts[:-1])
            mosFileTemplate = os.path.join(workspace, "Mosaic", "%s_%s_%s_mos_%s.tif" %
                                                                (productDate,productTime,projCode,"%s"))
            mosFiles        = []

            # Create 1 to 4 files, depending on how many polarizations are
            # present, and identify the file to serve as the default selection.
            if len(pathParts) == 9:     # single pole
                mosFiles.append(mosFileTemplate % pathParts[7])
                selectedFile = 0
            elif len(pathParts) == 10:  # dual pole
                mosFiles.append(mosFileTemplate % pathParts[7])
                mosFiles.append(mosFileTemplate % pathParts[8])
                if pathParts[8] == "HH":
                    selectedFile = 1
                else:
                    selectedFile = 0
            elif len(pathParts) == 12:  # quad pole
                mosFiles.append(mosFileTemplate % pathParts[7])
                mosFiles.append(mosFileTemplate % pathParts[8])
                mosFiles.append(mosFileTemplate % pathParts[9])
                mosFiles.append(mosFileTemplate % pathParts[10])
                if pathParts[8] == "HH":
                    selectedFile = 1
                elif pathParts[9] == "HH":
                    selectedFile = 2
                elif pathParts[10] == "HH":
                    selectedFile = 3
                else:
                    selectedFile = 0

            # Load the 16-Bit Image list field and set the default selection
            parameters[4].filter.list = mosFiles
            parameters[4].values      = [parameters[4].filter.list[selectedFile]]

        return


    def loadWaterThresholds(self, parameters):
        """
        Generates a list of Polarizations and corresponding Water Thresholds,
        one entry for each selected 8-Bit Scaled Filtered SAR Image, to serve as
        an input parameter to the "FT3_ExtractFloodExtentAndConvertToVector"
        tool.

        This method is dependent on the files that have been selected in the
        8-Bit Scaled Filtered SAR Image field, and will be called each time
        that field is changed.  If the Water Thresholds for a selected 8-Bit
        Image is not already present, a default entry consisting of Polarization
        and MIN and MAX Water Thresholds will be added to the list.

        Parameters:
            TYPE        NAME            DESCRIPTION
            Parameter[] parameters      List of Parameter objects created for
                                        this class.  Will use elements 5, 6
                                        (8-Bit Scaled Filtered SAR Image, Water
                                        Threshold) of this list.

        Return Values:
            None.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        # If one or more 8-Bit Scaled Filtered SAR Images have been selected,
        # use the "validateWaterThresholds" class method of the
        # "FT3_ExtractFloodExtentAndConvertToVector" tool to load the
        # corresponding Water Thresholds.  That method not only validates
        # existing entries, but adds new default entries for the selected images
        # when missing, and removes those that aren't required, and therefore
        # works well for this task.  If no images have been selected, the list
        # of Polarizations/Water Thresholds will be emptied.
        if parameters[6].values:
            # Adjust entries in Water Thresholds field
            FT3_ExtractFloodExtentAndConvertToVector.validateWaterThresholds(
                    parameters[6], parameters[7])  # SAR Files, Water Thresholds
        else:
            # No images selected: remove all Water Thesholds
            parameters[7].value = None

        return


    # ============= #
    # Class Methods #
    # ============= #


def main():
    """
        Allows FT0_FloodTools Tool to be executed from commmand line instead of
        GUI.

        Function "main()" allows the FT0_FloodTools module to be run as a script
        in batch, called from the command line or managing script rather than
        through a Toolbox in ArcCatalog or ArcMap, thereby bypassing the GUI
        interface provided by the Toolbox.  In this way, the application can be
        added to a processing chain, overseen by an orchestrating parent
        process, without requiring manual intervention between steps.  It uses
        argparse to exchange parameters with the command line.

        Usage:
            FT0_FloodMaster.py [-h] -dem DEMFILE [-mask PROCESSINGMASK]
                               [-mps MINPOLYGONSIZE] [-pix PIXELSPACE]
                               [-pol POLARIZATION] [-proj PROJECTION]
                               [-stretch CONTRASTSTRETCH] -ws WORKSPACE
                               [-wt WATERTHRESHOLD]

        Parameters:
            Parameters that take a file name will accept either relative or
            absolute paths.

            -h,                         Optional
            --help
                                        Show this help message and exit.

            -dem DEMFILE,               Mandatory
            --demfile DEMFILE
                                        Digital Elevation Model (DEM) File.
                                        Used during orthorectification to
                                        correct pixel distortion in SAR images
                                        caused by layover, foreshortening and
                                        so on.  Areal coverage must be larger
                                        than images to which it will be applied.
                                        Example:
                                        D:\Floods\BaseData\QC\DEM\QC_Richelieu_UTM18_DEM_30.img

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

            -pix PIXELSPACE,            Optional
            --pixelspace PIXELSPACE
                                        Pixel Spacing.  Comma-delimited pair of
                                        numbers that identify the resolution in
                                        metres of each pixel in the
                                        orthorectified image, in the X and Y
                                        directions, respectively.  Ideal when
                                        compatible with the DEM cell size.  Is
                                        required by the tool, but if not passed,
                                        will use a default value of "12.5,12.5".
                                        Example:
                                        "30,30"

            -pol POLARIZATION,          Optional
            --polarization POLARIZATION
                                        Polarization Channel.  Identifies which
                                        channel is to be processed.  Must be a
                                        channel that has been captured in the
                                        raw SAR image, and must be one of the
                                        following supported values:
                                        - 'HH'
                                        - 'HV'
                                        - 'VV'
                                        - 'VH'
                                        - 'ALL'
                                        Value "ALL" indicates that all
                                        polarizations are to be processed.  Will
                                        establish which 16-bit polarized SAR
                                        images, 8-bit scaled filtered SAR
                                        images, and default water thresholds are
                                        to be created and assigned, such as:
                                              Mosaic\20160510_UTM16_mos_HH.tif
                                              Scaled\20160510_UTM16_mos_HH_8bit_MED3x3.tif
                                              ['HH', 10, 12]
                                        If not passed, will use default value of
                                        "HH" if captured, or first polarization
                                        encountered otherwise.
                                        Example:
                                        HV

            -proj PROJECTION,           Optional
            --projection PROJECTION
                                        Projection.  Used to reproject the
                                        incoming SAR images to the desired
                                        projection.  Will typically be comprised
                                        of two elements, the first being the
                                        code used to identify the projection,
                                        and the second being PCI Geomatica's
                                        code for the datum (such as 'D000' for
                                        WGS84 and 'D122' for NAD83).  Must be
                                        compatible with the images, DEMs and
                                        masks to be used.  Precise spacing
                                        within the string is required for it to
                                        be accepted by the reprojection
                                        function.  Is required by the tool, but
                                        if not passed, will use a default value
                                        of "CanLCC      E008".
                                        Example:
                                        "UTM 14 D122"

            -stretch CONTRASTSTRETCH,   Optional
            --contraststretch CONTRASTSTRETCH
                                        Contrast Stretch.  Linear stretching
                                        algorithm used to convert incoming
                                        16-bit SAR images to 8-bit.  Must be one
                                        of the following supported values:
                                        - 'Min-Max Range'
                                        - 'Min-90% Max Range'
                                        - '95% Confidence Interval'
                                        - '99% Confidence Interval'
                                        First two options are ones that should
                                        be most commonly used.  If not passed,
                                        will use default value of
                                        "Min-Max Range".
                                        Example:
                                        "Min-90% Max Range"

            -ws WORKSPACE,              Mandatory
            --workspace WORKSPACE
                                        Workspace.  Root directory immediately
                                        below which SAR ZIP files will be found
                                        and processing will take place.  As this
                                        script calls other tools in the Flood
                                        Tools suite, they will create the
                                        subdirectories that they require if they
                                        are not already present, including
                                        'Mosaic', 'Ortho', 'OWFEP', 'Raw',
                                        'Scaled', 'Scaled_Unfiltered' and
                                        'Scratch'.  ZIP files will be moved and
                                        unpacked in the 'Raw' directory,
                                        RADARSAT images will be reprojected and
                                        orthrectified in the 'Ortho' directory,
                                        mosaicked in the 'Mosaic' directory,
                                        scaled from 16-bit to 8-bit and filtered
                                        in the 'Scaled' directory, placed
                                        unfiltered into the 'Scaled_Unfiltered'
                                        directory, then finally transformed from
                                        raster to vector polygon shapefiles,
                                        filtered and optionally clipped in the
                                        'OWFEP' directory.
                                        Example:
                                        D:\Floods\QC_Richelieu\20110507_225926_F6F

            -wt WATERTHRESHOLD,         Optional
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
            Pass Mandatory Parameters + Mask, Rely On Defaults For Others
            -------------------------------------------------------------
            C:\Python27\ArcGISx6410.3\python.exe FT0_FloodMaster.py ^
            -ws "D:\Floods\QC_Richelieu\20110507_225926_F6F" ^
            -dem "D:\Floods\BaseData\QC\DEM\QC_Richelieu_CanLCC_DEM_30.img" ^
            -mask "D:\Floods\BaseData\QC\ProcessingMask\QC_Richelieu_Mask_7p5km.shp"

            Pass All Parameters, Process All Channels With Extensive Water Thresholds
            -------------------------------------------------------------------------
            C:\Python27\ArcGISx6410.3\python.exe FT0_FloodMaster.py ^
            -ws "D:\Floods\QC_Richelieu\20110507_225926_F6F" ^
            -dem "D:\Floods\BaseData\QC\DEM\QC_Richelieu_UTM18_DEM_30.img" ^
            -proj "UTM 18 D122" -pix "12.5,12.5" -mps 2.5 -pol ALL ^
            -stretch "Min-90% Max Range"
            -wt "[['HH', 9, 13], ['HV', 3, 7]]" ^
            -mask "D:\Floods\BaseData\QC\ProcessingMask\QC_Richelieu_Mask_7p5km.shp"

        Limit(s) and Constraint(s) During Use:
            Must be submitted through 64-bit Python.
    """
    # SAMPLE CALLS FOR TESTING
    #
    # GET USAGE / HELP (MUST Use 64-bit Python)
    # C:\Python27\ArcGISx6410.3\python.exe FT0_FloodMaster.py -h
    #
    # ORTHORECTIFY AND MOSAIC RADARSAT IMAGE
    # C:\Python27\ArcGISx6410.3\python.exe FT0_FloodMaster.py ^
    # -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" ^
    # -dem "E:\FloodTest\BaseData\RiverIce\ON\DEM\ON_FarNorth_UTM16_DEM_25.img" ^
    # -proj "UTM 16 D122" -pix "12.5,12.5"
    #
##C:\Python27\ArcGISx6410.3\python.exe FT0_FloodMaster.py -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" -dem "E:\FloodTest\BaseData\RiverIce\ON\DEM\N_Ontario_DEM_UTM16_to__E008.tif"
##C:\Python27\ArcGISx6410.3\python.exe FT0_FloodMaster.py -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" -dem "E:\FloodTest\BaseData\RiverIce\ON\DEM\ON_FarNorth_UTM16_DEM_25.img" -proj "UTM 16 D122" -pix "12.5,12.5"
##C:\Python27\ArcGISx6410.3\python.exe FT0_FloodMaster.py -ws "E:\FloodTest\test_dataset\2011_05_22\QuadPolTest" -dem "E:\FloodTest\test_dataset\BaseData\DEM\DEM_for_testing_victor.img" -proj "UTM 18 D122" -pol ALL -stretch "Min-90% Max Range" -wt "[['HH', 6, 10], ['HV', 2, 4], ['VV', 2, 4], ['VH', 6, 10]]" -mask "E:\FloodTest\test_dataset\BaseData\Processing_Mask\Mask_Richelieu_River.shp"

    DEBUG = False   # Set to True to see incoming parameters before "execute"
##    DEBUG = True    # Set to True to see incoming parameters before "execute"
    try:
        if DEBUG:
            print 'Argument List:\n', str(sys.argv)

# CAN SET DEFAULTS FOR IMAGES, ETC. ????? USING "load" methods?


        # Get Command Line Arguments (if running in batch and not through GUI)
        parser = argparse.ArgumentParser(
                            formatter_class=argparse.RawTextHelpFormatter,
                            description=
                            "Consolidates individual flood tools under a "    +
                            "managing umbrella that oversees and\n"           +
                            "integrates their operations.  Tools launched:\n" +
                            "- FT1_R2ReadOrthoMosaic\n"                       +
                            "- FT2_Scale16to8BitSet\n"                        +
                            "- FT3_ExtractFloodExtentAndConvertToVector\n",
                            epilog=
                            "Examples:\n"                                                                           +
                            "- Pass Mandatory Parameters + Mask, Rely On Defaults For Others\n"                     +
                            "  C:\\Python27\\ArcGISx6410.3\\python.exe FT0_FloodMaster.py ^\n"                      +
                            "  -ws \"D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\" ^\n"                           +
                            "  -dem \"D:\\Floods\\BaseData\\QC\DEM\\QC_Richelieu_CanLCC_DEM_30.img\" ^\n"           +
                            "  -mask \"D:\\Floods\\BaseData\\QC\\ProcessingMask\\QC_Richelieu_Mask_7p5km.shp\"\n\n" +
                            "- Pass All Parameters, Process All Channels With Extensive Water Thresholds\n"         +
                            "  C:\\Python27\\ArcGISx6410.3\\python.exe FT0_FloodMaster.py ^\n"                      +
                            "  -ws \"D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\" ^\n"                           +
                            "  -dem \"D:\\Floods\\BaseData\\QC\DEM\\QC_Richelieu_UTM18_DEM_30.img\" ^\n"            +
                            "  -proj \"UTM 18 D122\" -pix \"12.5,12.5\" -mps 2.5 -pol ALL ^\n"                      +
                            "  -stretch \"" + FT2_Scale16to8BitSet.SUPPORTED_CONTRASTSTRETCH[1] + "\" ^\n"          +
                            "  -wt \"[['HH', 9, 13], ['HV', 3, 7]]\" ^\n"                                           +
                            "  -mask \"D:\\Floods\\BaseData\\QC\\ProcessingMask\\QC_Richelieu_Mask_7p5km.shp\"\n\n")
        parser.add_argument('-dem', '--demfile',
                            required=True, action='store', dest='demFile',
                            help="Digital Elevation Model (DEM) File.  Used during\n"      +
                                 "orthorectification to correct pixel distortion in SAR\n" +
                                 "images caused by layover, foreshortening and so on.\n"   +
                                 "Areal coverage must be larger than images to which it\n" +
                                 "will be applied.\n"                                      +
                                 "Example:\n"                                              +
                                 "D:\\Floods\\BaseData\\QC\DEM\\QC_Richelieu_UTM18_DEM_30.img\n")
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
        parser.add_argument('-pix', '--pixelspace',
                            required=False, action='store', dest='pixelSpace',
                            help="Pixel Spacing.  Comma-delimited pair of numbers that\n"    +
                                 "identify the resolution in metres of each pixel in the\n"  +
                                 "orthorectified image, in the X and Y directions,\n"        +
                                 "respectively.  Ideal when compatible with the DEM cell\n"  +
                                 "size.  Is required by the tool, but if not passed, will\n" +
                                 "use a default value of \"12.5,12.5\".\n"                   +
                                 "Example:\n"                                                +
                                 "\"30,30\"\n")
        parser.add_argument('-pol', '--polarization',
                            required=False, action='store', dest='polarization',
                            help="Polarization Channel.  Identifies which channel is to\n"    +
                                 "be processed.  Must be a channel that has been captured\n"  +
                                 "in the raw SAR image, and must be one of the following\n"   +
                                 "supported values:\n"                                        +
                                 str(FT3_ExtractFloodExtentAndConvertToVector.SUPPORTED_POLARIZATIONS).replace("[","- ").replace(", ","\n- ").replace("]","\n") +
                                 "- 'ALL'\n"                                                  +
                                 "Value \"ALL\" indicates that all polarizations are to be\n" +
                                 "processed.  Will establish which 16-bit polarized SAR\n"    +
                                 "images, 8-bit scaled filtered SAR images, and default\n"    +
                                 "water thresholds are to be created and assigned, such\n"    +
                                 "as:\n"                                                      +
                                 "      Mosaic\\20160510_UTM16_mos_HH.tif\n"                  +
                                 "      Scaled\\20160510_UTM16_mos_HH_8bit_MED3x3.tif\n"      +
                                 "      ['HH', 10, 12]\n"                                     +
                                 "If not passed, will use default value of \"HH\" if\n"       +
                                 "captured, or first polarization encountered otherwise.\n"   +
                                 "Example:\n"                                                 +
                                 "HV\n")
        parser.add_argument('-proj', '--projection',
                            required=False, action='store', dest='projection',
                            help="Projection.  Used to reproject the incoming SAR images\n"  +
                                 "to the desired projection.  Will typically be comprised\n" +
                                 "of two elements, the first being the code used to\n"       +
                                 "identify the projection, and the second being PCI\n"       +
                                 "Geomatica's code for the datum (such as 'D000' for\n"      +
                                 "WGS84 and 'D122' for NAD83).  Must be compatible with\n"   +
                                 "the images, DEMs and masks to be used.  Precise spacing\n" +
                                 "within the string is required for it to be accepted by\n"  +
                                 "the reprojection function.  Is required by the tool,\n"    +
                                 "but if not passed, will use a default value of\n"          +
                                 "\"CanLCC      E008\".\n"                                   +
                                 "Example:\n"                                                +
                                 "\"UTM 14 D122\"\n")
        # NOTE: The '%' signs in the stretch strings cause problems here and must be '%%' escaped.
        parser.add_argument('-stretch', '--contraststretch',
                            required=False, action='store', dest='contraststretch',
                            help="Contrast Stretch.  Linear stretching algorithm used to\n"  +
                                 "convert incoming 16-bit SAR images to 8-bit.  Must be\n"   +
                                 "one of the following supported values:\n"                  +
                                 str(FT2_Scale16to8BitSet.SUPPORTED_CONTRASTSTRETCH).replace("[","- ").replace(", ","\n- ").replace("]","\n").replace("%", "%%") +
                                 "First two options are ones that should be most commonly\n" +
                                 "used.  If not passed, will use default value of\n"         +
                                 "\"" + FT2_Scale16to8BitSet.SUPPORTED_CONTRASTSTRETCH[0].replace("%", "%%") + "\".\n" +
                                 "Example:\n"                                                +
                                 "\"" + FT2_Scale16to8BitSet.SUPPORTED_CONTRASTSTRETCH[1].replace("%", "%%") + "\"\n")
        parser.add_argument('-ws', '--workspace',
                            required=True, action='store', dest='workspace',
                            help="Workspace.  Root directory immediately below which SAR\n"  +
                                 "ZIP files will be found and processing will take place.\n" +
                                 "As this script calls other tools in the Flood Tools\n"     +
                                 "suite, they will create the subdirectories that they\n"    +
                                 "require if they are not already present, including\n"      +
                                 "'Mosaic', 'Ortho', 'OWFEP', 'Raw', 'Scaled',\n"            +
                                 "'Scaled_Unfiltered' and 'Scratch'.  ZIP files will be\n"   +
                                 "moved and unpacked in the 'Raw' directory, RADARSAT\n"     +
                                 "images will be reprojected and orthrectified in the\n"     +
                                 "'Ortho' directory, mosaicked in the 'Mosaic' directory,\n" +
                                 "scaled from 16-bit to 8-bit and filtered in the\n"         +
                                 "'Scaled' directory, placed unfiltered into the\n"          +
                                 "'Scaled_Unfiltered' directory, then finally transformed\n" +
                                 "from raster to vector polygon shapefiles, filtered and\n"  +
                                 "optionally clipped in the 'OWFEP' directory.\n"            +
                                 "Example:\n"                                                +
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

        # Create FT0_FloodTools object and initialize its parameters.  The
        # initialization will assign default values, where defined.  Make sure
        # relative paths are expressed as absolute paths or may get error.  Will
        # take advantage of any defaults assigned in the "getParameterInfo"
        # method.
        ft0Obj = FT0_FloodMaster()
        params = ft0Obj.getParameterInfo()

        params[0].value = os.path.abspath(cmdLineFlags.workspace) # Workspace
        params[1].value = os.path.abspath(cmdLineFlags.demFile)   # DEM Filename

        if cmdLineFlags.projection:                               # Ortho Projection
            params[2].value = cmdLineFlags.projection

        if cmdLineFlags.pixelSpace:                               # Ortho Pixel Spacing
            params[3].value = cmdLineFlags.pixelSpace

        # Load 16-Bit Polarized Images.
        #
        # Will begin by loading all images that 'could' be generated from the
        # ZIP file based on the captured polarization channels and from which a
        # default selection will be made.  Then if caller has requested a
        # specific polarization or ALL polarizations, will change the selection
        # accordingly.  If the requested polarization is not supported or has
        # not been captured in the raw SAR image, an exception will be triggered.
        #
        # NOTE:
        # A ZIP file MUST be located in the Workspace root directory for this to
        # work, since the polarizations contained within the ZIP file name are
        # used to determine which channels are available.
        ft0Obj.loadOrthoMosaicFilesField(params)                  # 16-Bit SAR Images
        if cmdLineFlags.polarization:                             # Polarization
            supportedPolarizations = FT3_ExtractFloodExtentAndConvertToVector.SUPPORTED_POLARIZATIONS
            supportedPolarizations.append("ALL")
            if cmdLineFlags.polarization not in supportedPolarizations:
                raise ValueError(
                    "ERROR:  Unsupported Polarization '%s' passed.  Must be " \
                    "one of: %s" % (cmdLineFlags.polarization, str(supportedPolarizations)))
            elif cmdLineFlags.polarization == "ALL":
                params[4].values = params[4].filter.list
            else:
                fileExists = False
                for imageFile in params[4].filter.list:
                    # File root names will be similar to "20160510_UTM16_mos_HH"
                    sarImage16Bit = os.path.splitext(os.path.basename(imageFile))[0]
                    if sarImage16Bit.endswith("_" + cmdLineFlags.polarization):
                        params[4].values = [imageFile]
                        fileExists = True
                        break
                if fileExists == False:
                    raise ValueError(
                        "ERROR:  Requested Polarization '%s' is not one that " \
                        "has been captured." % (cmdLineFlags.polarization))

        if cmdLineFlags.contraststretch:                          # Contrast Stretch
            params[5].value = float(cmdLineFlags.contraststretch)

        # Load each 8-Bit SAR Image that corresponds to a selected 16-Bit SAR
        # Image, then each Water Threshold that the 8-Bit images require.  Any
        # Water Threshold that has been passed in will override the default
        # threshold values retrieved this way.
        ft0Obj.load8BitSarImageField(params)                      # 8-Bit SAR Images

        if cmdLineFlags.waterthreshold:                           # Water Thresholds
            # Convert string argument to nested list objects, then use
            # validation method to ensure that any missing items are assigned
            # defaults.
            params[7].values = eval(cmdLineFlags.waterthreshold)
            FT3_ExtractFloodExtentAndConvertToVector.validateWaterThresholds(
                    params[6], params[7])  # 8-Bit SAR files, Water Thresholds
        else:
            ft0Obj.loadWaterThresholds(params)

        if cmdLineFlags.minpolygonsize:                           # Minimum Polygon Size
            params[8].value = float(cmdLineFlags.minpolygonsize)

        if cmdLineFlags.processingmask:                           # Processing Mask
            params[9].value = os.path.abspath(cmdLineFlags.processingmask)

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
        startTime   = time.time()
        status      = ft0Obj.execute(params, None)
        deltaTime   = time.time() - startTime
        elapsedTime = time.strftime('%H:%M:%S', time.gmtime(deltaTime))
        ## elapsedTime = str(datetime.timedelta(seconds=int(deltaTime)))
        print "\nElapsed Time: " + elapsedTime
        if status:
            exit(1) # Failure
        else:
            exit(0) # Success


    except Exception as ex:
        logText = "ERROR:  Encountered exception in 'main':\n" \
                  "        %s" % (ex)
        print logText
        exit(1)


if __name__ == '__main__':
    main()