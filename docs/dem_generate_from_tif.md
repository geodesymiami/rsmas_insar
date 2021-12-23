example:

```
tif_file='FL_Miami_Dade_DEM_2018_9272.tif'

gdalwarp -of ISCE -dstnodata 0 -te  -80.15 25.755 -80.115 25.9  -te_srs EPSG:4326 ${tif_file} dem.wgs84

rm dem.wgs84

gdalwarp -of ENVI -dstnodata 0 -te  -80.15 25.755 -80.115 25.9   -te_srs EPSG:4326 ${tif_file} dem.wgs84

gdal_translate -of vrt dem.wgs84 dem.wgs84.vrt

fixImageXml.py -f -i dem.wgs84
```
