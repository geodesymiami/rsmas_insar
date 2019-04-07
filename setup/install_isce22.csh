#!/bin/csh -v
# Script for ISCE installation. Requires $PARENTDIR, $ISCEHOME,  $PYTHON3DIR

setenv ISCEDOWNLOADFILE ${PARENTDIR}/3rdparty/isce/isce-2.2.0.tar.bz2
setenv SCONS_CONFIG_DIR ${PARENTDIR}/3rdparty/isce/isce-2.2.0

########################################################
echo "Create SConfigISCE file  ..."
########################################################
cat >! SConfigISCE<<EOF
PRJ_SCONS_BUILD = $ISCE_BUILD/build/
PRJ_SCONS_INSTALL = $ISCE_BUILD/isce/
LIBPATH = $PYTHON3DIR/lib64/ $PYTHON3DIR/lib
CPPPATH = $PYTHON3DIR/include $PYTHON3DIR/include/python3.6m $PYTHON3DIR/lib/python3.6/site-packages/numpy/core/include
FORTRANPATH = $PYTHON3DIR/include
FORTRAN=gfortran
CC=gcc
CXX=g++

MOTIFLIBPATH = /usr/lib64/
X11LIBPATH  = /usr/lib/
MOTIFINCPATH = /usr/include/Xm
X11INCPATH = /usr/include/X11

ENABLE_CUDA = False
EOF
########################################################
echo "Install isce in $ISCE_HOME  ..."
########################################################
test -d $SCONS_CONFIG_DIR && rm -r $SCONS_CONFIG_DIR
test -d $ISCE_HOME && rm -r $ISCE_HOME
mkdir -p $SCONS_CONFIG_DIR
tar xjf $ISCEDOWNLOADFILE -C ${SCONS_CONFIG_DIR}/..
cd $SCONS_CONFIG_DIR
rm -rf .sconf_temp/ .sconsign.dblite config.log 
cp $PARENTDIR/setup/SConfigISCE .
scons install SConfigISCE
cp -r $SCONS_CONFIG_DIR/contrib/stack/topsStack $PARENTDIR/sources/isceStack
cp -r $SCONS_CONFIG_DIR/contrib/stack/stripmapStack $PARENTDIR/sources/isceStack
