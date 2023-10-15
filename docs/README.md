## RSMAS InSAR code

The Miami INterferometric SAR software  (MinSAR) is an open-source python package for Interferometric Synthetic Aperture Radar processing and time series analysis written at the Geodesy Lab of the University of Miami at the Rosenstiel School of Marine and Atmospheric Science (RSMAS). MinSAR uses the following packages:

[ISCE](https://github.com/isce-framework/isce2), [MintPy](https://github.com/insarlab/MintPy), [PyAPS](https://github.com/yunjunz/pyaps3), [MiNoPy](https://github.com/geodesymiami/miaplpy)

The main Developers are Sara Mirzaee and Falk Amelung with contributions of many University of Miami graduate and undergraduate students.

## 1. [Installation](./installation.md) ###

## 2. Running MinSAR ###

MinSAR downloads a stack of SLC images, downloads a DEM, processes the interferograms and creates displacement timeseries products using MintPy and/or MiaplPy. Optional steps are the ingestion into our [dataportal] (https//:insarmaps.miami.edu) and the upload of the data products to our jetstream server.

The processing is controlled by a *.template file which offers many different options for each processing step ([see example])(../samples/unittestGalapagosSenDT128.template). The processing is executed by `minsarApp.bash`. The processing steps are specified on the command line. Steps:
```
download:   downloading data     (by executing the command in 
dem:        downloading DEM
jobfiles:   create runfiles and jobfiles
ifgram:     processing interferograms starting with unpacking of the images
mintpy:     time series analysis based on smallbaseline method or single master interferograms (MintPy) (see Yunjun et al., 2019(
insarmaps:  uploading displacement products to insarmaps website
miaplpy:    time series analysis of persistent and distributed scatterers  (see Mirzaee et al., 2023)
upload:     upload data products to jetstream server
```

The entire workflow including `insarmaps` is run by specifying the *template file (see note below for the unittestGalapagosSenDT128.template example):
```
  minsarApp.bash  $SAMPLESDIR/unittestGalapagosSenDT128.template             # run with default and custom templates
  minsarApp.bash  -h / --help                      # help 
```
The default is to run the `mintpy` step. The `--mintpy --miaplpy` option runs both, MintPy and MiaplPy.

Processing can be started at a given step using the `--start` option and stopped using `--stop` option. The `--dostep` option execute only one processing step. Examples:

  minsarApp.bash $SAMPLESDIR/unittestGalapagosSenDT128.template --dostep  download     
  minsarApp.bash $SAMPLESDIR/unittestGalapagosSenDT128.template --dostep  dem          
  minsarApp.bash $SAMPLESDIR/unittestGalapagosSenDT128.template --dostep  jobfiles
  minsarApp.bash $SAMPLESDIR/unittestGalapagosSenDT128.template --dostep  ifgram
  minsarApp.bash $SAMPLESDIR/unittestGalapagosSenDT128.template --dostep  mintpy
  (minsarApp.bash $SAMPLESDIR/unittestGalapagosSenDT128.template --dostep  insarmaps   # currently switched off because of disk space limitations)
  (minsarApp.bash $SAMPLESDIR/unittestGalapagosSenDT128.template --dostep  upload      # currently switched off)
  minsarApp.bash $SAMPLESDIR/unittestGalapagosSenDT128.template --dostep  miaplpy        
```
In order to use either `--start` or `--dostep`, it is necessary that the previous step was completed.

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
