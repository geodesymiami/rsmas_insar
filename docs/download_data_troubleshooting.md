### Troubleshooting downloading data 

There are occasional errors with data download. The most coomon is that the NASA URS authentication is down. If that happens you get a *zip file of  short length (1568 bytes) that tells you that there was an authenticatin problem.

If download does not work run `download_ssara.py` and `download_asfserial.py` independently.  `download_asfserial.py` is more reliable but much slower (is it serial).  I don't understand why it is more reliable. 

See this issue for suggested imporvements:
https://github.com/geodesymiami/rsmas_insar/issues/244
