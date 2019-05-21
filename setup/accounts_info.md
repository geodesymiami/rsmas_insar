The accounts directory contains 

```
model.cfg
netrc
password_config.py
```

 `model.cfg` is required for downloading data from ECMWF, `netrc` (to be copied into your `~/.netrc`) allows DEM download from the USGS and `password_config.py` is used by `ssara_federated_query.py` and contains your credentials to download data from the ASF and WinSAR.  The ASF credentials are generic and are only used to track who downloaded granules from NASA servers (ASF data are open access).  You get your WinSAR credentials from Unavco. These files will be copied by `install_credentials.py` to their respective locations.
 
 
 model.cfg:
 ```
 #The key to the new server for ECMWF
##Get it from https://software.ecmwf.int/wiki/display/WEBAPI/Accessing+ECMWF+data+servers+in+batch 
[ECMWF]
email = [you@youremail.com]
key = [a5c4ee9...] 

#####Passwd and key for download from ecmwf.int. Old version.
[ECMWF_old]
email = [you@youremail.com]
key = [a5c4ee9...]

#####Passwd and key for download from ucar
[ERA]
email = [you@youremail.com]
key = [...]

[NARR]


[MERRA]
```
netrc: 
```
machine urs.earthdata.nasa.gov
        login [your login]
        password [...]
```

password_config.py (can contain additional passwords):
```
#For data download using SSARA
unavuser="..."
unavpass="..."

asfuser="..."
asfpass="..."

eossouser="..."
eossopass="..."

```
