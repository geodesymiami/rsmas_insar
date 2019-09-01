## RSMAS InSAR
RSMAS InSAR  code
The Miami INterferometric SAR software  (MinSAR) is an open-source package for Interferometric Synthetic Aperture Radar time series analysis. It reads the stack of interferograms (coregistered and unwrapped) in [ISCE](https://github.com/isce-framework/isce2), GAMMA, [ARIA](https://github.com/aria-tools/ARIA-tools), [SNAP](http://step.esa.int/) or ROI_PAC format, and produces three dimensional (2D in space and 1D in time) ground surface displacement. It includes a routine time series analysis (`smallbaselineApp.py`) and some independent toolbox.

### 1. [Installation](./installation.md) ###

### 2. Running MintPy ###

MintPy reads a stack of interferograms (unwrapped interferograms, coherence, wrapped interferograms and connecting components from SNAPHU if available) and the geometry files (DEM, lookup table, etc.). You need to give the path to where the files are and MintPy takes care of the rest!

```bash
smallbaselineApp.py                         #run with default template 'smallbaselineApp.cfg'
smallbaselineApp.py <custom_template>       #run with default and custom templates
smallbaselineApp.py -h / --help             #help
smallbaselineApp.py -H                      #print    default template options
smallbaselineApp.py -g                      #generate default template if it does not exist
smallbaselineApp.py -g <custom_template>    #generate/update default template based on custom template

# Run with --start/stop/dostep options
smallbaselineApp.py GalapagosSenDT128.template --dostep velocity  #run at step 'velocity' only
smallbaselineApp.py GalapagosSenDT128.template --end load_data    #end after step 'load_data'
```

#### [Example](./example_dataset.md) on Fernandina volcano, Galápagos with Sentinel-1 data ####

```
wget https://zenodo.org/record/2748487/files/FernandinaSenDT128.tar.xz
tar -xvJf FernandinaSenDT128.tar.xz
cd FernandinaSenDT128/MintPy
smallbaselineApp.py ${MINTPY_HOME}/docs/examples/input_files/FernandinaSenDT128.txt
```

<p align="left">
  <img width="600" src="https://yunjunzhang.files.wordpress.com/2019/06/fernandinasendt128_poi.jpg">
</p>

Inside smallbaselineApp.py, it reads the unwrapped interferograms, references all of them to the same coherent pixel (reference point), calculates the phase closure and estimates the unwrapping errors (if it has been asked for), inverts the network of interferograms into time-series, calculates a parameter called "temporal coherence" which can be used to evaluate the quality of inversion, corrects local oscillator drift (for Envisat only), corrects stratified tropospheric delay (using pyaps or phase-elevation-ratio approach), removes phase ramps (if it has been asked for), corrects DEM error,... and finally estimates the velocity.

Check **./pic** folder for auto-generated figures. More details about this test data are in [here](./example_dataset.md).
