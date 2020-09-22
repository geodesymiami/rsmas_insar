###  Known issues with data
* Data unpacking problems
run_02_unpack_secondary_slc (Sentinel1_TOPS) may fail because of issues with the data. `check_job_outputs.py` raises an exception when one of the following strings is found:

```
`There appears to be a gap between slices. Cannot stitch them successfully`
`no element found: line`
`Trying to combine SLC products from different IPF versions`
`Exiting .......`
```

Currently  you need to add problem scenes into `topsStack.excludeDates`.  In principle we could remove the offending dates from the run_files, but this hasnot been implemented.


* Other potential errors for which excpetions are raised
```
                   'Segmentation fault',
                    'Bus',
                    'Aborted',
                    'ERROR',
                    'Error',
                    'FileNotFoundError',
                    'IOErr',
                    'Traceback'
```


###  Other known issues
* MintPy may have a problem with weather data download and you might see the message below. This could happen because you don't have your ECMWF credentials (`model.cfg`) installed.

```
INFO: You are using the latest ECMWF platform for downloading datasets: https://cds.climate.copernicus.eu/api/v2
Downloading 1 of 7: /work/05861/tg851601/stampede2/insarlab/WEATHER/ERA5/ERA5_20160605_12.grb 
{'product_type': 'reanalysis', 'format': 'grib', 'variable': ['geopotential', 'temperature', 'specific_humidity'], 'pressure_level': ['1', '2', '3', '5', '7', '10', '20', '30', '50', '70', '100', '125', '150', '175', '200', '225', '250', '300', '350', '400', '450', '500', '550', '600', '650', '700', '750', '775', '800', '825', '850', '875', '900', '925', '950', '975', '1000'], 'year': '2016', 'month': '06', 'day': '05', 'time': '12:00'}
2020-09-22 10:55:51,341 INFO Welcome to the CDS
2020-09-22 10:55:51,341 INFO Sending request to https://cds.climate.copernicus.eu/api/v2/resources/reanalysis-era5-pressure-levels
2020-09-22 10:55:52,674 INFO Request is completed
2020-09-22 10:55:52,674 INFO Downloading http://136.156.133.25/cache-compute-0008/cache/data3/adaptor.mars.internal-1600790135.4841793-2268-9-2b4e38b2-fccb-409c-9397-492b07f5d283.grib to /work/05861/tg851601/stampede2/insarlab/WEATHER/ERA5/ERA5_20160605_12.grb (219.8M)
                                                                                                                                                                                   
**************************************************
WARNING: downloading failed for 3 times, stop trying and continue.
**************************************************
```
