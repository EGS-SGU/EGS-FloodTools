#! /usr/bin/env python
# -*- coding: Latin-1 -*-

__revision__ = "--REVISION-- : $Id: FT1_R2ReadOrthoMosaic.py 796 2017-03-06 16:33:43Z stolszcz $"

#==============================================================================#
# HISTORY                                                                      #
# -------                                                                      #
# Originally developed as ArCGIS Toolbox "1_R2_Read_Ortho_Mosaic.py" by        #
# A. Deschamps, converted  to Python Toolbox and altered by V. Neufeld,        #
# September 2016.                                                              #
#==============================================================================#


# Libraries
# =========
import arcpy
import argparse
import glob
import os
import shutil
import sys
import traceback
import zipfile


# ======= #
# Globals #
# ======= #


class FT1_R2ReadOrthoMosaic(object):
    """
    Performs first step in creating Flood Product.

    Is the first tool called in the procedure used to generate Flood Products.
    Starting in the workspace root directory where raw SAR imagery has been
    placed as ZIP file packages (either manually or automatically by the RS2Pull
    application), creates all subdirectories it requires if they are not already
    present (Raw, Ortho, Mosaic), moves the ZIP files to the Raw folder and
    unpacks them, then uses the DEM to orthorectify, reprojects, mosaics and
    finally separates the resultant into individual files that each represent
    one of the polarization channels (eg. HH, HV).  This work will serve as the
    starting point for the second tool to be applied (FT2_Scale16to8BitSet).

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
        PREDEFINED_PROJECTIONS
                        : List of predefined projections that are provided as a
                          convenience the tool.  Contains projections that one
                          may commonly encounter when applying the tool to
                          different areas of Canada, expressed in format that is
                          supported and compatible with PCI Geomatica whose
                          "ortho2" tool will be used to reproject the SAR image.

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
    PREDEFINED_PROJECTIONS = ["CanLCC      E008",
                              "UTM 9 D122",
                              "UTM 10 D122",
                              "UTM 11 D122",
                              "UTM 12 D122",
                              "UTM 13 D122",
                              "UTM 14 D122",
                              "UTM 15 D122",
                              "UTM 16 D122",
                              "UTM 17 D122",
                              "UTM 18 D122",
                              "UTM 19 D122",
                              "UTM 20 D122",
                              "UTM 21 D122",
                              "UTM 22 D122"]
    idxChangeField         = None


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
        self.label              = "FT1_R2ReadOrthoMosaic"
        self.description        = "First step in generating Flood Product.  " \
                                  "Unzips SAR images, orthorectifies, "       \
                                  "reprojects, mosaicks and separates into "  \
                                  "polarization channels."
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
        params = [None]*4

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
        params[3].value = "12.5,12.5"

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
                FT1_R2ReadOrthoMosaic.idxChangeField = i
                break

        # If user has defined a new projection that is not part of the
        # predefined list, add it to list now in this method, before validations
        # take place in "updateMessages" so it won't be rejected.  Note that the
        # Python "append" method does not appear to work in this context, so
        # appending has been done as shown.
        if FT1_R2ReadOrthoMosaic.idxChangeField == 2:
            if parameters[2].value not in parameters[2].filter.list:
                parameters[2].filter.list += [parameters[2].value]

        return


    def updateMessages(self, parameters):
        """
        Part of the Python toolbox template, called after internal validation,
        can be used to modify the messages created by internal validation for
        each tool parameter.

        In this implementation, it:
        - confirms that the workspace exists, is accessible, and contains ZIP
          files
        - confirms that the pixel spacing consists of a comma-delimited pair of
          numbers


        Parameters:
            TYPE        NAME            DESCRIPTION
            Array of Parameter
                        parameters      All Parameter objects defined in the
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
        # - Map Template
        if FT1_R2ReadOrthoMosaic.idxChangeField == 0:
            if parameters[0].value:
                # Verify that workspace exists, is accessible, and has at least
                # 1 ZIP file present.
                zipFiles = FT1_R2ReadOrthoMosaic.validateWorkspace(str(parameters[0].value))
                if zipFiles == None:
                    msgText = "ERROR:  Workspace does not contain ZIP " \
                              "files, or do not have access privileges."
                    parameters[0].setErrorMessage( msgText )
        # - Pixel Spacing
        elif FT1_R2ReadOrthoMosaic.idxChangeField == 3:
            if parameters[3].value != None:
                msgText = FT1_R2ReadOrthoMosaic.validatePixelSpacing(str(parameters[3].value))
                if msgText:
                    parameters[3].setErrorMessage( msgText )

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
        - imports 64-bit PCI Geomatica libraries; cannot be done at module level
          since ArcCatalog/ArcMap are 32-bit applications
        - validates all incoming parameters
            - verifies that workspace directory exists, is accessible, and
              contains ZIP files
            - verifies that DEM file exists and is accessible
            - verifies that Projection has been passed
            - verifies that Pixel Spacing has been passed and consists of
              comma-delimited pair of numbers
        - creates "Raw" directory if it doesn't exist, moves ZIP files to that
          directory and unpacks them
        - creates "Ortho" directory if it doesn't exist, and uses DEM to
          generate orthorectified versions of raw SAR images and reprojects
        - creates "Mosaic" directory if it doesn't exist, and mosaics individual
          orthorectified images together
        - separates mosaicked images into separate HH and HV polarization
          channel images


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
        # Import 64-bit Modules
        # ---------------------
        # Must be done with "execute" or will get error:
        #
        #       "TypeError: 'module' object is not callable"
        #
        # Also essential is to set the following class attribute to 'True' so
        # the 64-bit version of Arcpy gets called:
        #
        #        self.canRunInBackground = True
        # See:
        # https://blogs.esri.com/esri/supportcenter/2013/07/29/64-bit-vs-32-bit-python-explained/
        #
        # If you add an "argparse" command-line interface, will get warnings
        # like the following caused by placing an import statement within a
        # function rather than at the module level:
        #
        #    from pci.automos import *
        #    ...
        #    FT1_R2ReadOrthoMosaic.py:477: SyntaxWarning: import * only allowed at module level
        #      def execute(self, parameters, messages):
        #
        # These can be eliminated by being specific about which libraries are
        # being imported, as in:
        #
        #    from pci.automos import automos
        #
        from pci.automos import automos
        from pci.fexport import fexport
        from pci.fimport import fimport
        from pci.ortho2  import ortho2

        try:
            # Open up message log and progress bar
            # ------------------------------------
            arcpy.SetProgressor("default", "Flood Tools - R2 Read Ortho Mosaic")
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
            workspace         = str(parameters[0].value)
            demFilename       = str(parameters[1].value)
            orthoProjection   = parameters[2].value
            orthoPixelSpacing = str(parameters[3].value)

            # Validate Workspace Directory
            arcpy.SetProgressorLabel("Validate Workspace Directory...")
            arcpy.AddMessage("- Validate Workspace Directory")
            if parameters[0].value != None:
                zipFiles = FT1_R2ReadOrthoMosaic.validateWorkspace(str(parameters[0].value))
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
            if parameters[1].value != None:
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
            arcpy.AddMessage("- Validate Ortho Pixel Spacing\n")
            if parameters[3].value != None:
                msgText = FT1_R2ReadOrthoMosaic.validatePixelSpacing(orthoPixelSpacing)
                if msgText:
                    arcpy.AddError( msgText )
                    return 1
            else:
                arcpy.AddError( "ERROR:  Ortho Pixel Spacing is missing." )
                return 1


            # Echo Final Parameters To Log
            # ----------------------------
            # Okay to proceed.  Feedback
            zipFileList = ""
            for zippedFile in zipFiles:
                zipFileList += "    " + zippedFile + "\n"
            arcpy.AddMessage( "Parameter Values\n"             \
                              "- Workspace Directory : %s\n"   \
                              "  - ZIP Files         :\n"      \
                              "%s"                             \
                              "- Ortho Projection    : %s\n"   \
                              "- DEM File Name       : %s\n"   \
                              "- Ortho Pixel Spacing : %s\n" % \
                             (workspace,
                              zipFileList,
                              orthoProjection,
                              demFilename,
                              orthoPixelSpacing) )

            #-------------------------------------------------------------------
            #          Copy and Unzip RS2 Data Segments to RAW folder
            #-------------------------------------------------------------------
            # Create "Raw" subdirectory if it does not already exist, remove and
            # recreate it otherwise (if not done, cannot rerun this tool since
            # will trigger an error when trying to re-UNZIP the ZIP file).  Then
            # move ZIP files to that directory, and unpack.
            arcpy.SetProgressorLabel("Process ZIP Files...")
            arcpy.AddMessage("Process ZIP Files")
            rawDir = os.path.join(workspace, 'Raw')
            arcpy.AddMessage("- Target Folder: '%s'" % (rawDir))
            if os.path.exists(rawDir):
                shutil.rmtree(rawDir)
            os.mkdir(rawDir)

            for zippedFile in zipFiles:
                zipBaseName = os.path.basename(zippedFile)
                arcpy.AddMessage("  - Move File  : '%s'" % (zipBaseName))
                zipFileNew = os.path.join(rawDir, zipBaseName)
                shutil.move(zippedFile, zipFileNew)

            zipFilesRawDir = glob.glob(os.path.join(rawDir, '*.zip'))
            for zippedFile in zipFilesRawDir:
                unzipSubdir = os.path.splitext(os.path.basename(zippedFile))[0]
                if os.path.exists(os.path.join(rawDir, unzipSubdir)) == True:
                    arcpy.AddMessage("  - Unzip Subdirectory " + "'" + unzipSubdir + "'" + " already exists.")
                else:
                    with zipfile.ZipFile(zippedFile, "r") as z:
                        z.extractall(rawDir)
                        arcpy.AddMessage("  - File " + "'" + os.path.basename(zippedFile) + "'" + " has been unzipped.")

            arcpy.AddMessage("  - All files unzipped.")

            listDir     = os.listdir(rawDir)
            sceneDirs   = [ d for d in listDir if os.path.isdir(os.path.join(rawDir,d))]
            numSegments = len(sceneDirs)
            arcpy.AddMessage("  - Number Of Scenes To Process = %d\n" % (numSegments))

            if numSegments == 0:
                arcpy.AddMessage('No scenes to process.  Terminating...')
                return 0

            #-------------------------------------------------------------------
            #                 IMPORT and ORTHO Each RS2 Segment
            #-------------------------------------------------------------------
            arcpy.SetProgressorLabel("Orthorectify RS2 Segments...")
            arcpy.AddMessage("Orthorectify RS2 Segments")
            orthoDir = os.path.join(workspace, 'Ortho')
            arcpy.AddMessage("- Target Folder: '%s'" % (orthoDir))
            if not os.path.exists(orthoDir):
                os.mkdir(orthoDir)

            for i, sceneDir in enumerate(sceneDirs):
                file01      =  os.path.join(rawDir, sceneDir, 'product.xml')
                arcpy.AddMessage("  - Scene [%d]  :\n" \
                                 "    - Product  : '%s'" % (i, file01))
                dirParts     = sceneDir.rsplit('_')
                productSat   = dirParts[0]
                productBeam  = dirParts[4]
                productDate  = dirParts[5]
                productTime  = dirParts[6]
                fileBaseName = "%s_%s_%s_%s.pix" % (productSat, productBeam, productDate, productTime)
                file02       = os.path.join(rawDir, fileBaseName)
                arcpy.AddMessage("    - Pix File : '%s'" % (fileBaseName))

                dbiw         = []           # Use all image
                poption      = "NEAR"
                dblayout     = "BAND"
                fimport(file01, file02, dbiw, poption, dblayout)
                arcpy.AddMessage("- Completed FIMPORT process")

                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                orthoProduct = os.path.join(orthoDir, "o" + fileBaseName)
                arcpy.AddMessage("- Ortho Product: '%s'" % (orthoProduct))

                mfile        = file02       # Input image file name
                # identify polarization channel(s) and last math segment elements
                if len(dirParts) == 9:      # single pole
                    dbic     = [1]
                    mmseg    = [2]
                elif len(dirParts) == 10:   # dual pole
                    dbic     = [1,2]
                    mmseg    = [3]
                elif len(dirParts) == 12:   # quad pole
                    dbic     = [1,2,3,4]
                    mmseg    = [5]
                srcbgd       = "ALL,0"      # srcbgd       = "NONE" ? "ALL,0"
                                            # Assign all incoming pixels with 0
                                            # value to background/NoData to
                                            # remove any black borders.
                filo         = orthoProduct # Uses the default file name
                ftype        = "PIX"        # use the PCIDSK format
                foptions     = "BAND"
                outbgd       = [0]          # outbgd       = [0] ? [65535]
                                            # Specifies the background (NoData)
                                            # value to use for ortho pixels that
                                            # are not populated.
                ulx          = ''
                uly          = ''
                lrx          = ''
                lry          = ''
                edgeclip     = [0]          # clip image by 0 percent (>0 only valid when image is not on slant)
                tipostrn     = ""
                mapunits     = orthoProjection
                ORTHO_PXSZ   = orthoPixelSpacing.split(",")
                bxpxsz       = ORTHO_PXSZ[0]
                bypxsz       = ORTHO_PXSZ[1]
                filedem      = demFilename  # input DEM file
                dbec         = [1]          # use 1st DEM channel
                backelev     = []
                elevref      = "MSL"        # Elevation values referenced to mean sea level (Geoid)
                elevunit     = "METER"
                elfactor     = []           # Specifies the offset only
                proc         = ""
                sampling     = [4]          # Ortho correction is computed for every 4th pixel
                resample     = "BILIN"

                ortho2(mfile,   dbic,     mmseg,    dbiw,     srcbgd,   filo,
                       ftype,   foptions, outbgd,   ulx,      uly,      lrx,
                       lry,     edgeclip, tipostrn, mapunits, bxpxsz,   bypxsz,
                       filedem, dbec,     backelev, elevref,  elevunit, elfactor,
                       proc,    sampling, resample)

                arcpy.AddMessage('- Completed ORTHO2 process\n')

            #-------------------------------------------------------------------
            #          MOSAIC Orthorectified Segments If More Than One
            #-------------------------------------------------------------------
            # Use directory of last scene processed above as target directory
            # for mosaicked product.  Example scene directories derived from
            # unpacking a SAR ZIP file might be:
            #
            #    RS2_OK20576_PK214403_DK199768_F6F_20110507_225921_HH_HV_SGF
            #    0   1       2        3        4   5        6      7  8  9
            #
            #    RS2_OK79874_PK704700_DK632860_FQ26_20110605_123300_HH_VV_HV_VH_SGX
            #    0   1       2        3        4    5        6      7  8  9  10 11
            #
            # Examples of orthorectified projection specification might be:
            #
            #    UTM 14 D122
            #    0   1  2
            #
            #    CanLCC      E008
            #    0           1
            arcpy.SetProgressorLabel("MOSAIC Orthorectified Segments...")
            arcpy.AddMessage("MOSAIC Orthorectified Segments")
           	# add dummy '_' to offset polarizations to index values 1,2
            if len(dirParts) == 9:     # single pole
                productPol = ['_', dirParts[7]]
            elif len(dirParts) == 10:  # dual pole
                productPol = ['_', dirParts[7], dirParts[8]]
            elif len(dirParts) == 12:  # quad pole
                productPol = ['_', dirParts[7], dirParts[8], dirParts[9], dirParts[10]]
            # pack spaces within string, then assign leftmost-1 to projCode
            projParts      = orthoProjection.split()
            projCode       = ''.join(projParts[:-1])
            mosaicDir      = os.path.join(workspace, 'Mosaic')
            mosaicFile     = "%s_%s_%s_mos.pix" % (productDate, productTime, projCode)
            mosaicProduct  = os.path.join(mosaicDir, mosaicFile)
            if not os.path.exists(mosaicDir):
                os.mkdir(mosaicDir)
            arcpy.AddMessage("- Mosaic Folder: '%s'" % (mosaicDir))
            arcpy.AddMessage("- Mosaic File  : '%s'" % (mosaicProduct))

            # NO mosaic, copy single segment ortho to mosaic directory
            if numSegments == 1:
                FILI     = orthoProduct
                FILO     = mosaicProduct
                DBIW     = []
                if len(productPol) == 2:    # single pole
                    DBIC = [1]
                elif len(productPol) == 3:  # dual pole
                    DBIC = [1,2]
                elif len(productPol) == 5:  # quad pole
                    DBIC = [1,2,3,4]
                DBIB     = []
                DBVS     = []
                DBLUT    = []
                DBPCT    = []
                FTYPE    = "PIX"
                FOPTIONS = ""
                fexport(FILI, FILO, DBIW, DBIC, DBIB, DBVS, DBLUT, DBPCT, FTYPE, FOPTIONS)
                arcpy.AddMessage("- EXPORTed single ortho segment to mosaic directory\n")

            # Mosaic muliple segments in ortho directory and assemble in mosaic directory
            elif numSegments >= 1:
                MFILE    = orthoDir
                if len(productPol) == 2:    # single pole
                    DBICLIST = "1"
                elif len(productPol) == 3:  # dual pole
                    DBICLIST = "1,2"
                elif len(productPol) == 5:  # quad pole
                    DBICLIST = "1,2,3,4"
                MOSTYPE  = "FULL"
                FILO     = mosaicProduct
                FTYPE    = "PIX"
                FOPTIONS = "BAND"
                CLRMOS   = "YES"
                STARTIMG = ""
                RADIOCOR = "NONE"
                BALMTHD  = "NONE"
                BALOPT   = [0]
                FILI_REF = ""
                LOCLMASK = "NONE"
                GLOBFILE = ""
                GLOBMASK = []
                CUTMTHD  = "ENTIRE"
            #    CUTMTHD="MINDIFF"  EASI setting
                FILVIN   = ""
                DBIV     = [0]
                FILVOUT  = ""
                DBOV     = [0]
                DBLUTO   = ""
            #    BLEND    =[2]    # EASI setting
                BLEND    = [0]
                BACKVAL  = [0.0]
                TEMPDIR  = ""
                automos(MFILE,    DBICLIST, MOSTYPE,  FILO,    FTYPE,   FOPTIONS,
                        CLRMOS,   STARTIMG, RADIOCOR, BALMTHD, BALOPT,  FILI_REF,
                        LOCLMASK, GLOBFILE, GLOBMASK, CUTMTHD, FILVIN,  DBIV,
                        FILVOUT,  DBOV,     DBLUTO,   BLEND,   BACKVAL, TEMPDIR)

                arcpy.AddMessage('- AUTOMOSed multiple ortho segments to mosaic directory\n')

            #-------------------------------------------------------------------
            #       EXPORT Each Mosaic Polarization To Separate TIF File
            #-------------------------------------------------------------------
            arcpy.SetProgressorLabel("EXPORT Each Mosaic Polarization To Separate TIF File...")
            arcpy.AddMessage("EXPORT Each Mosaic Polarization To Separate TIF File")
            for channel in range(1,len(productPol)):
                mosaicProductTIF = os.path.join(mosaicDir, "%s_%s_%s_mos_%s.tif" % (productDate, productTime, projCode, productPol[channel]))
                arcpy.AddMessage("- Writing channel [%d] to '%s'" % (channel, mosaicProductTIF))
                ftype    = '"' + 'TIF'
                foption  = '"' + 'WORLD'
                FILI     = mosaicProduct
                FILO     = mosaicProductTIF
                DBIW     = []
                DBIC     = [channel]
                DBIB     = []
                DBVS     = []
                DBLUT    = []
                DBPCT    = []
                FTYPE    = "TIF"
                FOPTIONS = "WORLD"
                fexport(FILI, FILO, DBIW, DBIC, DBIB, DBVS, DBLUT, DBPCT, FTYPE, FOPTIONS)

            #-------------------------------------------------------------------
            #                               DONE
            #-------------------------------------------------------------------
            return 0

        except (Exception), ex:
            line, filename, err = self.trace()
            msgText  = "ERROR:  Encountered exception in 'FT1_R2ReadOrthoMosaic.execute'.\n%s\n" % (ex)
            msgText += "        At line %s of file '%s'." % (str(line), filename)
            arcpy.AddError(msgText)
            # Assign a "Failure" status for return in "finally" block.
            return 1




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
        filename = os.path.join(sys.path[0], "FT1_R2ReadOrthoMosaic.py")
        synerror = traceback.format_exc().splitlines()[-1]
        return line, filename, synerror


    # ============= #
    # Class Methods #
    # ============= #
    # NOTE: These have been created as Class rather than Instance methods to
    #       accomodate integration of this modules into the FT0_FloodTools
    #       wrapper.
    @staticmethod
    def validatePixelSpacing(pixelSpacing):
        """
        Verifies that pixel spacing is properly specified, returning an error
        message if not.

        Parameters:
            TYPE        NAME            DESCRIPTION
            String      pixelSpacing    Comma-delimited pair of numbers, the
                                        first identifying the pixel size in
                                        metres in the X direction, and the
                                        second the pixel size in the Y
                                        direction.  For example, "12.5,12.5".

        Return Values:
            String
            -  None  Pixel spacing is valid.
            - !None  Pixel spacing is invalid.  Is not a comma-delimited pair of
                     numbers.  Value returned will be an error message that can
                     be displayed to the user or recorded in the Results window
                     or log file.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        pixelSize = pixelSpacing.split(",")
        isError   = False
        if len(pixelSize) != 2:
            isError = True
        else:
            try:
                float(pixelSize[0])
                float(pixelSize[1])
            except ValueError:
                isError = True
        if isError:
            return "ERROR:  Invalid pixel spacing '%s'.  Must be a pair of " \
                   "comma-delimited numbers." % (pixelSpacing)
        else:
            return None


    @staticmethod
    def validateWorkspace(workspace):
        """
        Confirms that Workspace directory exists, the user has access
        privileges, and that at least 1 SAR ZIP file is present within the
        directory.  Also returns a list of those ZIP files that the caller can
        then use for flood processsing.

        Parameters:
            TYPE        NAME            DESCRIPTION
            String      workspace       The path and name of the workspace
                                        directory below which all flood work
                                        is to take place.

        Return Values:
            String[]
            - !None  List of SAR ZIP files that caller will use for
                     downstream processing.
            -  None  Workspace is invalid: it does not exist, user does not have
                     read access to it, or no ZIP files are present.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        if not os.path.isdir(workspace) or not os.access(workspace, os.R_OK):
            return None
        else:
            zipFiles = glob.glob(os.path.join(workspace, '*.zip'))
            if zipFiles:
                if len(zipFiles) == 0:
                    return None
                else:
                    return zipFiles
            else:
                return None


def main():
    """
        Allows FT1_R2ReadOrthoMosaic Tool to be executed from commmand line
        instead of GUI.

        Function "main()" allows the FT1_R2ReadOrthoMosaic module to be run as a
        script in batch, called from the command line or managing script rather
        than through a Toolbox in ArcCatalog or ArcMap, thereby bypassing the
        GUI interface provided by the Toolbox.  In this way, the application can
        be added to a processing chain, overseen by an orchestrating parent
        process, without requiring manual intervention between steps.  It uses
        argparse to exchange parameters with the command line.

        Usage:
            FT1_R2ReadOrthoMosaic.py [-h] -dem DEMFILE [-pix PIXELSPACE]
                                     [-proj PROJECTION] -ws WORKSPACE


        Parameters:
            Parameters that take a file name will accept either relative or
            absolute paths.

            -h,                         Optional
            --help
                                        Show this help message and exit.

            -dem DEMFILE,               Mandatory
            --demfile DEMFILE
                                        Digital Elevation Model (DEM) File.
                                        Path and name of file used during
                                        orthorectification to correct pixel
                                        distortion in SAR images caused by
                                        layover, foreshortening and so on.
                                        Areal coverage must be larger than
                                        images to which it will be applied.
                                        Example:
                                        D:\Floods\BaseData\QC\DEM\QC_Richelieu_UTM18_DEM_30.img

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

            -proj PROJECTION,           Mandatory
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

            -ws WORKSPACE,              Mandatory
            --workspace WORKSPACE
                                        Workspace.  Root directory immediately
                                        below which SAR ZIP files will be
                                        found and processing will take place.
                                        Script will create subdirectories
                                        'Mosaic', 'Ortho' and 'Raw' if they are
                                        not already present, move and unpack the
                                        ZIP files in the 'Raw' directory,
                                        reproject and orthrectify the SAR
                                        images in the 'Ortho' directory, and
                                        mosaic the reprojected images in the
                                        'Mosaic' directory.
                                        Example:
                                        D:\Floods\QC_Richelieu\20110507_225926_F6F

        Return Values:
            Check on Windows OS with "echo %ERRORLEVEL%" after run.
            0       Successfully completed
            1       Error encountered during run.  Check messages issued to
                    standard output for details.
            2       Returned by "argparse" when mandatory parameter has not been
                    passed.


        Examples:
            Pass All Parameters
            -------------------
            C:\Python27\ArcGISx6410.3\python.exe FT1_R2ReadOrthoMosaic.py ^
            -ws "D:\Floods\QC_Richelieu\20110507_225926_F6F" ^
            -dem "D:\Floods\BaseData\QC\DEM\QC_Richelieu_UTM18_DEM_30.img" ^
            -proj "UTM 18 D122" -pix "12.5,12.5"

            Same As Above But Employs Default Projection And Pixel Spacing
            --------------------------------------------------------------
            C:\Python27\ArcGISx6410.3\python.exe FT1_R2ReadOrthoMosaic.py ^
            -ws "D:\Floods\QC_Richelieu\20110507_225926_F6F" ^
            -dem "D:\Floods\BaseData\QC\DEM\QC_Richelieu_CanLCC_DEM_30.img"


        Limit(s) and Constraint(s) During Use:
            Must be submitted through 64-bit Python.
    """
    # SAMPLE CALLS FOR TESTING
    #
    # GET USAGE / HELP (MUST Use 64-bit Python)
    # C:\Python27\ArcGISx6410.3\python.exe FT1_R2ReadOrthoMosaic.py -h
    #
    # ORTHORECTIFY AND MOSAIC SAR IMAGE
    # C:\Python27\ArcGISx6410.3\python.exe FT1_R2ReadOrthoMosaic.py ^
    # -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" ^
    # -dem "E:\FloodTest\BaseData\RiverIce\ON\DEM\ON_FarNorth_UTM16_DEM_25.img" ^
    # -proj "UTM 16 D122" -pix "12.5,12.5"
    #
##C:\Python27\ArcGISx6410.3\python.exe FT1_R2ReadOrthoMosaic.py -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" -dem "E:\FloodTest\BaseData\RiverIce\ON\DEM\ON_FarNorth_UTM16_DEM_25.img" -proj "UTM 16 D122" -pix "12.5,12.5"

    DEBUG = False   # Set to True to see incoming parameters before "execute"
##    DEBUG = True    # Set to True to see incoming parameters before "execute"
    try:
        if DEBUG:
            print 'Argument List:\n', str(sys.argv)

        # Get Command Line Arguments (if running in batch and not through GUI)
        parser = argparse.ArgumentParser(
                            formatter_class=argparse.RawTextHelpFormatter,
                            description=
                            "Orthorectifies and mosaics SAR images as first " +
                            "step in producing Flood Product.\n",
                            epilog=
                            "Examples:\n"                                                                +
                            "- Pass All Parameters\n"                                                    +
                            "  C:\\Python27\\ArcGISx6410.3\\python.exe FT1_R2ReadOrthoMosaic.py ^\n"     +
                            "  -ws \"D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\" ^\n"          +
                            "  -dem \"D:\\Floods\\BaseData\\QC\DEM\\QC_Richelieu_UTM18_DEM_30.img\" ^\n" +
                            "  -proj \"UTM 18 D122\" -pix \"12.5,12.5\"\n\n"                             +
                            "- Same As Above But Employs Default Projection And Pixel Spacing\n"         +
                            "  C:\\Python27\\ArcGISx6410.3\\python.exe FT1_R2ReadOrthoMosaic.py ^\n"     +
                            "  -ws \"D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\" ^\n"          +
                            "  -dem \"D:\\Floods\\BaseData\\QC\DEM\\QC_Richelieu_CanLCC_DEM_30.img\"\n\n")
        parser.add_argument('-dem', '--demfile',
                            required=True, action='store', dest='demFile',
                            help="Digital Elevation Model (DEM) File.  Used during\n"      +
                                 "orthorectification to correct pixel distortion in SAR\n" +
                                 "images caused by layover, foreshortening and so on.\n"   +
                                 "Areal coverage must be larger than images to which it\n" +
                                 "will be applied.\n"                                      +
                                 "Example:\n"                                              +
                                 "D:\\Floods\\BaseData\\QC\DEM\\QC_Richelieu_UTM18_DEM_30.img\n")
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
        parser.add_argument('-ws', '--workspace',
                            required=True, action='store', dest='workspace',
                            help="Workspace.  Root directory immediately below which SAR\n"  +
                                 "ZIP files will be found and processing will take place.\n" +
                                 "Script will create subdirectories 'Mosaic', 'Ortho'\n"     +
                                 "and 'Raw' if they are not already present, move and\n"     +
                                 "unpack the ZIP files in the 'Raw' directory, reproject\n"  +
                                 "and orthrectify the SAR images in the 'Ortho'\n"           +
                                 "directory, and mosaic the reprojected images in the\n"     +
                                 "'Mosaic' directory.\n"                                     +
                                 "Example:\n"                                                +
                                 "D:\\Floods\\QC_Richelieu\\20110507_225926_F6F\n")
        cmdLineFlags = parser.parse_args()

        # Create FT1_R2ReadOrthoMosaic object and initialize its parameters.
        # Make sure relative paths are expressed as absolute paths or may get
        # error.
        ft1Obj = FT1_R2ReadOrthoMosaic()
        params = ft1Obj.getParameterInfo()

        params[0].value = os.path.abspath(cmdLineFlags.workspace)
        params[1].value = os.path.abspath(cmdLineFlags.demFile)
        params[2].value = cmdLineFlags.projection

        if cmdLineFlags.pixelSpace:
            params[3].value = cmdLineFlags.pixelSpace
        else:
            params[3].value = "12.5,12.5"

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
        status = ft1Obj.execute(params, None)
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