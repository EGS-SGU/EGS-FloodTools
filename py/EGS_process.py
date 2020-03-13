################################################################################
# Name : EGS_process.py
"""
    This is a test wrapper for all the functions within veg_flood_process.py

    EGS_process.py has input parameters that can be added as command line arguments or read from a config file.
    For more information please consult the documentation.

    Parameters:
        indir    RADARSAT-2 data input directory
        inadir   Ancillary data directory
        wdir     Working directory
        outdir   Output products directory
        logdir   Log file directory

        land_cover Land cover file
        DEM_file   Digital elevation model file

        imp_im   Import imagery: 1 to process, 0 to skip
        or_im    Orthorectify imagery: 1 to process, 0 to skip
        fl_im    Filter imagery: 1 to process, 0 to skip
        sc_im    Scale imagery: 1 to process, 0 to skip
        th_im    THreshold imagery: 1 to process, 0 to skip
        im_veg   Create Flooded vegetation product: 1 to process, 0 to skip

        im_pro   Image projection
        im_pix_x Image pixel spacing in x
        im_pix_y Image pixel spacing in y
        v_th     Vegetation threshold
        ow_th    Open water threshold
        th_cal   Calculate threshold
        ow_seed  Open water seed
        fv_seed  Flood Vegetation seed
        nfv_seed Non Flood Vegetation seed

        m        Defines processing mode: "production" will delete all intermediate files, not implemented

        h        Shows help and exit
        c        Config file containing all required parameters
        v        verbose
        t        test
        refr_file Reference raster file
        refp_file Reference PCIDSK file
        refp2_file Reference ortho PCIDSK file

    Usage:
        EGS_process  [-indir input_dir] [-inadir input_anc_dir] [-wdir work_dir] [-outdir output_dir] [-logdir log_dir]
                     [-lc_file land_cover] [-DEM_file DEM_file]
                     [-imp_im import_image] [-or_im ortho_image] [-fl_im filter_image]
                     [-sc_im scale_image] [-th_im thres_image] [-im_veg image_veg]
                     [-im_pro image_pro] [-im_pix_x image_pixspac_x] [-im_pix_y image_pixspac_y]
                     [-v_th veg_thres] [-ow_th openwater_thres] [-th_cal cal_thres] [-ow_seed openwater_seed]
                     [-fv_seed floodveg_seed] [-nfv_seed nfloodveg_seed] [-m process_mode] [-v] [-t test]
                     [-refr_file refr_file] [-refp_file refp_file] [-refp2_file refp2_file]
        EGS_process  [-h ] show help and exit
        EGS_process  [-c config file] [-v] [-t test]

    Limit ( s) and strain (s) of use:
        veg_flood_process.py must be available
"""
__revision__ = "--REVISION-- : $Id: EGS_process.py 255 2016-07-18 13:00:00Z jbennett $"
################################################################################

# Import public modules
import os
import sys
import argparse
import ConfigParser
import logging
# datetime conflicts with arcpy, therefore declare as dt
from datetime import datetime as dt

# Import private modules
import veg_flood_process
import ortho_mosaic
import EGS_utility

#import required PCI Geomatica modules
from pci.api import datasource as ds

defaultConfigFileName = os.path.basename(__file__)[:-3] + ".ini"

parser = argparse.ArgumentParser(description='Create Vegetation flood products.')
parser.add_argument("-c", "--conf_file",
                        help="Specify config file", metavar="FILE", default=defaultConfigFileName)
parser.add_argument("--indir",
                        help="RADARSAT-2 data input directory", metavar="indir")
parser.add_argument("--inadir",
                        help="Ancillary data input directory", metavar="inadir")
parser.add_argument("--wdir",
                        help="Working directory", metavar="wdir")
parser.add_argument("--outdir",
                        help="Output products directory", metavar="outdir")
parser.add_argument("--logdir",
                        help="Log file directory", metavar="logdir")

parser.add_argument("--lc_file",
                        help="Land cover file", metavar="lc_file")
parser.add_argument("--DEM_file",
                        help="DEM file", metavar="DEM_file")

parser.add_argument("--imp_im",
                        help="Import imagery: 1 to process, 0 to skip", metavar="imp_im")
parser.add_argument("--or_im",
                        help="Orthorectify imagery: 1 to process, 0 to skip", metavar="or_im")
parser.add_argument("--fl_im",
                        help="Filter imagery: 1 to process, 0 to skip", metavar="fl_im")
parser.add_argument("--sc_im",
                        help="Scale imagery: 1 to process, 0 to skip", metavar="sc_im")
parser.add_argument("--th_im",
                        help="Threshold imagery: 1 to process, 0 to skip", metavar="th_im")
parser.add_argument("--im_veg",
                        help="Create Flooded vegetation product", metavar="im_veg")

parser.add_argument("--im_pro",
                        help="Image projection", metavar="im_pro")
parser.add_argument("--im_pix_x",
                        help="Image pixel spacing in x", metavar="im_pix_x")
parser.add_argument("--im_pix_y",
                        help="Image pixel spacing in y", metavar="im_pix_y")
parser.add_argument("--v_th",
                        help="Vegetation threshold", metavar="v_th")
parser.add_argument("--ow_th",
                        help="Open water threshold", metavar="ow_th")
parser.add_argument("--th_cal",
                        help="Calculate threshold", metavar="th_cal")
parser.add_argument("--ow_seed",
                        help="Open water seed", metavar="ow_seed")
parser.add_argument("--fv_seed",
                        help="Flood Vegetation seed", metavar="fv_seed")
parser.add_argument("--nfv_seed",
                        help="Non Flood Vegetation seed", metavar="nfv_seed")
parser.add_argument("--m",
                        help="defines processing mode: production will delete all intermediate files, not implemented ", metavar="m")
parser.add_argument("--refr_file",
                        help="Reference raster file required for testing", metavar="refr_file")
parser.add_argument("--refp_file",
                        help="Reference PCIDSK file required for testing", metavar="refp_file")
parser.add_argument("--refp2_file",
                        help="Reference ortho PCIDSK file required for testing", metavar="refp2_file")
parser.add_argument("-v", "--verbose",
                        help="Verbose output", action='store_true')
parser.add_argument("-t", "--test", type=int, choices=[0, 1],
                    help="increase test; compare results to reference data. 1=compare only final product.")

verbose = False
if len(sys.argv) == 1:
    if os.path.exists(defaultConfigFileName):
        args = argparse.Namespace(conf_file=defaultConfigFileName)
    else:
        parser.print_help();
        sys.exit(1)
else:
    args = parser.parse_args()

refr_file = ''
refp_file = ''
refp2_file = ''
DEM_file = ''
# =============================================================================
# 	Mainline
# =============================================================================
# Check if config file exists
if os.path.exists(args.conf_file) and len(sys.argv) <= 4:
    Config = ConfigParser.ConfigParser()
    Config.read(args.conf_file)
    input_dir       =   Config.get("DirStructure","input_dir")
    input_anc_dir   =   Config.get("DirStructure","input_anc_dir")
    work_dir        =   Config.get("DirStructure","work_dir")
    output_dir      =   Config.get("DirStructure","output_dir")
    log_dir         =   Config.get("DirStructure","log_dir")

    land_cover      =   Config.get("AncFiles","land_cover")
    DEM_file        =   Config.get("AncFiles","DEM_file")

    import_image    =   Config.getint("ProcessPar","import_image")
    ortho_image     =   Config.getint("ProcessPar","ortho_image")
    filter_image    =   Config.getint("ProcessPar","filter_image")
    scale_image     =   Config.getint("ProcessPar","scale_image")
    thres_image     =   Config.getint("ProcessPar","thres_image")
    import_veg      =   Config.getint("ProcessPar","import_veg")
    cal_thres       =   Config.getint("ProcessPar","cal_thres")

    image_pro       =   Config.get("DataPar","image_pro")
    image_pixspac_x =   Config.getint("DataPar","image_pixspac_x")
    image_pixspac_y =   Config.getint("DataPar","image_pixspac_y")
    veg_thres       =   Config.getfloat("DataPar","veg_thres")
    openwater_thres =   Config.getfloat("DataPar","openwater_thres")
    openwater_seed  =   Config.get("DataPar","openwater_seed")
    floodveg_seed   =   Config.get("DataPar","floodveg_seed")
    nfloodveg_seed  =   Config.get("DataPar","nfloodveg_seed")

    mode            =   Config.get("ProcessMode","mode")
    refr_file       =   Config.get("Testparameters","refr_file")
    refp_file       =   Config.get("Testparameters","refp_file")
    refp2_file      =   Config.get("Testparameters","refp2_file")

else:
    if args.indir is None or args.inadir is None or args.wdir is None or args.outdir is None \
    or args.logdir is None or args.lc_file is None or args.DEM_file is None or args.imp_im is None \
    or args.or_im is None or args.fl_im is None or args.sc_im is None or args.th_im is None \
    or args.im_veg is None or args.im_pro is None or args.im_pix_x is None or args.im_pix_y is None \
    or args.th_cal is None or args.m is None:
        print "Missing parameter, see EGS_process.py usage for required argument"
        parser.print_help();
        sys.exit(1)
    elif args.ow_seed is None and args.fv_seed is None and args.nfv_seed is None \
         and args.v_th is None and args.ow_th is None:
        print "  \n" \
              "                  !!!!!  WARNING  !!!!!                \n" \
              "  \n" \
              "Missing thresholds parameters, Using default values of -3.5 and -12.5" \
              " for open water and flooded vegetation respectively" \
              "  \n"

##        sys.exit(1)
    if args.indir is not None:
        input_dir = args.indir
    if args.inadir is not None:
        input_anc_dir = args.inadir
    if args.wdir is not None:
        work_dir = args.wdir
    if args.outdir is not None:
        output_dir = args.outdir
    if args.logdir is not None:
        log_dir = args.logdir

    if args.lc_file is not None:
        land_cover = args.lc_file
    if args.DEM_file is not None:
        DEM_file = args.DEM_file

    if args.imp_im is not None:
        import_image = int(args.imp_im)
    if args.or_im is not None:
        ortho_image = int(args.or_im)
    if args.fl_im is not None:
        filter_image = int(args.fl_im)
    if args.sc_im is not None:
        scale_image = int(args.sc_im)
    if args.th_im is not None:
        thres_image = int(args.th_im)
    if args.im_veg is not None:
        import_veg = int(args.im_veg)

    if args.im_pro is not None:
        image_pro = args.im_pro
    if args.im_pix_x is not None:
        image_pixspac_x = float(args.im_pix_x)
    if args.im_pix_y is not None:
        image_pixspac_y = float(args.im_pix_y)
    if args.v_th is not None:
        veg_thres = float(args.v_th)
    else:
        veg_thres = None
    if args.ow_th is not None:
        openwater_thres = float(args.ow_th)
    else:
        openwater_thres = None
    if args.th_cal is not None:
        cal_thres = float(args.th_cal)
    if args.ow_seed is not None:
        openwater_seed = str(args.ow_seed)
    else:
        openwater_seed = None
    if args.fv_seed is not None:
        floodveg_seed = str(args.fv_seed)
    else:
        floodveg_seed = None
    if args.nfv_seed is not None:
        nfloodveg_seed = str(args.nfv_seed)
    else:
        nfloodveg_seed = None
    if args.m is not None:
        mode = args.m
    if args.refr_file is not None:
        refr_file = args.refr_file
    if args.refp_file is not None:
        refp_file = args.refp_file
    if args.refp2_file is not None:
        refp2_file = args.refp2_file

verbose = False
if len(sys.argv) > 1:
    if args.verbose:
        verbose = True

test =0
if len(sys.argv) > 1:
    if args.test:
        test = args.test

# Check if Log directory exists
if not os.path.isdir(log_dir):
    print "Log directory not found, creating log directory: ", log_dir
    os.makedirs(log_dir)

#Setup logger
datetime1 = dt.now().strftime('_%Y_%m_%d_%H_%M_%S_')
logfile = log_dir + 'EGS_process_' + datetime1 + '.log'
EGS_utility.EGSUtility().setup_logger(logfile, verbose)

logging.info('Executing  EGS Merge processing: EGS_merge.py' )
logging.info('   EGS VEG PROCESS PARAMETER SETTINGS:')
logging.info('       Input dir: ' + input_dir)
logging.info('       Input ancillary dir: ' + input_anc_dir)
logging.info('       Working dir: ' + work_dir)
logging.info('       Output dir: ' + output_dir)
logging.info('       Log dir: ' + log_dir)
logging.info('       land cover: ' + land_cover)
logging.info('       DEM file: ' + DEM_file)
logging.info('       Import image:' + str(import_image))
logging.info('       Ortho image: ' + str(ortho_image))
logging.info('       Filter image: ' + str(filter_image))
logging.info('       Scale image: ' + str(scale_image))
logging.info('       Import Veg Land Cover: ' + str(import_veg))
logging.info('       Threshold image: ' + str(thres_image))
logging.info('       Veg threshold: ' + str(veg_thres))
logging.info('       Open water threshold: ' + str(openwater_thres))
logging.info('       Calculate thresholds: ' + str(cal_thres))
logging.info('       Open water seed file: ' + str(openwater_seed))
logging.info('       Flood Vegetation seed file: ' + str(floodveg_seed))
logging.info('       Non Flood Vegetation seed file: ' + str(nfloodveg_seed))
logging.info('       Image projection info: ' + str(image_pro))
logging.info('       Image pixel spacing x: ' + str(image_pixspac_x))
logging.info('       Image pixel spacing y: ' + str(image_pixspac_y))
logging.info('       Mode: ' + mode)
logging.info('       Reference raster file: ' + refr_file)
logging.info('       Reference PCIDSK file: ' + refp_file)
logging.info('')

# Check if directory structure is correct.
if not os.path.isdir(input_dir):
    logging.info('No input directory defined by as:  ' + input_dir)
    logging.info('Creating input directory and exiting. Please add RADARSAT-2 datasets to this')
    logging.info('directory and restart process.')
    os.makedirs(input_dir)
    sys.exit(1)
if not os.path.isdir(input_anc_dir):
    logging.info('No ancillary directory defined by as:  ' + input_anc_dir)
    logging.info('Creating ancillary directory and exiting. Please add ancillary datasets')
    logging.info('(e.g. Vegetation Land Cover data) to this directory and restart process.')
##    os.makedirs(input_anc_dir)
    sys.exit(1)
if not os.path.isdir(work_dir):
    logging.info('Working directory not found, creating working directory:  ' + work_dir)
    os.makedirs(work_dir)
if not os.path.isdir(output_dir):
    logging.info('Output directory not found, creating working directory:  ' + output_dir)
    os.makedirs(output_dir)

if cal_thres:
    logging.info('   Validating thresholds...  ')
    # if calculating thresholds, check to see if seed files exist.
    openwater_seed = os.path.join(input_anc_dir, openwater_seed)
    # Check if open water seed file exists
    if not os.path.exists(openwater_seed):
        logging.info('   File must exist in order to import: ' + openwater_seed)
        logging.info('   Proceding with default values')
##        sys.exit(1)
    floodveg_seed = os.path.join(input_anc_dir, floodveg_seed)
    # Check if flood veg seed file exists
    if not os.path.exists(floodveg_seed):
        logging.info('   File must exist in order to import: ' + floodveg_seed)
        logging.info('   Proceding with default values')
##        sys.exit(1)
    nfloodveg_seed = os.path.join(input_anc_dir, nfloodveg_seed)
    # Check if non-flood veg seed file exists
    if not os.path.exists(nfloodveg_seed):
        logging.info('   File must exist in order to import: ' + nfloodveg_seed)
        logging.info('   Proceding with default values')
##        sys.exit(1)

# Determine if the vegetation land cover shapefile exists.
# for anc_subdir, anc_dirs, anc_files in os.walk(input_anc_dir):
    # for anc_file in anc_files:
        # if anc_file.endswith (land_cover):
            # in_file_veg = os.path.join(anc_subdir, anc_file)
            # out_file_veg =  work_dir + os.path.splitext(anc_file)[0] + '.pix'
            # logging.info('   input Veg Land Cover: ' + in_file_veg)
            # logging.info('   output Veg Land Cover: ' + out_file_veg)

in_file_veg = land_cover
out_veg_basename = os.path.splitext(os.path.basename(land_cover))
out_file_veg = os.path.join(work_dir, 'working', out_veg_basename[0],'.pix')
logging.info('   input Veg Land Cover: ' + in_file_veg)
logging.info('   output Veg Land Cover: ' + out_file_veg)

# Check if reference files exists if testing
if test > 0:
    if not os.path.exists(refr_file):
        logging.info('   Reference raster file must exist when run comparison test: ' + refr_file)
        sys.exit(1)
if test > 1:
    if not os.path.exists(refp_file):
        logging.info('   Reference PCIDSK file must exist when run comparison test: ' + refp_file)
        sys.exit(1)
    if not os.path.exists(refp2_file):
        logging.info('   Reference PCIDSK file must exist when run comparison test: ' + refp2_file)
        sys.exit(1)

# Assign processing variables
report_file = work_dir  + 'report.txt'
veg_process = veg_flood_process.VegFloodProcess()
ortho_m = ortho_mosaic.OrthoMosaic()
in_file = ''
out_file = ''
out_file_ortho = ''
out_file_vegflood = ''
image_stats = []
filter_channel = ''
scale_channel = ''
flood_seg= []

# Process all RADARSAT-2 datasets (products) in the input directory.
for subdir, dirs, files in os.walk(input_dir):
    for file in files:
        if file.endswith ('product.xml'):
            in_file = os.path.join(subdir, file)
            out_file =  work_dir + os.path.basename(os.path.normpath(subdir))[30:49] + '.pix'
            out_file_ortho = work_dir + os.path.basename(os.path.normpath(subdir))[30:49] + '_ortho.pix'
            out_file_vegflood = output_dir + os.path.basename(os.path.normpath(subdir))[30:49] + '_vegflood.tif'

            logging.info('')
            logging.info('Processing')
            logging.info('   input: ' + in_file)
            logging.info('   PCIPIX output: '  + out_file)
            logging.info('   ortho output: ' + out_file_ortho)
            logging.info('')

            # Import RADARSAT-2 Imagery
            if import_image:
                if not os.path.isfile(in_file):
                    logging.info('   File must exist in order to import:' + in_file)
                else:
                    if os.path.isfile(out_file):
                        logging.info('   Not importing, file already exists: ' + out_file)
                    else:
                        logging.info('   Importing: ' + in_file)
                        ortho_m.import_sar(in_file,out_file)

            # Orthorectify imagery
            if ortho_image:
                if not os.path.isfile(out_file):
                    logging.info('   File must exist in order to ortho: ' + out_file)
                else:
                    if os.path.isfile(out_file_ortho):
                        logging.info('   No ortho applied, file already exists: ' + out_file_ortho)
                    else:
                        logging.info('   Orthorectify image in process for ' + out_file_ortho)
                        ortho_m.orthorectify(out_file,out_file_ortho,DEM_file,image_pixspac_x,image_pixspac_y,image_pro)

            # Filter imagery
            if filter_image:
                if not os.path.isfile(out_file_ortho):
                    logging.info('   File must exist in order to apply filter:' + out_file_ortho)
                else:
                    logging.info('   Filtering image in process for ' + out_file_ortho)
                    filter_channel = veg_process.filter_sar(out_file_ortho)

            # Scale imagery
            if scale_image:
                if not filter_image:
                    filter_channel = "3"
                if not os.path.isfile(out_file_ortho):
                    logging.info('   File must exist in order to apply scale: ' + out_file_ortho)
                else:
                    logging.info('   Scaling image in process for ' + out_file_ortho)
                    scale_channel = veg_process.scale_sar(out_file_ortho, filter_channel)
                    logging.info('       scale_channel: ' + scale_channel)

            # Threshold imagery: Low for open water, high for flooded vegetation
            if thres_image:
                if not scale_image:
                    scale_channel = "4"
                logging.info('   Threshold imagery in process...  ')
                if cal_thres:
                    logging.info('   Calculating thresholds from seed files...  ')

                    # Work around for determining new vector segments
                    #   Add bitmap just to determine segment number
                    #   The following 3 vector segments will be consecutive #s after this bitmap
                    #   PCI 2016 support Vector segment read, but not PCI2015
                    #   gdal can not determine the correct vector segment #
                    #   Create and name newly created segment
                    dataset = ds.open_dataset(out_file_ortho, ds.eAM_WRITE)
                    #   Get the number of the newly created bitmap segment
                    bitmap_seg = dataset.create_bitmap()
                    veg_process.import_vector(openwater_seed,out_file_ortho)
                    veg_process.import_vector(nfloodveg_seed,out_file_ortho)
                    veg_process.import_vector(floodveg_seed,out_file_ortho)
                    water_vseg = bitmap_seg + 1
                    veg_non_flood_vseg = bitmap_seg + 2
                    veg_flood_vseg = bitmap_seg + 3

                    water_bseg = veg_process.vegcover2bit(out_file_ortho, out_file_ortho,water_vseg)
                    veg_non_flood_bseg = veg_process.vegcover2bit(out_file_ortho, out_file_ortho,veg_non_flood_vseg)
                    veg_flood_bseg = veg_process.vegcover2bit(out_file_ortho, out_file_ortho,veg_flood_vseg)
                    stat_info_water = EGS_utility.EGSUtility().raster_his(out_file_ortho,int(scale_channel),water_bseg,report_file)
                    stat_info_veg_non_flood = EGS_utility.EGSUtility().raster_his(out_file_ortho,int(scale_channel),veg_non_flood_bseg,report_file)
                    stat_info_veg_flood = EGS_utility.EGSUtility().raster_his(out_file_ortho,int(scale_channel),veg_flood_bseg,report_file)
                    water_mean = stat_info_water[1]
                    water_std_dev = stat_info_water[3]
                    veg_non_flood_mean = stat_info_veg_non_flood[1]
                    veg_non_flood_std_dev = stat_info_veg_non_flood[3]
                    veg_flood_mean = stat_info_veg_flood[1]
                    veg_flood_std_dev = stat_info_veg_flood[3]
                    water_max = water_mean + 2*water_std_dev
                    non_flood_min = veg_non_flood_mean - 2*veg_non_flood_std_dev
                    non_flood_max = veg_non_flood_mean + 2*veg_non_flood_std_dev
                    flood_min = veg_flood_mean - 2*veg_flood_std_dev

                    if ((water_max < non_flood_min)&(flood_min > non_flood_max)):
                        veg_thres = flood_min
                        openwater_thres = water_max
                    else:
                        logging.info('       SEED ERROR: ' )
                        logging.info('            Seed polygons must be modified or threshold values must be manually calculated and ' )
                        logging.info('           provided as input. ' )
                        logging.info('            The following criteria must be met but was not, therefore process stopped: ' )
                        logging.info('            (water_max < non_flood_min)&(flood_min > non_flood_max) ' )
                        logging.info('            The following seed values were determined from the seed polygons:' )
                        logging.info('              Water max value: ' + str(water_max))
                        logging.info('              Non flood veg min value: ' + str(non_flood_min))
                        logging.info('              Flood veg min value: ' + str(flood_min))
                        logging.info('              Proceeding with default value of -3.5 and -12.5 for open water and flooded vegetation')

                        print '       SEED ERROR: '
                        print '            Seed polygons must be modified or threshold values must be manually calculated and '
                        print '            provided as input. '
                        print '            The following criteria must be met but was not, therefore process stopped: '
                        print '            (water_max < non_flood_min)&(flood_min > non_flood_max) '
                        print '            The following seed values were determined from the seed polygons:'
                        print '              Water max value: ' + str(water_max)
                        print '              Non flood veg min value: ' + str(non_flood_min)
                        print '              Flood veg min value: ' + str(flood_min)
                        print('              Proceeding with user values if provided or default values of -3.5 and -12.5 for ' \
                                             'open water and flooded vegetation')
##                        sys.exit(1)
                    if openwater_thres is None:
                        openwater_thres = float("-3.5")
                    if veg_thres is None:
                        veg_thres = float("-12.5")

                    logging.info('       water_mean: ' + str(water_mean))
                    logging.info('       water_std_dev: ' + str(water_std_dev))
                    logging.info('       water_max: ' + str(water_max))
                    logging.info('       veg_non_flood_mean: ' + str(veg_non_flood_mean))
                    logging.info('       veg_non_flood_std_dev: ' + str(veg_non_flood_std_dev))
                    logging.info('       non_flood_min: ' + str(non_flood_min))
                    logging.info('       non_flood_max: ' + str(non_flood_max))
                    logging.info('       veg_flood_mean: ' + str(veg_flood_mean))
                    logging.info('       veg_flood_std_dev: ' + str(veg_flood_std_dev))
                    logging.info('       flood_min: ' + str(flood_min))
                    logging.info('       veg_thres: ' + str(veg_thres))
                    logging.info('       openwater_thres: ' + str(openwater_thres))

                if openwater_thres is None:
                    openwater_thres = float("-3.5")
                if veg_thres is None:
                    veg_thres = float("-12.5")
                flood_seg = veg_process.threshold_sar(out_file_ortho, int(scale_channel), veg_thres, openwater_thres)
                logging.info('       Veg segment: ' + str(flood_seg[0]))
                logging.info('       Water segment: ' + str(flood_seg[1]))
                #stat_info = EGS_utility.EGSUtility().raster_his(out_file_ortho,int(scale_channel),veg_bitmap,report_file)

            # Import Vegetation Land Cover shapefile, combine with derived flood veg layer and
            # Export result as a Geotiff
            if import_veg:
                if not thres_image:
                    flood_seg = [2,3]
                # Work around for determining new vector segments
                #   PCI 2016 support Vector segment read, but not PCI2015
                #   Add bitmap just to determine segment number
                dataset = ds.open_dataset(out_file_ortho, ds.eAM_WRITE)
                #   Get the number of the newly created bitmap segment
                bitmap_seg = dataset.create_bitmap()
                veg_channel = bitmap_seg + 1
                veg_process.import_vegcover(in_file_veg,out_file_ortho)
                veg_cover_seg = veg_process.vegcover2bit(out_file_ortho, out_file_ortho,veg_channel)
                logging.info('       veg_cover_seg: ' + str(veg_cover_seg))

                vegflood_channel = veg_process.combine_veglayers(out_file_ortho,flood_seg[0],flood_seg[1],veg_cover_seg)
                veg_process.export_vegflood(out_file_ortho,out_file_vegflood,vegflood_channel)

            # Perform test, compare results to reference
            if test > 1:
                EGS_utility.EGSUtility().test_raster(refp_file,out_file,report_file)
                EGS_utility.EGSUtility().test_raster(refp2_file,out_file_ortho,report_file)
            if test > 0:
                EGS_utility.EGSUtility().test_raster(refr_file,out_file_vegflood,report_file)
logging.info('Completed EGS_Process')
