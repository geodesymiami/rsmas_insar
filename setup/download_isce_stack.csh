#!/bin/csh -v

setenv DOWNLOAD_DIR ../3rdparty
cd $DOWNLOAD_DIR
git clone https://github.com/isce-framework/isce2.git

test -d ../sources/isceStack && rm -r ../sources/isceStack
mkdir -p ../sources/isceStack

cp -r $DOWNLOAD_DIR/isce2/contrib/stack/topsStack ../sources/isceStack
cp -r $DOWNLOAD_DIR/isce2/contrib/stack/stripmapStack ../sources/isceStack

rm -rf $DOWNLOAD_DIR/isce2
