CC=gcc
CPP=cpp

.PHONY: FFTW ROIPAC TIFF GEOTIFF GDAL MDX GAMMA RSMAS GAMMA_LITEND PYSAR2INSARMAPS

all:
	make FFTW
	make ROIPAC
	make GETORB
	make RSMAS
	make HDF5
	make TIFF
	make GEOTIFF
	make GDAL
	make GAMMA
	make MDX
	make IMAGEMAGICK
	make INSARMAPS
	make PYKML
	#make PYAPS
FFTW:
	cd $(FFTWHOME2);	./configure --enable-float --enable-shared --enable-type-prefix --prefix=$(FFTW_LIB) CFLAGS="-O3 -fomit-frame-pointer -fno-schedule-insns -fstrict-aliasing -fPIC -mpreferred-stack-boundary=4";
	cd $(FFTWHOME2);	make
	cd $(FFTWHOME2);	make install
	cd $(FFTWHOME2);	cp -f fftw/*fftw*.h $(FFTW_INC_DIR)
	cd $(FFTWHOME2);	cp -f rfftw/*fftw*.h $(FFTW_INC_DIR)
	cd $(FFTWHOME);	./configure --enable-float --enable-shared --enable-type-prefix --prefix=$(FFTW_LIB) CFLAGS="-O3 -fomit-frame-pointer -fno-schedule-insns -fstrict-aliasing -fPIC -mpreferred-stack-boundary=4";
	cd $(FFTWHOME);	make
	cd $(FFTWHOME);	make install
	cd $(FFTW_LIB);	cp -f lib/*fftw* .

ROIPAC:
	cd $(ROIPACHOME);   chmod +x configure
	cd $(ROIPACHOME);  ./configure  LDFLAGS=-L$(FFTW_LIB_DIR) CPPFLAGS=-I$(FFTW_INC_DIR) --prefix=$(ROIPACHOME)
	cd $(ROIPACHOME);   make
	cd $(ROIPACHOME);   make install
	mkdir -p $(INT_BIN)
	cp $(ROIPACHOME)/bin/* $(INT_BIN)
	# the following installs an old version ast this version oflibroipac.a is needed for rect in codes_roi_pac_modified
	cd $(ROIPACHOME); cd ../../codes_roi_pacv3.0.1;  ./configure  LDFLAGS=-L$(FFTW_LIB_DIR) CPPFLAGS=-I$(FFTW_INC_DIR)   # installed without prefix option and without make install as only libroipac.a is used
	cd $(ROIPACHOME); cd ../../codes_roi_pacv3.0.1;   make

TIFF:
	cd $(TIFFHOME);	./configure	--prefix=$(TIFFHOME)
	cd $(TIFFHOME); make
	cd $(TIFFHOME); make install

GEOTIFF:
	cd $(GEOTIFFHOME);	./configure	--with-libtiff=$(TIFFHOME)	--prefix=$(GEOTIFFHOME)
	cd $(GEOTIFFHOME);	make
	cd $(GEOTIFFHOME);	make install

GDAL:
	## remove anaconda python from search path as there are library conflicts
	$(eval export QPATH=`echo $(PATH) | sed -e s\#$(PYTHON2DIR)/bin:\#\#g | sed -e s\#$(PYTHON3DIR)/bin:\#\#g`)
	cd $(GDALSOURCE);	./configure --prefix=$(GDALHOME) PATH=$(QPATH) 
	cd $(GDALSOURCE); make
	cd $(GDALSOURCE); make install
	## GDAL is needed for PYSAR2INSARMAPS because conda does not have the postgres driver FA 11/2016

MDX:
	cd $(MDXHOME); make -f Makemdx_gfortran

HDF5: 
	cd $(HDF5HOME);	./configure
	cd $(HDF5HOME); make
	cd $(HDF5HOME); make install

GAMMA: 
	mkdir -p $(PARENTDIR)/3rdparty/gamma
	tar xvfz $(PARENTDIR)/sources/roipac/install_gamma/GAMMA_SOFTWARE-20150702_MSP_ISP_DIFF.src.tar.gz -C $(PARENTDIR)/3rdparty/gamma
	cp $(PARENTDIR)/sources/roipac/install_gamma/makefile_static_pegasus $(GAMMA_HOME1)
	cp $(PARENTDIR)/sources/roipac/install_gamma/MSP/src/makefile_static_pegasus  $(GAMMA_HOME1)/MSP/src
	cp $(PARENTDIR)/sources/roipac/install_gamma/ISP/src/makefile_static_pegasus  $(GAMMA_HOME1)/ISP/src
	cp $(PARENTDIR)/sources/roipac/install_gamma/DISP/src/makefile_static_pegasus $(GAMMA_HOME1)/DISP/src
	cp $(PARENTDIR)/sources/roipac/install_gamma/DIFF/src/makefile_static_pegasus $(GAMMA_HOME1)/DIFF/src
	make -C $(GAMMA_HOME1) -f makefile_static_pegasus all; 
	ln -s $(GAMMA_HOME1) $(GAMMA_HOME1)_LITEND
	mkdir -p $(GAMMA_HOME1)/BIN
	mv $(GAMMA_HOME1)/MSP/bin/*  $(GAMMA_HOME1)/BIN
	mv $(GAMMA_HOME1)/ISP/bin/*  $(GAMMA_HOME1)/BIN
	mv $(GAMMA_HOME1)/DISP/bin/* $(GAMMA_HOME1)/BIN
	mv $(GAMMA_HOME1)/DIFF/bin/* $(GAMMA_HOME1)/BIN
	make GAMMA_LITEND
	make GAMMA_BIGEND
	make GAMMA_BINARY
GAMMA_LITEND: 
	mkdir -p $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND
	mkdir -p $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/BIN
	tar xvfz $(PARENTDIR)/sources/roipac/install_gamma/GAMMA_SOFTWARE-20160625_MSP_ISP_DIFF_LAT.src.tar.gz -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND
	mv    $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/GAMMA_SOFTWARE-20160625/* $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND
	rm -r $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/GAMMA_SOFTWARE-20160625
	cp $(PARENTDIR)/sources/roipac/install_gamma/MSP_makefile_static_pegasus_20160625  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/MSP/src/makefile_static_pegasus
	cp $(PARENTDIR)/sources/roipac/install_gamma/ISP_makefile_static_pegasus_20160625  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/ISP/src/makefile_static_pegasus
	cp $(PARENTDIR)/sources/roipac/install_gamma/DISP_makefile_static_pegasus_20160625 $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/DISP/src/makefile_static_pegasus
	cp $(PARENTDIR)/sources/roipac/install_gamma/DIFF_makefile_static_pegasus_20160625 $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/DIFF/src/makefile_static_pegasus
	make -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/DISP/src CPPFLAGS="-DFFTW -DSFFTW -DCPU_LITTLE_END -DLITTLE_END -msse2 -mfpmath=sse -mtune=generic -fopenmp" LD_LIB_FLAGS="-shared" -f makefile_static_pegasus
	make -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/MSP/src  CPPFLAGS="-DFFTW -DSFFTW -DCPU_LITTLE_END -DLITTLE_END -msse2 -mfpmath=sse -mtune=generic -fopenmp" LD_LIB_FLAGS="-shared" -f makefile_static_pegasus
	make -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/ISP/src  CPPFLAGS="-DFFTW -DSFFTW -DCPU_LITTLE_END -DLITTLE_END -msse2 -mfpmath=sse -mtune=generic -fopenmp" LD_LIB_FLAGS="-shared" -f makefile_static_pegasus
	make -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/DIFF/src CPPFLAGS="-DFFTW -DSFFTW -DCPU_LITTLE_END -DLITTLE_END -msse2 -mfpmath=sse -mtune=generic -fopenmp" LD_LIB_FLAGS="-shared" -f makefile_static_pegasus
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/DISP/bin/* $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/BIN
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/MSP/bin/*  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/BIN
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/ISP/bin/*  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/BIN
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/DIFF/bin/* $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_LITEND/BIN
GAMMA_BIGEND: 
	mkdir -p $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND
	mkdir -p $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/BIN
	tar xvfz $(PARENTDIR)/sources/roipac/install_gamma/GAMMA_SOFTWARE-20160625_MSP_ISP_DIFF_LAT.src.tar.gz -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND
	mv    $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/GAMMA_SOFTWARE-20160625/* $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND
	rm -r $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/GAMMA_SOFTWARE-20160625
	cp $(PARENTDIR)/sources/roipac/install_gamma/MSP_makefile_static_pegasus_20160625  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/MSP/src/makefile_static_pegasus
	cp $(PARENTDIR)/sources/roipac/install_gamma/ISP_makefile_static_pegasus_20160625  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/ISP/src/makefile_static_pegasus
	cp $(PARENTDIR)/sources/roipac/install_gamma/DISP_makefile_static_pegasus_20160625 $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/DISP/src/makefile_static_pegasus
	cp $(PARENTDIR)/sources/roipac/install_gamma/DIFF_makefile_static_pegasus_20160625 $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/DIFF/src/makefile_static_pegasus
	cp $(PARENTDIR)/sources/roipac/install_gamma/LAT_makefile_static_pegasus_20160625  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/LAT/src/makefile_static_pegasus
	# FA 8/2017: removed -fopenmp option to avoid using multiple cores
	make -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/DISP/src CPPFLAGS="-DFFTW -DSFFTW -DCPU_LITTLE_END -msse2 -mfpmath=sse -mtune=generic" LD_LIB_FLAGS="-shared" -f makefile_static_pegasus
	make -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/MSP/src  CPPFLAGS="-DFFTW -DSFFTW -DCPU_LITTLE_END -msse2 -mfpmath=sse -mtune=generic" LD_LIB_FLAGS="-shared" -f makefile_static_pegasus
	make -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/ISP/src  CPPFLAGS="-DFFTW -DSFFTW -DCPU_LITTLE_END -msse2 -mfpmath=sse -mtune=generic" LD_LIB_FLAGS="-shared" -f makefile_static_pegasus
	make -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/DIFF/src CPPFLAGS="-DFFTW -DSFFTW -DCPU_LITTLE_END -msse2 -mfpmath=sse -mtune=generic" LD_LIB_FLAGS="-shared" -f makefile_static_pegasus
	make -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/LAT/src  CPPFLAGS="-DFFTW -DSFFTW -DCPU_LITTLE_END -msse2 -mfpmath=sse -mtune=generic" LD_LIB_FLAGS="-shared" -f makefile_static_pegasus
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/DISP/bin/* $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/BIN
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/MSP/bin/*  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/BIN
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/ISP/bin/*  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/BIN
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/DIFF/bin/* $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/BIN
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/LAT/bin/* $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BIGEND/BIN
GAMMA_BINARY: 
	mkdir -p $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY
	mkdir -p $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/BIN
	tar xvfz $(PARENTDIR)/sources/roipac/install_gamma/GAMMA_SOFTWARE-20160625_MSP_ISP_DIFF_LAT_IPTA.linux64_rhel6.tar.gz -C $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY
	mv    $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/GAMMA_SOFTWARE-20160625/* $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY
	rm -r $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/GAMMA_SOFTWARE-20160625
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/DISP/bin/* $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/BIN
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/MSP/bin/*  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/BIN
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/ISP/bin/*  $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/BIN
	mv $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/DIFF/bin/* $(PARENTDIR)/3rdparty/gamma/GAMMA_SOFTWARE-20160625_BINARY/BIN

IMAGEMAGICK:
	cd $(IMAGEMAGICKHOME); ./configure --prefix=$(IMAGEMAGICKHOME)  --with-gs-font-dir=$(PARENTDIR)/3rdparty/GhostScript/fonts   
	cd $(IMAGEMAGICKHOME); make 
	cd $(IMAGEMAGICKHOME); make install
GETORB:
	cp $(PARENTDIR)/sources/roipac/install_getorb/Makefile_falk $(GETORBHOME)
	cd $(GETORBHOME); make -f Makefile_falk all BIN_DIR=$(INT_BIN)
	cd $(GETORBHOME); make -f Makefile_falk install BIN_DIR=$(INT_BIN)
RSMAS:
	cd $(PARENTDIR)/sources/roipac; make all
	cd $(PARENTDIR)/sources/roipac; make install

PYTHON2:
	echo " ...installing anaconda python....  ...please wait.... "
	mkdir -p $(PARENTDIR)/3rdparty/python
	cd $(PARENTDIR)/3rdparty/python; ./Anaconda2-4.2.0-Linux-x86_64.sh -b -p $(PYTHON2DIR)
	${PYTHON2DIR}/bin/conda install git --yes
	${PYTHON2DIR}/bin/conda config --add channels conda-forge
	${PYTHON2DIR}/bin/conda install basemap --yes   
	${PYTHON2DIR}/bin/conda install scons --yes    
	${PYTHON2DIR}/bin/conda install joblib --yes   
	${PYTHON2DIR}/bin/conda install gdal --yes   
	# gdal installation because ogr2ogr is used by json_mbtiles2insarmaps. Python 3.6 ogr2ogr does not seem to work
PYTHON35:
	$(eval export PYTHON3DIR=$(PARENTDIR)/3rdparty/python/anaconda35)
	cd $(PARENTDIR)/3rdparty/python; ./Anaconda3-4.2.0-Linux-x86_64.sh -b -p $(PYTHON3DIR)
	$(PYTHON3DIR)/bin/conda config --add channels conda-forge
	$(PYTHON3DIR)/bin/conda install -c omnia fftw3f=3.3.4 --yes
	$(PYTHON3DIR)/bin/conda install krb5 basemap pyresample psycopg2 geocoder requests --yes
	$(PYTHON3DIR)/bin/conda install gdal libgdal --yes
PYTHON36:
	$(eval export PYTHON3DIR=$(PARENTDIR)/3rdparty/python/anaconda36)
	cd $(PARENTDIR)/3rdparty/python; ./Anaconda3-5.2.0-Linux-x86_64.sh -b -p $(PYTHON3DIR)
	$(PYTHON3DIR)/bin/conda config --add channels conda-forge
	$(PYTHON3DIR)/bin/conda install krb5 basemap pyresample geocoder requests --yes
	#$(PYTHON3DIR)/bin/conda install libgdal --yes
	#$(PYTHON3DIR)/bin/conda install gdal --yes   # removed because ogr2ogr (in json2insarmaps) does not work
	$(PYTHON3DIR)/bin/conda install -c omnia fftw3f=3.3.4 --yes
	$(PYTHON3DIR)/bin/pip install psycopg2        # install via conda did not work
	$(PYTHON3DIR)/conda install opencv --yes      
	$(PYTHON3DIR)/conda install -c defaults libprotobuf protobuf --yes
PYKML:
	cd $(PARENTDIR)/3rdparty; git clone https://github.com/yunjunz/pykml.git
	cd $(PARENTDIR)/3rdparty/pykml; $(PYTHON3DIR)/bin/python setup.py build
	cd $(PARENTDIR)/3rdparty/pykml; $(PYTHON3DIR)/bin/python setup.py install
PYAPS: 
	tar xfv $(PARENTDIR)/sources/roipac/install_pygrib/pygrib_2.0.1.orig.tar.xz -C $(PARENTDIR)/3rdparty/pygrib
	cd $(JASPER_DIR);  patch -Np1 -i ../jasper-1.900.1-security_fixes-2.patch
	cd $(JASPER_DIR);  ./configure --prefix $(JASPER_DIR) --enable-shared --disable-static --mandir=$(JASPER_DIR)/share/man
	cd $(JASPER_DIR);  make
	cd $(JASPER_DIR);  make install
	cd $(GRIBAPI_DIR); ./configure --prefix $(GRIBAPI_DIR)
	cd $(GRIBAPI_DIR); make
	cd $(GRIBAPI_DIR); make install
	cd $(JPEG_DIR); ./configure --prefix $(JPEG_DIR)
	cd $(JPEG_DIR); make 
	cd $(JPEG_DIR); make install
	cd $(JPEG_DIR); make clean
	${PYTHON2DIR}/bin/conda install pygrib --yes
	cp $(PARENTDIR)/sources/roipac/install_pyaps/model.cfg $(PYAPS_DIR)/pyaps

INSARMAPS: 
	# NOTE: needs GDAL's source-built ogr2ogr as conda's ogr2ogr does not have the postgres driver. FA 11/2016
	cd $(PARENTDIR)/3rdparty/tippecanoe; make install PREFIX=$(PARENTDIR)/3rdparty/tippecanoe
	rm -f $(GDALHOME)/bin/ogr2ogr
	#${PYTHON2DIR}/bin/conda install psycopg2 --yes                   # commented out 6/2018
	#conda install gdal -n python2 --yes;                            # commented out 2/2017
	#conda install psycopg2 -n python2 --yes;                        # commented out 2/2017
	#cd $(PARENTDIR)/3rdparty/python/anaconda3/bin; rm -f python;    # commented out 2/2017
	#cd $(PARENTDIR)/3rdparty; git clone https://github.com/DenisCarriere/geocoder
	#cd $(PARENTDIR)/3rdparty/geocoder; python setup.py install       # commented out 6/2018
clean:
	cd $(FFTWHOME);			make clean
	cd $(ROIPACHOME);		make clean
	cd sources/roipac;		make clean
	cd $(TIFFHOME);			make clean
	cd $(GEOTIFFHOME);		make clean
	cd $(GDALHOME);			make clean
	cd $(HDF5HOME);			make clean
	#cd $(MDXHOME);			make -f Makemdx_gfortran clean
	cd $(GAMMA_HOME); 		make -f makefile_static_pegasus clean 
	cd $(GETORBHOME); 		make -f Makefile_falk uninstall BIN_DIR=$(INT_BIN)
	cd $(ROIPACHOME); cd ../../codes_roi_pacv3.0.1;		make clean

uninstall:
	cd $(FFTWHOME);			make uninstall
	cd $(ROIPACHOME);		make uninstall
	cd sources/roipac;		make uninstall
	cd $(TIFFHOME);			make uninstall
	cd $(GEOTIFFHOME);		make uninstall
	cd $(HDF5HOME);			make uninstall
	#cd $(GDALHOME);			make uninstall       # does not have this option
	cd $(MDXHOME);			make uninstall
	cd $(GAMMA_HOME); 		make uninstall
	cd $(GETORBHOME); 		make -f Makefile_falk uninstall BIN_DIR=$(INT_BIN)
	cd $(ROIPACHOME); cd ../../codes_roi_pacv3.0.1;		make uninstall
	rm -r $(INT_BIN)

test:
	cd $(PARENTDIR)/samples/distribution_testing/process_rsmas_Env ; make all
	#cd $(PARENTDIR)/samples/distribution_testing ; make default $(ROIPACTESTFLAG)
