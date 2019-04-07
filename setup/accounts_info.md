The accounts directory contains 

```
model.cfg
netrc
password_config.py
```

 `model.cfg` is required for downloading data from ECMWF, netrc (to be copied into your `~/.netrc`) allows DEM download from the USGS and `password_config.py` is used by `ssara_federated_query.py` and contains your credentials to download data from the ASF and WinSAR.  The ASF credentials are generic and are only used to track who downloaded granules from NASA servers (ASF data are open access).  You get your WinSAR credentials from Unavco. `download_isce.py` also uses the WInSAR crednetials to download ths ISCE software from Unavco.
