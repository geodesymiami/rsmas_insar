### RSMAS InSAR code
The Miami INterferometric SAR software  (MinSAR) is an open-source python package for Interferometric Synthetic Aperture Radar time series analysis written at the Geodesy Lab of the University of Miami at the Rosenstiel School of Marine and Atmospheric Science (RSMAS). MinSAR uses the following packages for InSAR processing and time series analysis.

[ISCE](https://github.com/isce-framework/isce2), [MintPy](https://github.com/insarlab/MintPy), [PyAPS](https://github.com/yunjunz/pyaps3), [MiNoPy](https://github.com/geodesymiami/minopy)


The main Developers are Sara Mirzaee and Falk Amelung with contributions of many University of Miami graduate and undergraduate students.

### 1. [Installation](./installation.md) ###

### 2. Running MinSAR ###

MinSAR downloads a stack of SLCs, processes the interferograms and creates displacement timeseries products.

```
process_rsmas.py   $SAMPLESDIR/GalapagosSenDT128.template   #run with default and custom templates    

# Run with --start/stop/dostep options
```

#### [Example](.) for Galápagos with Sentinel-1 data ####
`
