#! /usr/bin/env python
# -*- coding: Latin-1 -*-

__revision__ = "--REVISION-- : $Id:  $"


# Libraries
# =========
import arcpy
import argparse
import subprocess
import sys
import os
import datetime
import shutil
import glob
import traceback
import zipfile

# ======= #
# Globals #
# ======= #

class FT4_FloodVegExtraction(object):
    """
    Performs fourth step in creating Flood Product.

    Is the fourth tool called in the procedure used to generate Flood Products.
    Starting in the workspace root directory, creates all subdirectories it
    requires if they are not already present (scratch, outdir, logs),
    then processes one or more polarized image files (HH, HV), present in the
    required ./raw directory. A DEM and a shapefile representing
    treed vegetation mask are to be provided with full path. Some required files
    are required to be place in a directory called ./seeds, these files includes
    should be three shapefiles representing training areas for non flooded
    vegetation(veg_non_flood.shp), flooded vegetation (veg_flood.shp) and
    open water (water.shp) can be used to overwrite the default tresholds values
    suggested by the GUI.


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
        """Define the tool (tool name is the name of the class)."""

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

        self.label = "FT4_FloodVegExtraction"
        self.description =  "Extracts flooded vegetation areas from a SAR image. " \
                            "Read, orthorecify and rescale to sigma nought the SAR file. " \
                            "Takes as input : one or several RADARSAT-2 scenes with associated product.xml files. " \
                            "A vegetation mask and a DEM. " \
                            "The tool will output a flooded vegetation product." \

        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""

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
            Array of Parameter  All Parameter objects defined and required for
                                the tool, and their values.


        Limit(s) and Constraint(s) During Use:
            None

            For more details refer to following links:
            Python Toolbox
            http://resources.arcgis.com/EN/HELP/MAIN/10.2/index.html#/The_Python_toolbox_template/001500000023000000/
            getParameterInfo Method
            http://resources.arcgis.com/en/help/main/10.2/index.html#//001500000028000000
        """

        params = [None]*8

        params[0] = arcpy.Parameter(
             displayName   = "Workspace",
             name          = "workspace",
             datatype      = "DEFolder",
             parameterType = "Required",
             direction     = "Input"
             )
        #params[0].value = None
        params[0].value = ""

        params[1] = arcpy.Parameter(
             displayName   = "Input Landcover Filename",
             name          = "land_cover",
             datatype      = ["DEFile"],
             parameterType = "Required",
             direction     = "Input"
             )
        params[1].value = ""

        params[2] = arcpy.Parameter(
             displayName   = "Input DEM Filename",
             name          = "DEM_file",
             datatype      = ["DEFile"],
             parameterType = "Required",
             direction     = "Input"
             )
        params[2].value = ""

        params[3] = arcpy.Parameter(
                        displayName   = "Ortho Projection",
                        name          = "orthoProjection",
                        datatype      = "GPString",
                        parameterType = "Required",
                        direction     = "Input"
                     )
        params[3].filter.type = "ValueList"
        params[3].filter.list = FT4_FloodVegExtraction.PREDEFINED_PROJECTIONS
        params[3].value       = "CanLCC      E008"
        # UTM Zone# + D122 which is PCI Geomatica code for NAD 83 (eg. "UTM 14 D122")
        # http://www.pcigeomatics.com/geomatica-help/references/proj_r/proj3n149.html


        params[4] = arcpy.Parameter(
                displayName   = "Output Ortho Pixel Spacing",
                name          = "orthoPixelSpacing",
                datatype      = "GPString",
                parameterType = "Required",
                direction     = "Input"
             )
        params[4].value   = "12.5,12.5"

        params[5] = arcpy.Parameter(
                displayName   = "Vegetation Threshold",
                name          = "v_th",
                datatype      = "GPString",
                parameterType = "Optional",
                direction     = "Input"
             )
        params[5].value   = "-3.5"

        params[6] = arcpy.Parameter(
                displayName   = "Open Water Threshold",
                name          = "ow_th",
                datatype      = "GPString",
                parameterType = "Optional",
                direction     = "Input"
             )
        params[6].value   = "-12.5"

        params[7] = arcpy.Parameter(
                displayName   = "Seeds directory (Optional)",
                name          = "SeedsDir",
                datatype      = "DEFolder",
                parameterType = "Optional",
                direction     = "Input"
             )
        params[7].value   = ""


        return params


    def isLicensed(self):
        """Set whether tool is licensed to execute."""
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
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

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
            Array of Parameter
                        parameters      All Parameter objects defined in the
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
                FT4_FloodVegExtraction.idxChangeField = i
                break

        if  FT4_FloodVegExtraction.idxChangeField == 3:
            if parameters[3].value not in parameters[3].filter.list:
                parameters[3].filter.list += [parameters[3].value]

        return


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
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
        if FT4_FloodVegExtraction.idxChangeField == 0:
            if parameters[0].value:
                # Verify that workspace exists, is accessible, and has at least
                # 1 XML file present.
                xmlFiles = self.validateWorkspace(str(parameters[0].value))
                if xmlFiles == None:
                    msgText = "ERROR:  Workspace does not contain valid radarsat " \
                              "product files, make sure the data is unzipped"
                    parameters[0].setErrorMessage( msgText )

##        # Making sure the landcover mask is correct
##        elif FT4_FloodVegExtraction.idxChangeField == 1:
##            if parameters[1].value:
##                LCFile = self.validateLandCover(str(parameters[1].value))
##                if LCFile == None:
##                    msgText = "ERROR: Invalid vegetated Landcover Mask file, " \
##                              "or doesn't have access privileges."
##                    parameters[1].setErrorMessage(msgText)

##        # Making sure the DEM is correct
##        elif FT4_FloodVegExtraction.idxChangeField == 2:
##            if parameters[2].value:
##                self.validateDEM(str(parameters[2].value))
##                msgText = "ERROR: Invalid DEM file, " \
##                          "or doesn't have access privileges."
##                parameters[2].setErrorMessage(msgText)
##
##        # Making sure the projection entered fits PCI format
##        elif FT4_FloodVegExtraction.idxChangeField == 3:
##            if parameters[3].value:
##                self.validateProjCode(str(parameters[3].value))
##                msgText = "ERROR: Invalid projection code" \
##                parameters[3].setErrorMessage(msgText)

        # - Pixel Spacing
        elif FT4_FloodVegExtraction.idxChangeField == 4:
            if parameters[4].value != None:
                msgText = FT4_FloodVegExtraction.validatePixelSpacing(str(parameters[4].value))
                if msgText:
                    parameters[4].setErrorMessage( msgText )

##        # Making sure the treshold value is a float delimited by a period
##        elif FT4_FloodVegExtraction.idxChangeField == 5:
##            if parameters[5].value:
##                self.validateDbValue(str(parameters[5].value))
##                msgText = "ERROR: Invalid treshold value, " \
##                          "use '.' as the delimiter, it must expressed in Db."
##                          "Ex : -3.5"
##                parameters[5].setErrorMessage(msgText)
##
##        # Making sure the treshold value is a float delimited by a period
##        elif FT4_FloodVegExtraction.idxChangeField == 6:
##            if parameters[6].value:
##                self.validateDbValue(str(parameters[6].value))
##                msgText = "ERROR: Invalid treshold value, " \
##                          "use '.' as the delimiter, it must expressed in Db."
##                          "Ex : -10.5"
##                parameters[6].setErrorMessage(msgText)

        return

    def execute(self,parameters, messages):
        """The source code of the tool."""

##        '''
##        Processing includes :
##        - Importing to PCI (.pix) imagery format
##        - Orthorectification of the input imagery
##        - Filtering
##        - Rescaling
##        - Tresholding (lower treshold for open water, upper treshold for land)
##        - Extraction of flooded vegetation
##
##        (FT4_FloodVegExtraction).
##
##        The script takes as input parameters  :
##
##            root directory in which it must find :
##                indir    RADARSAT-2 data input directory
##                inadir   Ancillary data directory
##                wdir     Working directory
##                outdir   Output products directory
##                logdir   Log file directory
##
##            landcover info :
##                land_cover Land cover file
##                DEM_file digital elevation model file
##
##            debugging parameters :
##            imp_im   Import imagery: 1 to process, 0 to skip
##            or_im    Orthorectify imagery: 1 to process, 0 to skip
##            fl_im    Filter imagery: 1 to process, 0 to skip
##            sc_im    Scale imagery: 1 to process, 0 to skip
##            th_im    THreshold imagery: 1 to process, 0 to skip
##            im_veg   Create Flooded vegetation product: 1 to process, 0 to skip
##
##            processing parameters :
##            im_pro   Image projection
##            im_pix_x Image pixel spacing in x
##            im_pix_y Image pixel spacing in y
##            v_th     Vegetation threshold
##            ow_th    Open water threshold
##            th_cal   Calculate threshold
##            ow_seed  Open water seed
##            fv_seed  Flood Vegetation seed
##            nfv_seed Non Flood Vegetation seed
##
##            m        Defines processing mode: "production" will delete all intermediate files, not implemented
##
##            h        Shows help and exit
##            c        Config file containing all required parameters
##            v        verbose
##
##            For testing purpose :
##            t        test
##            refr_file Reference raster file
##            refp_file Reference PCIDSK file
##            refp2_file Reference ortho PCIDSK file
##
##            '''
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
        # check for working, output and logs directory
        # create them if they dont exist
        # otherwise it deletes them and recreates them
        # not finished add more code


        import gdal
        import arcpy
        ##import required PCI Geomatica modules
        from pci.api import datasource as ds
        from pci.pcimod import pcimod
        from pci.exceptions import PCIException
        from pci.his import his
        from pci.nspio import Report, enableDefaultReport
##      importing some GDAL libs and numpy
        from osgeo import gdal, ogr, osr
        from gdalconst import GA_Update
        import numpy

        arcpy.AddMessage("Python Version: " + sys.version)
        arcpy.AddMessage("Current Product License: " + arcpy.ProductInfo())

        try:
            # More checks to make sure parameters provided are correct

            # Checking if VEGFEP folder exists
            # Reinitialises it if so
            if os.path.exists(str(str(parameters[0].value) + "\\VEGFEP\\")):
                shutil.rmtree(str(str(parameters[0].value) + "\\VEGFEP\\"))
                os.makedirs(str(str(parameters[0].value) + "\\VEGFEP\\"))
            else:
                os.makedirs(str(str(parameters[0].value) + "\\VEGFEP\\"))

            #create the base command call
            cmd =  'C:/Python27/ArcGISx6410.3/python.exe C:/EGS/applications/py/EGS_process.py '\
                   '--indir %s '\
                   '--wdir %s '\
                   '--outdir %s '\
                   '--logdir %s '\
                   '--lc_file %s '\
                   '--DEM_file %s '\
                   '--imp_im 1 --or_im 1 --fl_im 1 --sc_im 1 --th_im 1 --im_veg 1 '\
                   '--im_pro "%s" '\
                   '--im_pix_x %s '\
                   '--im_pix_y %s '\
                   % (
                                    #input dir
                                    str(str(parameters[0].value) + "\\Raw\\"),
                                    #working dir
                                    str(str(parameters[0].value) + "\\Scratch\\"),
                                    #output dir
                                    str(str(parameters[0].value) + "\\VEGFEP\\"),
                                    #log dir
                                    str(str(parameters[0].value)+ "\\logs\\"),
                                    #LandCover file (vegetation mask)
                                    str(parameters[1].value),
                                    # DEM file
                                    str(parameters[2].value),
                                    # projection code
                                    str(parameters[3].value),
                                    # x output scell resolution
                                    str(parameters[4].value).split(',')[0],
                                    # y output scell resolution
                                    str(parameters[4].value).split(',')[1],
                                    #vegetation threshold
                                    )

            arcpy.AddMessage("Seeds directory "+str(parameters[7].value))
            arcpy.AddMessage("Open water threshold "+str(parameters[5].value))
            arcpy.AddMessage("Flooded vegetation threshold  "+str(parameters[6].value))
##            arcpy.AddMessage(str(parameters[7].value), str(parameters[5].value), str(parameters[6].value))
            # Validation of thresholds parameters
            Thresholds = FT4_FloodVegExtraction.validateThresholds(str(parameters[7].value),
                                                        str(parameters[5].value),
                                                        str(parameters[6].value))


            # Appending to the command call based on the results of thresholds check
            if Thresholds[0] is not None:
                cmd = cmd + '--inadir %s ' \
                            '--th_cal 1 '\
                            '--ow_seed water.shp ' \
                            '--fv_seed veg_flood.shp ' \
                            '--nfv_seed veg_non_flood.shp' \
                             % (str(Thresholds[0]))
                arcpy.AddMessage("Seeds directory provided")
            else:
                cmd = cmd + '--inadir %s ' \
                            '--th_cal 0 '\
                            '--v_th %s ' \
                            '--ow_th %s ' \
                             % (str(str(parameters[0].value) + "\\Scratch\\"),
                             str(Thresholds[1]), str(Thresholds[2]))

            # Appending the final arguments to cmd call
            cmd = cmd + ' --m test -v'

            #
            arcpy.AddMessage(cmd)
            proc = subprocess.Popen(cmd, shell =True,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT)
            out, err = proc.communicate()
            result = out.split('/n')
            for lin in result:
                arcpy.AddMessage(lin)

            # Cleaning up scratch space
            try:
                if os.path.exists(str(str(parameters[0].value) + "\\Scratch\\")):
                    shutil.rmtree(str(str(parameters[0].value) + "\\Scratch\\"))
                    os.makedirs(str(str(parameters[0].value) + "\\Scratch\\"))
                else:
                    os.makedirs(str(str(parameters[0].value) + "\\Scratch\\"))
            except:
                line, filename, err = self.trace()
                msgText  = "ERROR:  Encountered exception in 'FT4_FloodVegExtraction.execute'.\n%s\n" % (ex)
                msgText += "        At line %s of file '%s'." % (str(line), filename)
                arcpy.AddError(msgText)
                # Assign a "Failure" status for return in "finally" block.
                return 1

            return 0

        except (Exception), ex:
            line, filename, err = self.trace()
            msgText  = "ERROR:  Encountered exception in 'FT4_FloodVegExtraction.execute'.\n%s\n" % (ex)
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
        filename = os.path.join(sys.path[0], "FT4_FloodVegExtraction.py")
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
            xmlFiles = glob.glob(os.path.join(workspace,'Raw','*', 'product.xml'))
            if xmlFiles:
                if len(xmlFiles) == 0:
                    return None
                else:
                    return xmlFiles
            else:
                return None


##    @staticmethod
##    def validateLandCover(LandCoverPath):
##        """
##        Confirms that Workspace directory exists, the user has access
##        privileges, and that at least 1 SAR ZIP file is present within the
##        directory.  Also returns a list of those ZIP files that the caller can
##        then use for flood processsing.
##
##        Parameters:
##            TYPE        NAME            DESCRIPTION
##            String      workspace       The path and name of the workspace
##                                        directory below which all flood work
##                                        is to take place.
##
##        Return Values:
##            String[]
##            - !None  List of SAR ZIP files that caller will use for
##                     downstream processing.
##            -  None  Workspace is invalid: it does not exist, user does not have
##                     read access to it, or no ZIP files are present.
##
##        Limit(s) and Constraint(s) During Use:
##            None.
##        """
##        if not os.path.isfile(LandCoverPath) or not os.access(LandCoverPath, os.R_OK):
##            return None
##        else:
##            lcFile = os.path.exists(LandCoverPath)
##            if lcFile:
##                if lcFile == False:
##                    return None
##                else:
##                    return lcFile
##            else:
##                return None

    @staticmethod
    def validateThresholds(SeedsDirPath,OW_thresh,FV_thresh):
        """
        Checking if Seeds directory  exists,
        if it finds it and the correct shape files it return True
        thre script will then modify the cmd call in order to use them
        instead of the default tresholds values
        If not it creates an empty Seeds folder and returns False
        Function then checks if thresholds values have been provided in parameters
        If yes it returns then, else it return defaults values.

        Parameters:
            TYPE        NAME            DESCRIPTION
            String      SeedsDirPath       The path and name of the directory into
                                        which the seeds files are located.
            String      OW_thresh       Open Water Threshold value
            String      FV_thresh       Flooded Vegetation Threshold value


        Return Values:
            List[B,F,F]
            - Thresholds[0] Boolean of presence or absence of Seeds dir.
                - True  seeds directory is valid the correct files are present.
                - False seeds directory is invalid: it does not exist,
                        user does not have read access to it, or no shapefiles are present.
            - Thresholds[1] Float value of OpenWater Threshold to be used by the script
                    If supplied in params this values is fed other wise default of -3.5
                    is provided
            - Thresholds[2] Float value of FloodVeg Threshold to be used by the script
                    if supplied in params this value is fed, otherwise default of -12.5
                    is provided.

        Limit(s) and Constraint(s) During Use:
            None.
        """
        def isfloat(value):
          try:
            float(value)
            return True
          except ValueError:
            return False

        Threshold = [None, "-3.5", "-12.5"]

        if OW_thresh is not None and FV_thresh is not None:
            if isfloat(OW_thresh):
                Threshold[1] = OW_thresh
            elif isfloat(FV_thresh):
                Threshold[2] = FV_thresh

##        if SeedsDirPath is not None and SeedsDirPath != "" :
        elif SeedsDirPath is not None:
            if os.path.exists(SeedsDirPath) == False:
                arcpy.AddMessage('Supplied Seeds Path is invalid, please correct' \
                                 'and try again, proceding with user defined values')
                Threshold[0] = None

            elif not os.path.isdir(SeedsDirPath) or not os.access(SeedsDirPath, os.R_OK):
                arcpy.AddMessage('Supplied Seeds Path is invalid, or does not' \
                                 ' have read write access, proceding with user defined values')
                Threshold [0] = None

            elif os.path.exists(os.path.join(SeedsDirPath, 'water.shp')) and \
                os.path.exists(os.path.join(SeedsDirPath, 'veg_flood.shp')) and \
                os.path.exists(os.path.join(SeedsDirPath, 'veg_non_flood.shp')):
                Threshold = [SeedsDirPath, None, None]

##        elif OW_thresh is not None and OW_thresh != "" and FV_thresh is not None and FV_thresh != "":

        else:
            arcpy.AddMessage('No thresholds values were provided, using defaults of -3.5 and -12.5')

        return(Threshold)


def main():
    """
        Allows FT4_FloodVegExtraction Tool to be executed from commmand line
        instead of GUI.

        Function "main()" allows the FT4_FloodVegExtraction module to be run as a
        script in batch, called from the command line or managing script rather
        than through a Toolbox in ArcCatalog or ArcMap, thereby bypassing the
        GUI interface provided by the Toolbox.  In this way, the application can
        be added to a processing chain, overseen by an orchestrating parent
        process, without requiring manual intervention between steps.  It uses
        argparse to exchange parameters with the command line.

        Usage:
            FT4_FloodVegExtraction.py [-h]
                                        -ws WORKSPACE -veg_mask FILE -proj "PROJECTION"
                                        -pix VALUE [-veg_tresh VALUE] [-ow_tresh VALUE]
        Parameters:
            Parameters that take a file name will accept either relative or
            absolute paths.

            -h,                         Optional
            --help
                                        Show this help message and exit.

            -ws WORKSPACE,              Mandatory
            --workspace WORKSPACE
                                        Workspace.  Root directory that contains
                                        the /raw folder in which the SAR ZIP files
                                        will be found. Processing will take place here.
                                        Script will create subdirectories
                                        'Scratch' and 'VEGFEP' if they are
                                        not already present.
                                        ZIP files in the 'Raw' directory,
                                        reproject and orthrectify the SAR
                                        images in the 'Scratch' directory, and
                                        mosaic the reprojected images in the
                                         .pix file associated.
                                        The script is also looking for a ./Seeds
                                        directory to train the flooded vegetation tresholds
                                        Example:
                                        B:\\Projects\\GRIP_Flood\\DEV\\2011_05_07\

            -veg_mask VEGMASK,          Mandatory
            --veg_mask VEGMASK
                                        Mask file or arborecent type land cover.
                                        Path and name of file used during
                                        the identification of the flooded
                                        vegetation zones during the processing.
                                        Areal coverage must be larger than
                                        images to which it will be applied.
                                        Example:
                                        D:\BaseData\Floods\VegMask\Richelieu_vegetationMask.shp

            -DEM DEM ,                      Mandatory
            --DEM DEM
                                        Digital elevation model for
                                        orthorectification process
                                        Path and name of file used during
                                        the orthoretification of the input
                                        imagery. Areal coverage must be larger than
                                        images to which it will be applied.
                                        Example:
                                        D:\BaseData\Floods\ON\DEM\CDED_Richelieu_Validation_UTM18_NAD83.tif

            -pix PIXELSPACE,            Optional
            --pixelspace PIXELSPACE
                                        Pixel Spacing.  Comma-delimited pair of
                                        numbers that identify the resolution in
                                        metres of each pixel in the
                                        orthorectified image, in the X and Y
                                        directions, respectively.  If not
                                        passed, will use a default value of
                                        "12.5,12.5".
                                        Example:
                                        30,30

            -proj PROJECTION,           Optional
            --projection PROJECTION
                                        Projection.  Used to reproject the
                                        incoming SAR images to the desired
                                        projection.  Will typically be comprised
                                        of two elements, the first being the
                                        code commonly used to identify the
                                        projection, and the second being PCI
                                        Geomatica's code for the datum (such as
                                        'D000' for WGS84 and 'D122' for NAD83).
                                        Examples:
                                        UTM 14 D122
                                        or
                                        CanLCC E008



            -veg_tresh VEG_TRESH        Optionnal
            --veg_tresh VEG_TRESH
                                        Defines the vegetation treshold necessary to
                                        differentiate the unflooded vegetation from
                                        the flooded one. A defalut value is defined in the
                                        or can be ommited if three training shapefiles
                                        required are present in the .\input_anc folder.
                                        they must be named veg_flood.shp; veg_non_flood.shp
                                        water.shp


            -water_tresh WATER_TRESH    Optionnal
            --water_tresh WATER_TRESH
                                        Defines the treshold value to differentiate the
                                        open water extent from the flooded vegetation
                                        lower value. Can be entered manually or overridden
                                        by supplying a shapefile (water.shp) into the
                                        .\Seeds folder.




        Return Values:
            Check on Windows OS with "echo %ERRORLEVEL%" after run.
            0       Successfully completed
            1       Error encountered during run.  Check messages issued to
                    standard output for details.
            2       Returned by "argparse" when mandatory parameter has not been
                    passed.

## To be updated
        Examples:
            Pass All Parameters
            -------------------
            C:\Python27\ArcGISx6410.3\python.exe FT4_FloodVegExtraction.py ^
            -ws "E:\Floods\ON_AlbanyRiverForks\20160510_232540_W2" ^
            -dem "E:\Floods\BaseData\ON\DEM\ON_FarNorth_UTM16_DEM_25.img" ^
            -proj "UTM 16 D122" -pix "12.5,12.5"

            Same As Above But Employs Default Pixel Spacing
            -----------------------------------------------
            C:\Python27\ArcGISx6410.3\python.exe FT4_FloodVegExtraction.py ^
            -ws "E:\Floods\ON_AlbanyRiverForks\20160510_232540_W2" ^
            -dem "E:\Floods\BaseData\ON\DEM\ON_FarNorth_UTM16_DEM_25.img" ^
            -proj "UTM 16 D122"


        Limit(s) and Constraint(s) During Use:
            Must be submitted through 64-bit Python.
    """
    # SAMPLE CALLS FOR TESTING
    #
    # GET USAGE / HELP (MUST Use 64-bit Python)
    # C:\Python27\ArcGISx6410.3\python.exe FT4_FloodVegExtraction.py -h
    #
    # ORTHORECTIFY AND MOSAIC SAR IMAGE
    # C:\Python27\ArcGISx6410.3\python.exe FT4_FloodVegExtraction.py ^
    # -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" ^
##    # -img "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Mosaic\20160510_UTM16_mos_HH.tif;E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Mosaic\20160510_UTM16_mos_HV.tif"
    #
##C:\Python27\ArcGISx6410.3\python.exe FT4_FloodVegExtraction.py -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" -img "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Mosaic\20160510_UTM16_mos_HH.tif;E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Mosaic\20160510_UTM16_mos_HV.tif"

    DEBUG = True   # Set to True to see incoming parameters before "execute"
##    DEBUG = True    # Set to True to see incoming parameters before "execute"
    try:
        if DEBUG:
            print 'Argument List:\n', str(sys.argv)

        # Get Command Line Arguments (if running in batch and not through GUI)
        parser = argparse.ArgumentParser(
                            formatter_class=argparse.RawTextHelpFormatter,
                            description=
                            "Extracts flooded vegetation areas from a SAR image. " +
                            "Read, orthorecify and rescale to sigma nought the SAR file. \n"               +
                            "Takes as input : one or several RADARSAT-2 scenes with associated product.xml files. \n" +
                            "A vegetation mask and a DEM. " +
                            "The tool will output a flooded vegetation product.\n",
                            epilog=
                            "Examples:\n"                                                           +
                            "  C:\\Python27\\ArcGISx6410.3\\python.exe FT4_Scale16to8BitSet.py ^\n" +
                            "  -ws \"B:\\Projects\\GRIP_Flood\\DEV\\2011_05_07\" ^\n"     +
                            "  -veg_mask \"B:\\Projects\\GRIP_Flood\\DEV\\2011_05_07\\Vegetation_mask\\richelieu_vegetation_mask_land_cover.shp\" ^\n" +
                            "  -DEM \"B:\\Projects\\GRIP_Flood\\DEV\\2011_05_07\\dem\\CDED_Richelieu_Validation_UTM18_NAD83.tif\" ^\n" +
                            "  -proj CanLCC      E008 -pix 12.5,12.5 -veg_tresh -3.5 -water_tresh -12.5 \n"
                            )

        parser.add_argument('-ws', '--workspace',
                            required=True, action='store', dest='workspace',
                            help= "Workspace.  Root directory that contains \n" +
                                "the /raw folder in which the SAR ZIP files \n" +
                                "will be found. Processing will take place here. \n" +
                                "Script will create subdirectories \n" +
                                "'Scratch' and 'VEGFEP' if they are \n" +
                                "not already present. \n" +
                                "ZIP files in the 'Raw' directory, \n" +
                                "reproject and orthrectify the SAR \n" +
                                "images in the 'Scratch' directory, and \n" +
                                "mosaic the reprojected images in the \n" +
                                " .pix file associated. \n" +
                                "The script is also looking for a ./Seeds \n" +
                                "directory to train the flooded vegetation tresholds \n" +
                                "Example: \n" +
                                "B:\Projects\GRIP_Flood\DEV\2011_05_07 \n"
                                 )

        parser.add_argument('-veg_mask', '--veg_mask',
                            required=True, action='store', dest='veg_mask',
                            help= "Mask file of arborecent type land cover. \n" +
                            "Path and name of file used during \n" +
                            "the identification of the flooded \n" +
                            "vegetation zones during the processing. \n" +
                            "Areal coverage must be larger than \n" +
                            "images to which it will be applied. \n" +
                            "The vegetation mask should only mask tree classes \n" +
                            "Example: \n" +
                            "D:\BaseData\Floods\VegMask\Richelieu_vegetationMask.shp \n"

                            )


        parser.add_argument('-DEM', '--DEM',
                            required=True, action='store', dest='DEM',
                            help= "Digital elevation model for \n" +
                            "orthorectification process \n" +
                            "Path and name of file used during \n" +
                            "the orthoretification of the input \n" +
                            "imagery. Areal coverage must be larger than \n" +
                            "images to which it will be applied. \n" +
                            "Example: \n" +
                            "D:\BaseData\Floods\ON\DEM\CDED_Richelieu_Validation_UTM18_NAD83.tif \n"
                            )


        parser.add_argument('-proj', '--projection',
                            required=False, action='store', dest='proj',
                            help= "Projection.  Used to reproject the \n" +
                            "incoming SAR images to the desired \n" +
                            "projection.  Will typically be comprised \n" +
                            "of two elements, the first being the \n" +
                            "code commonly used to identify the \n" +
                            "projection, and the second being PCI \n" +
                            "Geomatica's code for the datum (such as \n" +
                            "'D000' for WGS84 and 'D122' for NAD83). \n" +
                            "Examples: \n" +
                            "UTM 14 D122 \n" +
                            "or \n" +
                            "CanLCC E008 \n"
                            )

        parser.add_argument('-pix', '--pixelspace',
                            required=False, action='store', dest='pixXY',
                            help= "Pixel Spacing.  Comma-delimited pair of \n" +
                            "numbers that identify the resolution in \n" +
                            "metres of each pixel in the \n" +
                            "orthorectified image, in the X and Y \n" +
                            "directions, respectively.  If not \n" +
                            "passed, will use a default value of \n" +
                            '"12.5,12.5". \n' +
                            "Example: \n" +
                            "30,30 \n"
                            )

        parser.add_argument('-veg_tresh', '--veg_tresh',
                            required=False, action='store', dest='veg_tresh',
                            help= "Defines the vegetation treshold necessary to \n" +
                            "differentiate the unflooded vegetation from \n" +
                            "the flooded one. Default value of -3.5 is defined \n" +
                            "The use of training areas Greatly improved results. \n" +
                            "If supplied the training shapefiles are used instead.\n" +
                            "They must be present in a ./$workspace$/Seeds folder \n" +
                            "they must be named veg_flood.shp; veg_non_flood.shp \n" +
                            "and water.shp \n"
                            )


        parser.add_argument('-water_tresh', '--water_tresh',
                            required=False, action='store', dest='water_tresh',
                            help= "Defines the treshold value to differentiate the \n" +
                            "open water extent from the flooded vegetation \n" +
                            "lower value. Can be entered manually or overridden \n" +
                            "by supplying a shapefile (water.shp) into the \n" +
                            ".\Seeds folder. \n"
                            )


        cmdLineFlags = parser.parse_args()

        # Create FT4_FloodVegExtraction object and initialize its parameters.
        # Make sure relative paths are expressed as absolute paths or may get
        # error.
        #
        ft4Obj = FT4_FloodVegExtraction()
        params = ft4Obj.getParameterInfo()

        params[0].value = os.path.abspath(cmdLineFlags.workspace)
        params[1].value = os.path.abspath(cmdLineFlags.veg_mask)
        params[2].value = os.path.abspath(cmdLineFlags.DEM)
        params[3].value = os.path.abspath(cmdLineFlags.proj)
        params[4].value = os.path.abspath(cmdLineFlags.pixXY)
        params[5].value = os.path.abspath(cmdLineFlags.veg_tresh)
        params[6].value = os.path.abspath(cmdLineFlags.water_tresh)


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
        status = ft2Obj.execute(params, None)
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
