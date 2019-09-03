from __future__ import print_function
import os
import sys

rsmasinsar_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, rsmasinsar_path)
sys.path.insert(1, os.path.join(rsmasinsar_path, 'objects'))
sys.path.insert(1, os.path.join(rsmasinsar_path, 'utils'))
sys.path.insert(1, os.path.join(rsmasinsar_path, 'defaults'))

from minsar.version import *
__version__ = release_version

try:
    os.environ['RSMASINSAR_HOME']
except KeyError:
    print('Using default MinSAR Path: %s' % (rsmasinsar_path))
    os.environ['RSMASINSAR_HOME'] = rsmasinsar_path


# logging.basicConfig(filename="example.log",
#                             format='%(asctime)s | %(name)-25s | [ %(levelname)s ]'
#                                                        ' | %(filename)s:%(lineno)d | %(message)s',
#                                                                            level=logging.DEBUG)
# ch = logging.StreamHandler()
# verbose = False
# if verbose:
#     ch.setLevel(logging.DEBUG)
# else:
#     ch.setLevel(logging.ERROR)
# warning_logger = logging.getLogger("process_rsmas")
# warning_logger.addHandler(ch)
# logger = logging.getLogger("process_rsmas." + "__init__")

# logger.debug('Starting Logger')
