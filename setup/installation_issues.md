The installation should work smoothly.  The following problems have been observed:
* Your conda environment was not properly installed. It appears that `conda install` not always raises exceptions when there are download errors. Check your conda environment with the listings below. In China some channels are slow and you may want to use the tsinghua mirror (commented out lines in install_miniconda.csh). Did you use the proper channels for conda install? The channels should be taken care of by the .condarc but this has not been properly looked at.

* A problem occurrs at runtime using PBS. A typical explanation is that you don't have the same libraries on the compute nodes then on the head node (which is used for calcualtions). First run commands (without scheduler) on the head node and then try the same on a compute node (e.g. ssh node4). 

```
//login4/nethome/famelung/test/test4/rsmas_insar[15] conda list | wc -l
311
//login4/nethome/famelung/test/test4/rsmas_insar[16] pip list | wc -l
203
```

If there are diffences go into the weeds to see what did not work:

* Here my conda environment (`conda list`)

```
# packages in environment at /nethome/famelung/test/test3/rsmas_insar/3rdparty/miniconda3:
#
# Name                    Version                   Build  Channel
_ipyw_jlab_nb_ext_conf    0.1.0            py36he11e457_0  
alabaster                 0.7.10           py36h306e16b_0  
anaconda-client           1.6.14                   py36_0  
anaconda-navigator        1.8.7                    py36_0  
anaconda-project          0.8.2            py36h44fb852_0  
asn1crypto                0.24.0                   py36_0    conda-forge
astroid                   1.6.3                    py36_0    conda-forge
astropy                   3.0.2            py36h3010b51_1  
attrs                     18.1.0                   py36_0  
babel                     2.5.3                    py36_0    conda-forge
backcall                  0.1.0                    py36_0  
backports                 1.0              py36hfa02d7e_1  
backports.shutil_get_terminal_size 1.0.0            py36hfea85ff_2  
basemap                   1.2.0            py36h705c2d8_0  
beautifulsoup4            4.6.0            py36h49b8c8c_1  
bitarray                  0.8.1            py36h14c3975_1  
bkcharts                  0.2              py36h735825a_0  
blas                      1.0                         mkl  
blaze                     0.11.3           py36h4e06776_0  
bleach                    2.1.3                    py36_0  
blosc                     1.14.3               hdbcaa40_0  
bokeh                     0.12.16                  py36_0    conda-forge
boto                      2.48.0           py36h6e4cd66_1  
bottleneck                1.2.1            py36haac1ea0_0  
bzip2                     1.0.6                h14c3975_5  
ca-certificates           2019.3.9             hecc5488_0    conda-forge
cairo                     1.14.12              h7636065_2  
certifi                   2019.3.9                 py36_0    conda-forge
cffi                      1.11.5           py36h9745a5d_0  
cftime                    1.0.1            py36h7eb728f_0    conda-forge
chardet                   3.0.4            py36h0f667ec_1  
click                     6.7              py36h5253387_0  
cloog                     0.18.0                        0  
cloudpickle               0.5.3                    py36_0  
clyent                    1.2.2            py36h7e57e65_1  
colorama                  0.3.9            py36h489cec4_0  
conda                     4.6.11                   py36_0    conda-forge
conda-build               3.10.5                   py36_0    conda-forge
conda-env                 2.6.0                h36134e3_1  
conda-verify              2.0.0            py36h98955d8_0  
configobj                 5.0.6                      py_0    conda-forge
contextlib2               0.5.5            py36h6c84a62_0  
cryptography              2.2.2            py36h14c3975_0  
curl                      7.60.0               h84994c4_0  
cvxopt                    1.1.8                    py36_0    omnia
cycler                    0.10.0           py36h93f1223_0  
cython                    0.28.2           py36h14c3975_0  
cytoolz                   0.9.0.1          py36h14c3975_0  
dask                      0.17.5                   py36_0  
dask-core                 0.17.5                   py36_0  
datashape                 0.5.4            py36h3ad6b5c_0  
dbus                      1.13.2               h714fa37_1  
decorator                 4.3.0                    py36_0  
distributed               1.21.8                   py36_0    conda-forge
docutils                  0.14             py36hb0f60f5_0  
ecmwf_grib                1.28.0            h0cee55e_1000    conda-forge
entrypoints               0.2.3            py36h1aec115_2  
et_xmlfile                1.0.1            py36hd6bccc3_0  
expat                     2.2.5                he0dffb1_0  
fastcache                 1.0.2            py36h14c3975_2  
fftw3f                    3.3.4                         2    omnia
filelock                  3.0.4                    py36_0    conda-forge
flask                     1.0.2                    py36_1  
flask-cors                3.0.4                    py36_0  
fontconfig                2.12.6               h49f89f6_0  
freetype                  2.8                  hab7d2ae_1  
freexl                    1.0.5                h14c3975_0  
gcc-5                     5.2.0                         1    psi4
gdal                      2.2.2            py36hc209d97_1  
geocoder                  1.38.1                     py_0    conda-forge
geos                      3.6.2                heeff764_2  
get_terminal_size         1.0.0                haa9412d_0  
gettext                   0.19.8.1             h5e8e0c9_1    conda-forge
gevent                    1.3.0            py36h14c3975_0  
giflib                    5.1.4                h14c3975_1  
git                       2.18.0          pl526hbb17d3c_1    conda-forge
glib                      2.56.1               h000015b_0  
glob2                     0.6              py36he249c77_0  
gmp                       6.1.2                h6c8ec71_1  
gmpy2                     2.0.8            py36hc8893dd_2  
graphite2                 1.3.11               h16798f4_2  
greenlet                  0.4.13           py36h14c3975_0  
gst-plugins-base          1.14.0               hbbd80ab_1  
gstreamer                 1.14.0               hb453b48_1  
h5py                      2.8.0            py36h7eb728f_3    conda-forge
harfbuzz                  1.7.6                h5f0a787_1  
hdf4                      4.2.13               h3ca952b_2  
hdf5                      1.10.2               hba1933b_1  
heapdict                  1.0.0                    py36_2  
html5lib                  1.0.1            py36h2f9c1c0_0  
hub                       2.6.0                h470a237_0    conda-forge
icu                       58.2                 h9c2bf20_1  
idna                      2.6              py36h82fb2a8_1  
imageio                   2.3.0                    py36_0    conda-forge
imagesize                 1.0.0                    py36_0    conda-forge
intel-openmp              2018.0.0                      8  
ipykernel                 4.8.2                    py36_0    conda-forge
ipython                   6.4.0                    py36_0    conda-forge
ipython_genutils          0.2.0            py36hb52b0d5_0  
ipywidgets                7.2.1                    py36_0    conda-forge
isl                       0.12.2                        0  
isort                     4.3.4                    py36_0    conda-forge
itsdangerous              0.24             py36h93cc618_1  
jasper                    1.900.1                       4    conda-forge
jbig                      2.1                  hdba287a_0  
jdcal                     1.4                      py36_0    conda-forge
jedi                      0.12.0                   py36_1  
jinja2                    2.10             py36ha16c418_0  
joblib                    0.12.5                     py_0    conda-forge
jpeg                      9b                   h024ee3a_2  
json-c                    0.13.1               h1bed415_0  
jsonschema                2.6.0            py36h006f8b5_0  
jupyter                   1.0.0                    py36_4  
jupyter_client            5.2.3                    py36_0    conda-forge
jupyter_console           5.2.0            py36he59e554_1  
jupyter_core              4.4.0            py36h7c827e3_0  
jupyterlab                0.32.1                   py36_0    conda-forge
jupyterlab_launcher       0.10.5                   py36_0    conda-forge
kealib                    1.4.7                h77bc034_6  
kiwisolver                1.0.1            py36h764f252_0  
krb5                      1.16.1               hc83ff2d_6  
lazy-object-proxy         1.3.1            py36h10fcdad_0  
libboost                  1.67.0               h46d08c1_4  
libcurl                   7.60.0               h1ad7b7a_0  
libdap4                   3.19.1               h6ec2957_0  
libedit                   3.1.20170329         h6b74fdf_2  
libffi                    3.2.1                hd88cf55_4  
libgcc                    7.2.0                h69d50b8_2    conda-forge
libgcc-ng                 7.3.0                hdf63c60_0  
libgdal                   2.2.4                h6f639c0_1  
libgfortran               3.0.0                         1    conda-forge
libgfortran-ng            7.2.0                hdf63c60_3  
libiconv                  1.15                 h470a237_3    conda-forge
libkml                    1.3.0                h590aaf7_4  
libnetcdf                 4.6.1                h13459d8_0  
libpng                    1.6.34               hb9fc6fc_0  
libpq                     10.5                 h1ad7b7a_0  
libsodium                 1.0.16               h1bed415_0  
libspatialite             4.3.0a              he475c7f_19  
libssh2                   1.8.0                h9cfc8f7_4  
libstdcxx-ng              7.3.0                hdf63c60_0  
libtiff                   4.0.9                he85c1e1_1  
libtool                   2.4.6                h544aabb_3  
libuuid                   1.0.3                h1bed415_2  
libxcb                    1.13                 h1bed415_1  
libxml2                   2.9.8                h26e45fe_1  
libxslt                   1.1.32               h1312cb7_0  
llvm-meta                 6.0.1                         0    conda-forge
llvmlite                  0.23.1           py36hdbcaa40_0  
locket                    0.2.0            py36h787c0ad_1  
lxml                      4.2.5            py36hc9114bc_0    conda-forge
lzo                       2.10                 h49e0be7_2  
markupsafe                1.0              py36hd9260cd_1  
matplotlib                2.2.2            py36h0e671d2_1  
mccabe                    0.6.1            py36h5ad9710_1  
mistune                   0.8.3            py36h14c3975_1  
mkl                       2018.0.2                      1  
mkl-service               1.1.2            py36h17a0993_4  
mkl_fft                   1.0.1            py36h3010b51_0  
mkl_random                1.0.1            py36h629b387_0  
more-itertools            4.1.0                    py36_0  
mpc                       1.0.3                hec55b23_5  
mpfr                      3.1.5                h11a74b3_2  
mpmath                    1.0.0            py36hfeacd6b_2  
msgpack-python            0.5.6            py36h6bb024c_0  
multipledispatch          0.5.0                    py36_0    conda-forge
navigator-updater         0.2.1                    py36_0  
nbconvert                 5.3.1            py36hb41ffb7_0  
nbformat                  4.4.0            py36h31c9010_0  
ncurses                   6.1                  hf484d3e_0  
netcdf4                   1.4.1            py36h62672b6_0    conda-forge
networkx                  2.1                      py36_0    conda-forge
nltk                      3.3.0                    py36_0  
nose                      1.3.7            py36hcdf7029_2  
notebook                  5.5.0                    py36_0    conda-forge
numba                     0.38.0           py36h637b7d7_0  
numexpr                   2.6.5            py36h7bf3b9c_0  
numpy                     1.14.3           py36hcd700cb_1  
numpy-base                1.14.3           py36h9be14a7_1  
numpydoc                  0.8.0                    py36_0    conda-forge
odo                       0.5.1            py36h90ed295_0  
olefile                   0.45.1                   py36_0    conda-forge
openblas                  0.3.5             h9ac9557_1001    conda-forge
opencv-python             4.0.1.24                 pypi_0    pypi
openjpeg                  2.3.0                h05c96fa_1  
openmp                    6.0.1                h2d50403_0    conda-forge
openpyxl                  2.5.3                    py36_0    conda-forge
openssl                   1.0.2r               h14c3975_0    conda-forge
orderedset                2.0                      py36_0    conda-forge
packaging                 17.1                     py36_0  
pandas                    0.23.0           py36h637b7d7_0  
pandoc                    1.19.2.1             hea2e7c5_1  
pandocfilters             1.4.2            py36ha6701b7_1  
pango                     1.41.0               hd475d92_0  
parso                     0.2.0                    py36_0  
partd                     0.3.8            py36h36fd896_0  
patchelf                  0.9                  hf79760b_2  
path.py                   11.0.1                   py36_0  
pathlib2                  2.3.2                    py36_0    conda-forge
patsy                     0.5.0                    py36_0    conda-forge
pcre                      8.42                 h439df22_0  
pep8                      1.7.1                    py36_0  
perl                      5.26.2               h470a237_0    conda-forge
pexpect                   4.5.0                    py36_0    conda-forge
pickleshare               0.7.4            py36h63277f8_0  
pillow                    5.1.0            py36h3deb7b8_0  
pip                       19.0.3                   py36_0    conda-forge
pixman                    0.34.0               hceecf20_3  
pkginfo                   1.4.2                    py36_1  
pluggy                    0.6.0            py36hb689045_0  
ply                       3.11                     py36_0    conda-forge
poppler                   0.65.0               ha54bb34_0  
poppler-data              0.4.9                         0    conda-forge
proj4                     5.0.1                h14c3975_0  
prompt_toolkit            1.0.15           py36h17d85b1_0  
psutil                    5.4.5            py36h14c3975_0  
psycopg2                  2.7.5            py36hdffb7b8_2    conda-forge
ptyprocess                0.5.2            py36h69acd42_0  
py                        1.5.3                    py36_0  
pycodestyle               2.4.0                    py36_0    conda-forge
pycosat                   0.6.3            py36h0a5515d_0  
pycparser                 2.18             py36hf9f622e_1  
pycrypto                  2.6.1            py36h14c3975_8  
pycurl                    7.43.0.1         py36hb7f436b_0  
pyflakes                  1.6.0            py36h7bd6a15_0  
pygments                  2.2.0            py36h0d3125c_0  
pygrib                    2.0.2            py36he706d3e_4    conda-forge
pyhdf                     0.9.10           py36he2eb8c5_0    conda-forge
pykdtree                  1.3.1            py36h7eb728f_2    conda-forge
pykml                     0.1.4                    pypi_0    pypi
pylint                    1.8.4                    py36_0    conda-forge
pyodbc                    4.0.23           py36hf484d3e_0  
pyopenssl                 18.0.0                   py36_0    conda-forge
pyparsing                 2.2.0            py36hee85983_1  
pyproj                    1.9.5.1                  py36_0  
pyqt                      5.9.2            py36h751905a_0  
pyresample                1.10.2           py36hf8a1672_0    conda-forge
pyshp                     1.2.12                     py_0    conda-forge
pysocks                   1.6.8                    py36_0  
pytables                  3.4.3            py36h02b9ad4_2  
pytest                    3.5.1                    py36_0    conda-forge
pytest-arraydiff          0.2                      py36_0  
pytest-astropy            0.3.0                    py36_0  
pytest-doctestplus        0.1.3                    py36_0  
pytest-openfiles          0.3.0                    py36_0  
pytest-remotedata         0.2.1                    py36_0  
python                    3.6.5                hc3d631a_2  
python-dateutil           2.7.3                    py36_0  
pytz                      2018.4                   py36_0  
pywavelets                0.5.2            py36he602eb0_0  
pyyaml                    3.12             py36hafb9ca4_1  
pyzmq                     17.0.0           py36h14c3975_0  
qt                        5.9.5                h7e424d6_0  
qtawesome                 0.4.4            py36h609ed8c_0  
qtconsole                 4.3.1            py36h8f73b5b_0  
qtpy                      1.4.1                    py36_0  
ratelim                   0.1.6                    py36_0    conda-forge
readline                  7.0                  ha6073c6_4  
requests                  2.18.4           py36he2e5f8d_1  
rope                      0.10.7           py36h147e2ec_0  
ruamel_yaml               0.15.35          py36h14c3975_1  
scikit-image              0.13.1           py36h14c3975_1  
scikit-learn              0.19.1           py36h7aa7ec6_0  
scipy                     1.1.0            py36hfc37229_0  
scons                     3.0.1                    py36_1    conda-forge
seaborn                   0.8.1            py36hfad7ec4_0  
send2trash                1.5.0                    py36_0  
setuptools                39.1.0                   py36_0    conda-forge
simplegeneric             0.8.1                    py36_2  
singledispatch            3.4.0.3          py36h7a266c3_0  
sip                       4.19.8           py36hf484d3e_0  
six                       1.11.0           py36h372c433_1  
snappy                    1.1.7                hbae5bb6_3  
snowballstemmer           1.2.1            py36h6febd40_0  
sortedcollections         0.6.1                    py36_0    conda-forge
sortedcontainers          1.5.10                   py36_0    conda-forge
sphinx                    1.7.4                    py36_0    conda-forge
sphinxcontrib             1.0              py36h6d0f590_1  
sphinxcontrib-websupport  1.0.1            py36hb5cb234_1  
spyder                    3.2.8                    py36_0    conda-forge
sqlalchemy                1.2.7            py36h6b74fdf_0  
sqlite                    3.24.0               h84994c4_0  
statsmodels               0.9.0            py36h3010b51_0  
sympy                     1.1.1            py36hc6d1c1c_0  
tblib                     1.3.2            py36h34cf8b6_0  
terminado                 0.8.1                    py36_1    conda-forge
testpath                  0.3.1            py36h8cadb63_0  
tk                        8.6.7                hc745277_3  
toolz                     0.9.0                    py36_0  
tornado                   5.0.2                    py36_0    conda-forge
traitlets                 4.3.2            py36h674d592_0  
typing                    3.6.4                    py36_0    conda-forge
unicodecsv                0.14.1           py36ha668878_0  
unixodbc                  2.3.6                h1bed415_0  
urllib3                   1.22             py36hbe7ace6_0  
wcwidth                   0.1.7            py36hdf4376a_0  
webencodings              0.5.1            py36h800622e_1  
werkzeug                  0.14.1                   py36_0  
wheel                     0.31.1                   py36_0    conda-forge
widgetsnbextension        3.2.1                    py36_0    conda-forge
wrapt                     1.10.11          py36h28b7045_0  
xerces-c                  3.2.1                hac72e42_0  
xlrd                      1.1.0            py36h1db9f0c_1  
xlsxwriter                1.0.4                    py36_0  
xlwt                      1.3.0            py36h7b00a1f_0  
xz                        5.2.4                h14c3975_4  
yaml                      0.1.7                had09818_2  
zeromq                    4.2.5                h439df22_0  
zict                      0.1.3            py36h3a3bf81_0  
zlib                      1.2.11               ha838bed_2  
```

* Here the pip  (`pip freeze`)
```
alabaster==0.7.10
anaconda-client==1.6.14
anaconda-navigator==1.8.7
anaconda-project==0.8.2
asn1crypto==0.24.0
astroid==1.6.3
astropy==3.0.2
attrs==18.1.0
Babel==2.5.3
backcall==0.1.0
backports.shutil-get-terminal-size==1.0.0
basemap==1.2.0
beautifulsoup4==4.6.0
bitarray==0.8.1
bkcharts==0.2
blaze==0.11.3
bleach==2.1.3
bokeh==0.12.16
boto==2.48.0
Bottleneck==1.2.1
certifi==2019.3.9
cffi==1.11.5
cftime==1.0.1
chardet==3.0.4
click==6.7
cloudpickle==0.5.3
clyent==1.2.2
colorama==0.3.9
conda==4.6.11
conda-build==3.10.5
conda-verify==2.0.0
configobj==5.0.6
contextlib2==0.5.5
cryptography==2.2.2
cvxopt==1.1.8
cycler==0.10.0
Cython==0.28.2
cytoolz==0.9.0.1
dask==0.17.5
datashape==0.5.4
decorator==4.3.0
distributed==1.21.8
docutils==0.14
entrypoints==0.2.3
et-xmlfile==1.0.1
fastcache==1.0.2
filelock==3.0.4
Flask==1.0.2
Flask-Cors==3.0.4
GDAL==2.2.2
geocoder==1.38.1
gevent==1.3.0
glob2==0.6
gmpy2==2.0.8
greenlet==0.4.13
h5py==2.8.0
heapdict==1.0.0
html5lib==1.0.1
idna==2.6
imageio==2.3.0
imagesize==1.0.0
ipykernel==4.8.2
ipython==6.4.0
ipython-genutils==0.2.0
ipywidgets==7.2.1
isort==4.3.4
itsdangerous==0.24
jdcal==1.4
jedi==0.12.0
Jinja2==2.10
joblib==0.12.5
jsonschema==2.6.0
jupyter==1.0.0
jupyter-client==5.2.3
jupyter-console==5.2.0
jupyter-core==4.4.0
jupyterlab==0.32.1
jupyterlab-launcher==0.10.5
kiwisolver==1.0.1
lazy-object-proxy==1.3.1
llvmlite==0.23.1
locket==0.2.0
lxml==4.2.5
MarkupSafe==1.0
matplotlib==2.2.2
mccabe==0.6.1
mistune==0.8.3
mkl-fft==1.0.0
mkl-random==1.0.1
more-itertools==4.1.0
mpmath==1.0.0
msgpack-python==0.5.6
multipledispatch==0.5.0
navigator-updater==0.2.1
nbconvert==5.3.1
nbformat==4.4.0
netCDF4==1.4.1
networkx==2.1
nltk==3.3
nose==1.3.7
notebook==5.5.0
numba==0.38.0
numexpr==2.6.5
numpy==1.14.3
numpydoc==0.8.0
odo==0.5.1
olefile==0.45.1
opencv-python==4.0.1.24
openpyxl==2.5.3
orderedset==2.0
packaging==17.1
pandas==0.23.0
pandocfilters==1.4.2
parso==0.2.0
partd==0.3.8
path.py==11.0.1
pathlib2==2.3.2
patsy==0.5.0
pep8==1.7.1
pexpect==4.5.0
pickleshare==0.7.4
Pillow==5.1.0
pkginfo==1.4.2
pluggy==0.6.0
ply==3.11
prompt-toolkit==1.0.15
psutil==5.4.5
psycopg2==2.7.5
ptyprocess==0.5.2
py==1.5.3
pycodestyle==2.4.0
pycosat==0.6.3
pycparser==2.18
pycrypto==2.6.1
pycurl==7.43.0.1
pyflakes==1.6.0
Pygments==2.2.0
pygrib==2.0.2
pyhdf==0.9.0
pykdtree==1.3.1
pykml==0.1.4
pylint==1.8.4
pyodbc==4.0.23
pyOpenSSL==18.0.0
pyparsing==2.2.0
pyproj==1.9.5.1
pyresample==1.10.2
pyshp==1.2.12
PySocks==1.6.8
pytest==3.5.1
pytest-arraydiff==0.2
pytest-astropy==0.3.0
pytest-doctestplus==0.1.3
pytest-openfiles==0.3.0
pytest-remotedata==0.2.1
python-dateutil==2.7.3
pytz==2018.4
PyWavelets==0.5.2
PyYAML==3.12
pyzmq==17.0.0
QtAwesome==0.4.4
qtconsole==4.3.1
QtPy==1.4.1
ratelim==0.1.6
requests==2.18.4
rope==0.10.7
ruamel-yaml==0.15.35
scikit-image==0.13.1
scikit-learn==0.19.1
scipy==1.1.0
scons==3.0.1
seaborn==0.8.1
Send2Trash==1.5.0
simplegeneric==0.8.1
singledispatch==3.4.0.3
six==1.11.0
snowballstemmer==1.2.1
sortedcollections==0.6.1
sortedcontainers==1.5.10
Sphinx==1.7.4
sphinxcontrib-websupport==1.0.1
spyder==3.2.8
SQLAlchemy==1.2.7
statsmodels==0.9.0
sympy==1.1.1
tables==3.4.3
tblib==1.3.2
terminado==0.8.1
testpath==0.3.1
toolz==0.9.0
tornado==5.0.2
traitlets==4.3.2
typing==3.6.4
unicodecsv==0.14.1
urllib3==1.22
wcwidth==0.1.7
webencodings==0.5.1
Werkzeug==0.14.1
widgetsnbextension==3.2.1
wrapt==1.10.11
xlrd==1.1.0
XlsxWriter==1.0.4
xlwt==1.3.0
zict==0.1.3
```

