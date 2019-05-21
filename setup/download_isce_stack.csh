#!/bin/csh -v

setenv DOWNLOAD_DIR ${PARENTDIR}/3rdparty
cd $DOWNLOAD_DIR
git clone https://github.com/isce-framework/isce2.git

test -d $PARENTDIR/sources/isceStack && rm -r $PARENTDIR/sources/isceStack
mkdir -p $PARENTDIR/sources/isceStack

cp -r $DOWNLOAD_DIR/isce2/contrib/stack/topsStack $PARENTDIR/sources/isceStack
cp -r $DOWNLOAD_DIR/isce2/contrib/stack/stripmapStack $PARENTDIR/sources/isceStack
