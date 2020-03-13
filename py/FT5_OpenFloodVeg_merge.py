#! /usr/bin/env python
# -*- coding: Latin-1 -*-
#! C:/Pythons27/ArcGISx6410.3/python.exe

__revision__ = "--REVISION-- : $Id:  $"



# Libraries
# =========
import arcpy
import argparse
import subprocess
import sys
import os
import datetime
import glob
import traceback
import shutil

import veg_open_merge
#import EGS_utility


# ======= #
# Globals #
# ======= #



class FT5_OpenFloodVeg_merge(object):
    """
    Performs fourth step in creating Flood Product.

    Is the fourth tool called in the procedure used to generate Flood Products.
    Starting in the workspace root directory, creates all subdirectories it
    requires if they are not already present (workdir, outdir, logs),
    then processes one or more polarized image files (HH, HV), present in the
    required ./indir directory. Some required files are required to be place in a
    directory called ./indir_anc, these files includes : a shapefile representing
    treed vegetation mask. Optionnally a set of three shapefiles representing
    training areas for non flooded vegetation(veg_non_flood.shp), flooded
    vegetation (veg_flood.shp) and open water (water.shp) can be used to overwrite
    the default tresholds values suggested by the GUI.


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

        self.label = "FT5_OpenFloodVeg_merge"
        self.description = "Extracts flooded vegetation areas from a SAR image. " \
                           "Read, orthorecify and rescale to sigma nought the SAR file. " \
                           "Takes as input : one or several RADARSAT-2 scenes with associated product.xml files. " \
                           "A vegetation mask and a DEM. " \
                           "The tool will output a flooded vegetation product. " \

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

        params = [None]*4

        params[0] = arcpy.Parameter(
             displayName   = "Workspace",
             name          = "workspace",
             datatype      = "DEFolder",
             parameterType = "Required",
             direction     = "Input"
             )
        params[0].value = None
##        params[0].value = "B:\\Projects\\GRIP_Flood\\DEV\\FloodTools"

##        params[1] = arcpy.Parameter(
##             displayName   = "Input Flooded Vegetation File",
##             name          = "flood_veg",
##             datatype      = ["DEFile"],
##             parameterType = "Required",
##             direction     = "Input"
##             )
##        # params[1].filter.list = ["tif","img"]
##        params[1].value = "B:\\Projects\\GRIP_Flood\\DEV\\FloodTools\\output\\FQ17_20110522_110144_vegflood.tif"

        params[1] = arcpy.Parameter(
             displayName   = "Input Open Water Flood File",
             name          = "open_flood",
             datatype      = ["DEFile"],
             parameterType = "Required",
             direction     = "Input"
             )
        #params[2].filter.list = ["shp"]
        params[1].value = ""

        params[2] = arcpy.Parameter(
                displayName   = "Minimum polygon size (Hectares)",
                name          = "min_polyS",
                datatype      = "GPString",
                parameterType = "Required",
                direction     = "Input"
             )
        params[2].value   = '2.5'
        #UTM Zone# + D122 which is PCI Geomatica code for NAD 83
        #http://www.pcigeomatics.com/geomatica-help/references/proj_r/proj3n149.html

        params[3] = arcpy.Parameter(
                displayName   = "Output Ortho Pixel Spacing",
                name          = "orthoPixelSpacing",
                datatype      = "GPString",
                parameterType = "Required",
                direction     = "Input"
             )
        params[3].value   = "12.5,12.5"

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
                FT5_OpenFloodVeg_merge.idxChangeField = i
                break

        return


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        # Index of last changed field, identified in "updateParameters":
        # - Map Template
        if FT5_OpenFloodVeg_merge.idxChangeField == 0:
            if parameters[0].value:
                # Verify that workspace exists, is accessible, and has at least
                # 1 vegflood.tif file present.
                vegFiles = self.validateWorkspace(str(parameters[0].value))
                if vegFiles == None:
                    msgText = "ERROR:  Workspace does not contain Flooded vegetation " \
                              "files, or do not have access privileges." \
                              "Files must be in folder ./VEGFEG/ the files must "  \
                              "be finish with the key word vegflood.tif."
                    parameters[0].setErrorMessage( msgText )

        # - Pixel Spacing
        elif FT5_OpenFloodVeg_merge.idxChangeField == 3:
            if parameters[3].value != None:
                msgText = FT5_OpenFloodVeg_merge.validatePixelSpacing(str(parameters[3].value))
                if msgText:
                    parameters[3].setErrorMessage( msgText )

        return


    def execute(self,parameters, messages):
        """The source code of the tool."""


        '''
        This part of the script calls methods found in within veg_open_merge.py
        A test wrapper tool named EGS_merge.py can also be called using the
        following parameter. EGS_merge has more options for debugging and testing

        EGS_merge.py has input parameters that can be added as command line
        arguments or read from a config file.
        For more information please consult the documentation.

        Parameters:
            indir       RADARSAT-2 data input directory
            wdir        Working directory
            outdir      Output products directory
            logdir      Log file directory
            vf_file     Vegetation flood file
            ow_file     Open water flood file
            hole_size   Filter size for holes and areas (hectares)
            h           Shows help and exit
            c           Config file containing all required parameters
            v           verbose
            t        test
            refr_file Reference vector file
            refp_file Reference raster file
            refp2_file Reference PCIDSK files

        Usage:
            EGS_merge  [-vf_file import_image] [-ow_file ortho_image]
                       [-indir input_dir] [-wdir work_dir] [-outdir output_dir]
                       [-logdir log_dir]
                       [-hole_size hole_size] [-v] [-t test]
                       [-refv_file refv_file] [-refr_file refr_file]
                       [-refp_file refp_file]
            EGS_merge  [-h ] show help and exit

        EGS_merge  [-c config file] [-v] [-t test]


        Limit ( s) and strain (s) of use:
            veg_open_merge.py must be available
            '''
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
        #    FT5_OpenFloodVeg_merge.py:477: SyntaxWarning: import * only allowed at module level
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

        import arcpy
        from arcpy import env
        import pci
        from pci.automos import automos
        from osgeo import gdal, ogr, osr
        from gdalconst import GA_Update

        env.workspace = parameters[0].value

        arcpy.AddMessage("Python Version: " + sys.version)
        arcpy.AddMessage("Current Product License: " + arcpy.ProductInfo())

##        try:
        root_path = str(parameters[0].value)

        #cleaning up scratch
        try:
            if os.path.exists(str(str(parameters[0].value) + "\\Scratch\\")):
                shutil.rmtree(str(str(parameters[0].value) + "\\Scratch\\"))
                os.makedirs(str(str(parameters[0].value) + "\\Scratch\\"))
            else:
                os.makedirs(str(str(parameters[0].value) + "\\Scratch\\"))
        except (Exception), ex:
            line, filename, err = self.trace()
            msgText  = "ERROR:  Encountered exception in 'FT5_OpenFloodVeg_merge.execute'.\n%s\n" % (ex)
            msgText += "        At line %s of file '%s'." % (str(line), filename)
            arcpy.AddError(msgText)
            # Assign a "Failure" status for return in "finally" block.
            return 1

        # assigning value to scratch path
        scratch_path = os.path.join(root_path, 'Scratch')
        # defining workspace to root/scratch
        env.workspace = scratch_path
        # Displaying the path for the user to see
        arcpy.AddMessage(root_path)
        arcpy.AddMessage(scratch_path)

        #rasterising input open water shapefile
        #--------------------------------------
        # defining input path of OWFEP
        in_owfep = str(parameters[1].value)
        # fetching the base nameof the file
        out_owfep_basename = os.path.splitext(os.path.basename(in_owfep))
        # defining outfile path and name
        out_owfep = str(os.path.join(root_path, 'Scratch', str(str(out_owfep_basename[0])+'.tif')))

        # x and y output scell resolution
        pix_X, pix_Y = str(parameters[3].value).split(',')[0], str(parameters[3].value).split(',')[1]

        # adding a field with a value of 1 for burning into the raster
        arcpy.AddField_management(in_owfep, "burn_value", 'SHORT')
        arcpy.CalculateField_management(in_owfep, "burn_value", '1', 'PYTHON_9.3')

        # converting shape file to a 8 bit raster for merging with the the flood veg layer
        arcpy.PolygonToRaster_conversion(in_owfep, "burn_value", out_owfep, "MAXIMUM_AREA", "", float(pix_X))

        # creating a list of floodeg vegetation raster to mosaic
        vegFile_list = glob.glob(str(os.path.join(root_path,'VEGFEP','*vegflood.tif')))
        # we then mosaic them together even if ehere is only one in order to rename it
        arcpy.MosaicToNewRaster_management(vegFile_list, scratch_path,'floodveg_mos.tif', "3978", '8_BIT_UNSIGNED', pix_X, '1', 'LAST', 'LAST')

##            OLD way of doing it...
##            cmd_rasterise = 'gdal_rasterize -burn 1 -of Gtiff -a_nodata 255 -ot byte -tr %s %s -tap %s %s' % (
##                                str(pix_X),
##                                str(pix_Y),
##                                str(in_owfep),
##                                str(out_owfep)
##                                )
##
##            #Mosaic flood veg raters using gdal
##
##            cmd_list_veg = 'dir /s /b %s >> %s' % (
##                                str(str(root_path) + '\\VEGFEP\\*vegflood.tif'),
##                                str(str(root_path) + '\\Scratch\\vegflood_list.txt')
##                                )
##
##            cmd_build_vrt = 'gdalbuildvrt -srcnodata "0 0 0" -vrtnodata "0 0 0" -hidenodata -input_file_list '\
##                            ' %s %s' % (
##                                str(str(parameters[0].value) + "\\Scratch\\vegflood_list.txt"),
##                                str(str(parameters[0].value) + "\\Scratch\\floodveg.vrt")
##                                )
##
##            cmd_translate = 'gdal_translate -of gtiff -ot byte -a_nodata 0 -co COMPRESS=LZW -co BIGTIFF=YES '\
##                            '-co TILED=YES -co BLOCKXSIZE=1024 -co BLOCKYSIZE=1024 --config GDAL_CACHEMAX 10240 '\
##                            '%s %s' % (
##                                str(str(parameters[0].value) + "\\Scratch\\floodveg.vrt"),
##                                str(str(parameters[0].value) + "\\Scratch\\floodveg_mos.tif")
##                                )
##
##            # call the merging routine while passing it the outputs from the
##            # previous steps (mosaicing and rasterising)
##
##
##            cmd_list = [cmd_rasterise, cmd_list_veg, cmd_build_vrt, cmd_translate]
##
##
##            for i in cmd_list:
##                arcpy.AddMessage(str(i))
##                proc = subprocess.Popen(str(i), shell =True,
##                                                 stdout=subprocess.PIPE,
##                                                 stderr=subprocess.STDOUT)
##
##
##                out, err = proc.communicate()
##
##                result = out.split('/n')
##                for lin in result:
##                    arcpy.AddMessage(lin)

        # check if MERGEFEP folder exists
        if os.path.exists(str(str(parameters[0].value) + "\\MERGEFEP\\")):
            os.system(' RD /S /Q %s' % (str(root_path + "\\MERGEFEP\\")))
            os.makedirs(str(str(parameters[0].value) + "\\MERGEFEP\\"))
        else:
            os.makedirs(str(str(parameters[0].value) + "\\MERGEFEP\\"))


        name_file = in_owfep
        out_basename = os.path.splitext(os.path.basename(name_file))
        out_file_pix = os.path.join(root_path, 'MERGEFEP', str(out_basename[0] + '_MergeFEP.pix'))
        out_file_tif = os.path.join(root_path, 'MERGEFEP', str(out_basename[0] + '_MergeFEP.tif'))
        out_file_shape = os.path.join(root_path, 'MERGEFEP', str(out_basename[0] + '_MergeFEP.shp'))

##            arcpy.AddMessage(str(out_file_pix))


        merge_process = veg_open_merge.MergeProcess()
        merge_process.merge_filter_export(str(os.path.join(str(parameters[0].value),"Scratch","floodveg_mos.tif ")), str(out_owfep), str(out_file_pix), str(out_file_tif), str(out_file_shape), float(parameters[2].value))

        '''
        finally:
            # Check in the Spatial Analyst extension
            arcpy.CheckInExtension("Spatial")

            # Clean up memory and temp files, if they exist (ie. created and not
            # previously removed before any exception redirection).  Will use
            # arcpy to do so rather than Python operating system functions
            # because the 'files' will actually consist of sets of files and
            # directories that share the same root names, and arcpy methods will
            # remove all related files.


            #arcpy.SetProgressorLabel("Remove Temporary Files...")
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
                           "'FT5_OpenFloodVeg_merge.execute' " \
                           "while removing temporary files.\n%s\n" % (ex)
                msgText += "          At line %s of file '%s'." % (str(line), filename)
                arcpy.AddWarning(msgText)

        '''
        return 0

##        except (Exception), ex:
##            line, filename, err = self.trace()
##            msgText  = "ERROR:  Encountered exception in 'FT5_OpenFloodVeg_merge'.\n%s\n" % (ex)
##            msgText += "        At line %s of file '%s'." % (str(line), filename)
##            arcpy.AddError(msgText)
##            # Assign a "Failure" status for return in "finally" block.
##            return 1

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
        filename = os.path.join(sys.path[0], "FT5_OpenFloodVeg_merge.py")
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
            vegFiles = glob.glob(os.path.join(workspace,'VEGFEP', '*vegflood.tif'))
            if vegFiles:
                if len(vegFiles) == 0:
                    return None
                else:
                    return vegFiles
            else:
                return None




def main():
    """
        Allows FT5_OpenFloodVeg_merge Tool to be executed from commmand line
        instead of GUI.

        Function "main()" allows the FT5_OpenFloodVeg_merge module to be run as a
        script in batch, called from the command line or managing script rather
        than through a Toolbox in ArcCatalog or ArcMap, thereby bypassing the
        GUI interface provided by the Toolbox.  In this way, the application can
        be added to a processing chain, overseen by an orchestrating parent
        process, without requiring manual intervention between steps.  It uses
        argparse to exchange parameters with the command line.

        Usage:
            FT5_OpenFloodVeg_merge.py [-h]
                                        -ws WORKSPACE -open_water FILE -min_poly_size "2.5 Ha"
        Parameters:
            Parameters that take a file name will accept either relative or
            absolute paths.

            -h,                         Optional
            --help
                                        Show this help message and exit.


            -ws WORKSPACE,              Mandatory
            --workspace WORKSPACE
                                        Workspace.  Root directory that the tool
                                        will use to find flooded vegetation files,
                                        mosaic them using the ./Scratch workspace.
                                        $_vegflood.tif files should be located in
                                        a VEGFEP folder in order to be located and
                                        mosaicked properly. _vegflood.tif is
                                        used as a keyword to identify files to
                                        be processed. Use accordingly.

                                        Example:
                                        B:\\Projects\\GRIP_Flood\\DEV\\2011_05_07\

            -open_water                 Optionnal
            --open_water                Defines the open water extent shape file
                                        to be used for merging with the extracted
                                        flooded vegetation areas. The open_water
                                        file must be a of the shape_file (.shp)
                                        type and must already be mosaiked if it
                                        was generated from more than one frame.
                                        The normal output of tool FT1 to FT3 is
                                        expected by this tool. User is free to
                                        feed an edited or clead up shape file

            -min_poly_size                  Optionnal
            --min_poly_size
                                        Defines the minimum polygon size for
                                        the identified flooded vegetation areas
                                        Polygons smaller than the specified size
                                        will be deleted. Hole will be filled.

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
            C:\Python27\ArcGISx6410.3\python.exe FT5_OpenFloodVeg_merge.py ^
            -ws "E:\Floods\ON_AlbanyRiverForks\20160510_232540_W2" ^
            -dem "E:\Floods\BaseData\ON\DEM\ON_FarNorth_UTM16_DEM_25.img" ^
            -proj "UTM 16 D122" -pix "12.5,12.5"

            Same As Above But Employs Default Pixel Spacing
            -----------------------------------------------
            C:\Python27\ArcGISx6410.3\python.exe FT5_OpenFloodVeg_merge.py ^
            -ws "E:\Floods\ON_AlbanyRiverForks\20160510_232540_W2" ^
            -dem "E:\Floods\BaseData\ON\DEM\ON_FarNorth_UTM16_DEM_25.img" ^
            -proj "UTM 16 D122"


        Limit(s) and Constraint(s) During Use:
            Must be submitted through 64-bit Python.
    """
    # SAMPLE CALLS FOR TESTING
    #
    # GET USAGE / HELP (MUST Use 64-bit Python)
    # C:\Python27\ArcGISx6410.3\python.exe FT5_OpenFloodVeg_merge.py -h
    #
    # ORTHORECTIFY AND MOSAIC SAR IMAGE
    # C:\Python27\ArcGISx6410.3\python.exe FT5_OpenFloodVeg_merge.py ^
    # -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" ^
    # -img "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Mosaic\20160510_UTM16_mos_HH.tif;E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Mosaic\20160510_UTM16_mos_HV.tif"
    #
##C:\Python27\ArcGISx6410.3\python.exe FT5_OpenFloodVeg_merge.py -ws "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2" -img "E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Mosaic\20160510_UTM16_mos_HH.tif;E:\FloodTest\ON_AlbanyRiverForks\20160510_232540_W2\Mosaic\20160510_UTM16_mos_HV.tif"

    DEBUG = False   # Set to True to see incoming parameters before "execute"
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
                            "  C:\\Python27\\ArcGISx6410.3\\python.exe FT5_OpenFloodVeg_merge.py ^\n" +
                            "  -ws \"B:\\Projects\\GRIP_Flood\\DEV\\2011_05_07\" ^\n"     +
                            "  -veg_mask \"B:\\Projects\\GRIP_Flood\\DEV\\2011_05_07\\Vegetation_mask\\richelieu_vegetation_mask_land_cover.shp\" ^\n" +
                            "  -DEM \"B:\\Projects\\GRIP_Flood\\DEV\\2011_05_07\\dem\\CDED_Richelieu_Validation_UTM18_NAD83.tif\" ^\n" +
                            "  -proj CanLCC      E008 -pix 12.5,12.5 -veg_tresh -3.5 -water_tresh -12.5 \n"
                            )

        parser.add_argument('-ws', '--workspace',
                            required=True, action='store', dest='workspace',
                            help= "Root directory that the tool \n" +
                                  "will use to find flooded vegetation files, \n" +
                                  "mosaic them using the ./Scratch workspace. \n" +
                                  "$_vegflood.tif files should be located in \n" +
                                  "a VEGFEP folder in order to be located and \n" +
                                  "mosaicked properly. _vegflood.tif is \n" +
                                  "used as a keyword to identify files to \n" +
                                  "be processed. Use accordingly. \n" +
                                  "Example: \n" +
                                  "B:\Projects\GRIP_Flood\DEV\2011_05_07 \n"
                                 )

        parser.add_argument('-open_water', '--open_water',
                            required=True, action='store', dest='open_water',
                            help=   "Open water file obtained from steps 1 to 3 \n" +
                                    "Input the path and name of the file obtained \n" +
                                    "during the identification of the flooded \n" +
                                    "areas processes. It must be a .shp file \n" +
                                    "The vegetation mask should only mask tree classes \n" +
                                    "Example: \n" +
                                    "D:\BaseData\Floods\VegMask\Richelieu_vegetationMask.shp \n"

                            )


        parser.add_argument('-min_poly_size', '--min_poly_size',
                            required=True, action='store', dest='min_poly_size',
                            help= "Minimum polygon size of the output merged product. \n" +
                            "This values is used to define minimum polygon and \n" +
                            "and minimum  \n" +
                            "Example: \n" +
                            "2.5 \n"
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


        cmdLineFlags = parser.parse_args()

        # Create FT5_OpenFloodVeg_merge object and initialize its parameters.
        # Make sure relative paths are expressed as absolute paths or may get
        # error.
        #
        ft5Obj = FT5_OpenFloodVeg_merge()
        params = ft5Obj.getParameterInfo()

        params[0].value = os.path.abspath(cmdLineFlags.workspace)
        params[1].value = os.path.abspath(cmdLineFlags.open_water)
        params[2].value = os.path.abspath(cmdLineFlags.min_poly_size)
        params[3].value = os.path.abspath(cmdLineFlags.pixXY)

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
        status = ft5Obj.execute(params, None)
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
