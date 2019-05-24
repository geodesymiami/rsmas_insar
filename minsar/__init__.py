# LOGGING
import logging
import os, sys

rsmasinsar_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, rsmasinsar_path)
sys.path.insert(1,os.path.join(rsmasinsar_path,'objects'))
sys.path.insert(1,os.path.join(rsmasinsar_path,'utils'))
sys.path.insert(1,os.path.join(rsmasinsar_path,'defaults'))

try:
    os.environ['RSMAS_INSAR']
except KeyError:
    print('Using default MintPy Path: %s' % (insar_path))
    os.environ['RSMAS_INSAR'] = insar_path


logging.basicConfig(filename="example.log",
                            format='%(asctime)s | %(name)-25s | [ %(levelname)s ]'
                                                       ' | %(filename)s:%(lineno)d | %(message)s',
                                                                           level=logging.DEBUG)
ch = logging.StreamHandler()
verbose = False
if verbose:
    ch.setLevel(logging.DEBUG)
else:
    ch.setLevel(logging.ERROR)
warning_logger = logging.getLogger("process_sentinel")
warning_logger.addHandler(ch)
logger = logging.getLogger("process_sentinel." + "__init__")

logger.debug('Starting Logger')
#logger.error('YO WHATS GOOD???')
