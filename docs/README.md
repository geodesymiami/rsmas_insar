## RSMAS InSAR code

The Miami INterferometric SAR software  (MinSAR) is an open-source python package for Interferometric Synthetic Aperture Radar processing and time series analysis written at the Geodesy Lab of the University of Miami at the Rosenstiel School of Marine and Atmospheric Science (RSMAS). MinSAR uses the following packages:

[ISCE](https://github.com/isce-framework/isce2), [MintPy](https://github.com/insarlab/MintPy), [PyAPS](https://github.com/yunjunz/pyaps3), [MiNoPy](https://github.com/geodesymiami/miaplpy)

The main Developers are Sara Mirzaee and Falk Amelung with contributions of many University of Miami graduate and undergraduate students.

## 1. [Installation](./installation.md) ###

## 2. Running MinSAR ###

MinSAR downloads a stack of SLC images, downloads a DEM, processes the interferograms and creates displacement timeseries products. Optional steps are the ingestion into our [dataportal] (https//:insarmaps.miami.edu) and the generation of image products that will soon be made available from another data portal.

The processing is controlled by a template file which offers many different options for each processing step ([see example])(../samples/GalapagosSenDT128.template). The processing is executed using `process_rsmas.py` with the processing steps specified on the command line. Steps:
```
download:   downloading data
dem:        downloading DEM
ifgrams:    processing interferograms starting with unpacking of the images
timeseries: time series analysis based on smallbaseline method or single master interferograms (MintPy or MiNoPy)
insarmaps:  uploading displacement products to insarmaps website
image_products: generating and uploading image products to hazards website (amplitudes, interferograms, coherences)
```
Processing can be started at a given step using the `--start` option. The `--dostep`  option allows to execute only one processing step. Example: 
```bash
  process_rsmas.py  $SAMPLESDIR/GalapagosSenDT128.template             # run with default and custom templates
  process_rsmas.py  $SAMPLESDIR/GalapagosSenDT128.template  --submit   # submit as job
  process_rsmas.py  -h / --help                      # help 
  process_rsmas.py -H                                # print    default template options

# Run with --start/stop/step options
  process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --dostep  download        # run the step 'download' only
  process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --start download        # start from the step 'download' 
  process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --stop  ifgrams         # end after step 'interferogram'
```
In order to use either `--start` or `--step`, it is necessary that the previous step was completed.

## 3. Example for Galápagos with Sentinel-1 data ####
The individual processing steps can be run stepwise using
```bash
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --dostep  download
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --dostep  dem
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --dostep  ifgrams
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --dostep  timeseries
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --dostep  insarmaps
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --dostep  image_products
```

These commands run the following scripts:
```
download_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template
dem_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template
create_runfiles.py $SAMPLESDIR/GalapagosSenDT128.template
execute_runfiles.py $SAMPLESDIR/GalapagosSenDT128.template
smallbaseline_wrapper.py $SAMPLESDIR/GalapagosSenDT128.template
miaplpy_wrapper.py $SAMPLESDIR/GalapagosSenDT128.template
ingest_insarmaps.py $SAMPLESDIR/GalapagosSenDT128.template
export_ortho_geo.py $SAMPLESDIR/GalapagosSenDT128.template
````
The  processing steps are recorded in the `./log` file in your project directory.

## 4. Processing steps

### 4.1 Download data: --step download
The `download_data.py` script downloads data based on the `ssaraopt` parameters in the template file. It will create an `--intersectsWith={Polygon ..)` string based on `topsStack.boundingBox`.

```################################# ssara option Parameters #################################
ssaraopt.platform                     = None         # platform name [SENTINEL-1A, ...]
ssaraopt.relativeOrbit                = None         # relative orbit number
ssaraopt.startDate                    = None         # starting acquisition date [YYYYMMDD]
ssaraopt.endDate                      = None         # ending acquisition date [YYYYMMDD]

topsStack.boundingBox                 = None         # [ -1 0.15 -91.7 -90.9] lat_south lat_north lon_west lon_east
```
It also accepts the `ssaraopt.frame` option but this did not work very well for us.

Examples:
```
download_data.py $SAMPLESDIR/GalapagosSenDT128.template

# submit as a job:
download_data.py $SAMPLESDIR/GalapagosSenDT128.template --submit

# Add a value of 0.1 to latitude from boundingBox field (default is 0.0):       
download_data.py $SAMPLESDIR/GalapagosSenDT128.template --delta_lat 0.1  
 ```
`download_data.py` calls two scripts. `download_ssara.py` and `download_asfserial.py` The first uses `ssara_federated_query-cj.py` and the second the ASF python download script.  The scripts can be called individually:
```
download_ssara.py $SAMPLESDIR/GalapagosSenDT128.template --delta_lat 0.1  
download_asfserial.py $SAMPLESDIR/GalapagosSenDT128.template --delta_lat 0.1 
```
* [Trouble shooting](./download_data_troubleshooting.md)

### 4.2. Download DEM: --dostep dem
Downaloading DEM from the USGS
* [Trouble shooting](./download_dem_troubleshooting.md)

### 4.3. Process interferograms: --dostep ifgrams

```
create_runfiles
execute_run_files.py ....
```
