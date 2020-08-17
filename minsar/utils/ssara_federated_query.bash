#!/bin/bash

ssara_federated_query.py "$@" > ssara_listing.txt

regex="https:\/\/datapool\.asf\.alaska\.edu\/[a-zA-Z\/0-9\_]+\.zip"

urls=$(grep -oP $regex ssara_listing.txt)

for f in $urls; do
    #echo $f
    wget --user famelung --password Falk@1234: $f
done
