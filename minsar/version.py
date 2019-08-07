#!/usr/bin/env python3
# grab version / date of the latest commit
import os
import subprocess


###########################################################################
def get_release_info(version='v1.1.1-dev', date='2019-08-06'):
    """Grab version and date of the latest commit from a git repository"""
    # go to the repository directory
    dir_orig = os.getcwd()
    os.chdir(os.path.dirname(os.path.dirname(__file__)))

    # grab git info into string
    try:
        version = subprocess.check_output(["git", "describe", "--tags"])
        version = version.decode('utf-8').strip()

        # if there are new commits after the latest release
        if '-' in version:
            version, num_commit = version.split('-')[:2]
            version += '-{}'.format(num_commit)

        date = subprocess.check_output(["git", "log", "-1", "--date=short", "--format=%cd"])
        date = date.decode('utf-8').strip()
    except:
        pass

    # go back to the original directory
    os.chdir(dir_orig)
    return version, date
###########################################################################


release_version, release_date = get_release_info()

# generate_from: http://patorjk.com/software/taag/
logo = """
_________________________________________________      

   Miami Interferometric SAR processor  
          MinSAR {v}, {d}
_________________________________________________
""".format(v=release_version, d=release_date)

website = 'https://github.com/geodesymiami/rsmas_insar'

description = """MinSAR release version {v}, release date {d}""".format(v=release_version,
                                                                        d=release_date)
