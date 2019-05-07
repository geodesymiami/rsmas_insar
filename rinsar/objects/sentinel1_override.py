#!/usr/bin/env python3
# Author: Sara Mirzaee

from isceobj.Sensor.TOPS.Sentinel1 import Sentinel1
from stackSentinel import get_dates

class Sentinel1_burst_count(Sentinel1):
    """
    Sentinel-1A TOPS reader
    """

    def get_burst_num(self, inps, swath):

        dateList, master_date, slaveList, safe_dict = get_dates(inps)
        dirname = safe_dict[master_date].safe_file

        self.safe = dirname.split()
        self.swathNumber = swath
        self.output = os.path.join(inps.work_dir, 'master', 'IW{0}'.format(swath))
        self.orbitFile = None
        self.auxFile = None
        self.orbitDir = inps.orbit_dirname
        self.auxDir = inps.aux_dirname
        self.polarization = inps.polarization

        if inps.bbox is not None:
            self.regionOfInterest = [float(x) for x in inps.bbox.split()]
        try:
            return self.parse()
        except:
            print('counting bursts failed!')
            return None


    def parse(self):
        '''
        Parser for S1A IW data.
        This is meant to only read in the metadata and does not read any imagery.
        Can be used only with the annotation xml files if needed.
        '''

        ####Check user inputs
        self.validateUserInputs()

        self._numSlices = len(self.xml)

        if self._numSlices > 1:
            self._parseMultiSlice()
        else:
            self._parseOneSlice()

        ###Set the parsed flag to True
        self._parsed = True

        return self.number_of_burst


    def _parseOneSlice(self):
        '''
        '''
        if self.xml[0].startswith('/vsizip'):
            import zipfile
            parts = self.xml[0].split(os.path.sep)

            if parts[2] == '':
                parts[2] = os.path.sep

            zipname = os.path.join(*(parts[2:-3]))
            fname = os.path.join(*(parts[-3:]))

            zf = zipfile.ZipFile(zipname, 'r')
            xmlstr = zf.read(fname)
            zf.close()
        else:
            with open(self.xml[0], 'r') as fid:
                xmlstr = fid.read()

        self._xml_root = ET.fromstring(xmlstr)
        numberBursts = self.getNumberOfBurstsFromAnnotation()

        ####Create empty burst SLCs
        for kk in range(numberBursts):
            slc = BurstSLC()
            slc.configure()
            slc.burstNumber = kk + 1
            self.product.bursts.append(slc)

        self.product.numberOfBursts = numberBursts

        ####Populate processing software info
        if len(self.manifest) != 0:
            self.populateIPFVersion()

        ####Populate common metadata
        self.populateCommonMetadata()

        ####Populate specific metadata
        self.populateBurstSpecificMetadata()

        ####Populate orbit information
        ###Try and locate an orbit file
        if self.orbitFile is None:
            if self.orbitDir is not None:
                self.orbitFile = s1_findOrbitFile(self.orbitDir,
                                                  self.product.bursts[0].sensingStart,
                                                  self.product.bursts[-1].sensingStop,
                                                  mission=self.product.mission)

        ####Read in the orbits
        if self.orbitFile:
            orb = self.extractPreciseOrbit()
        else:
            orb = self.extractOrbitFromAnnotation()

        for burst in self.product.bursts:
            if self.orbitFile:
                burst.orbit.setOrbitSource(os.path.basename(self.orbitFile))
            else:
                burst.orbit.setOrbitSource('Annotation')

            for sv in orb:
                burst.orbit.addStateVector(sv)

            ####Determine pass direction using Vz
            VV = burst.orbit.interpolateOrbit(burst.sensingMid, method='hermite').getVelocity()
            if VV[2] >= 0:
                burst.passDirection = 'ASCENDING'
            else:
                burst.passDirection = 'DESCENDING'

        ####If user provided a region of interest
        if len(self.regionOfInterest) != 0:
            self.number_of_burst = self.crop(self.regionOfInterest)

        return

    def crop(self, bbox):
        '''
        Crop a given slice with a user provided bbox (SNWE).
        '''

        from iscesys.Component import createTraitSeq

        def overlap(box1, box2):
            '''
            Overlapping rectangles overlap both horizontally & vertically
            '''
            hoverlaps = True
            voverlaps = True

            if (box1[2] >= box2[3]) or (box1[3] <= box2[2]):
                hoverlaps = False

            if (box1[1] <= box2[0]) or (box1[0] >= box2[1]):
                voverlaps = False

            return hoverlaps and voverlaps

        cropList = createTraitSeq('burst')

        ###For each burst
        for ind, burst in enumerate(self.product.bursts):
            burstBox = burst.getBbox()

            #####If it overlaps, keep the burst
            if overlap(burstBox, bbox):
                cropList.append(burst)

        return len(cropList)



