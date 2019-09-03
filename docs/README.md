### RSMAS InSAR code
The Miami INterferometric SAR software  (MinSAR) is an open-source python package for Interferometric Synthetic Aperture Radar processing and time series analysis written at the Geodesy Lab of the University of Miami at the Rosenstiel School of Marine and Atmospheric Science (RSMAS). MinSAR uses the following packages:

[ISCE](https://github.com/isce-framework/isce2), [MintPy](https://github.com/insarlab/MintPy), [PyAPS](https://github.com/yunjunz/pyaps3), [MiNoPy](https://github.com/geodesymiami/minopy)


The main Developers are Sara Mirzaee and Falk Amelung with contributions of many University of Miami graduate and undergraduate students.


### 1. [Installation](./installation.md) ###

### 2. [Set-up in Miami](./set_up_miami.md) ###

### 3. Running MinSAR ###

MinSAR downloads a stack of SLC images, downloads a DEM, processes the interferograms and creates displacement timeseries products. Optional steps are the ingestion into our [dataportal](https//:insarmaps.miami.edu) and the generation of image products that will soon be made available from another data portal.

The processing is controlled by a template file which offers many different options for each processing step [see example](..samples/GalapagosSenDT128.template). The processing is executed using `process_rsmas.py` with the processing steps specified on the command line:
```
Steps: 
download:   downloading data
dem:        downloading DEM
ifgrams:    processing interferograms starting with unpacking of the images
timeseries: time series analysis based on smallbaseline method or single master interferograms (MintPy or MiNoPy)
insarmaps:  uploading displacement products to insarmaps website
image_products: generating and uploading image products to hazards website (amplitudes, interferograms, coherences)
```
Processing can be started at a given step using the `--start` option. The `--step`  option allows to execute only one processing step. 

Example: 
```bash
  process_rsmas.py  $SAMPLESDIR/GalapagosSenDT128.template             # run with default and custom templates
  process_rsmas.py  $SAMPLESDIR/GalapagosSenDT128.template  --submit   # submit as job
  process_rsmas.py  -h / --help                      # help 
  process_rsmas.py -H                                # print    default template options

# Run with --start/stop/step options
  process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --step  download        # run the step 'download' only
  process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --start download        # start from the step 'download' 
  process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --stop  ifgrams         # end after step 'interferogram'
```
In order to use either `--start` or `--step`, it is necessary that the previous step was completed.

### 4. Example for Galápagos with Sentinel-1 data ####
The individual processing steps can be run stepwise using
```bash
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --step  download
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --step  dem
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --step  ifgrams
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --step  timeseries
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --step  insarmaps
process_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template --step  image_products
```

This runs these scripts:
```
download_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template
dem_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template
create_runfiles.py $SAMPLESDIR/GalapagosSenDT128.template
execute_runfiles.py $SAMPLESDIR/GalapagosSenDT128.template
smallbaseline_wrapper.py $SAMPLESDIR/GalapagosSenDT128.template
minopy_wrapper.py $SAMPLESDIR/GalapagosSenDT128.template
ingest_insarmaps.py $SAMPLESDIR/GalapagosSenDT128.template
export_ortho_geo.py $SAMPLESDIR/GalapagosSenDT128.template
````
The different processing steps are recorded in `./log`.

### 5. Download data: --step download
text from wiki. How to properly arrange the different steps for readthedocs? 
* Trouble shooting (need this tep for each step)

### 6. Download DEM: --step dem
Downaloading DEM from the USGS
* Trouble shooting
### 7. Process interferograms: --step ifgrams

```
execute_run_files.py ....
```
