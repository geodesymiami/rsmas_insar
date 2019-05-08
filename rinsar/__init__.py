# LOGGING
import logging
import os, sys
import importlib

rsmasinsar_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, rsmasinsar_path)

try:
    os.environ['RSMAS_INSAR']
except KeyError:
    print('Using default PySAR Path: %s' % (insar_path))
    os.environ['RSMAS_INSAR'] = insar_path

__all__ = [
    'create_runfiles',
    'create_batch',
    'dem_rsmas',
    'download_rsmas',
    'email_results',
    'execute_runfiles',
    'ingest_insarmaps'
]
for module in __all__:
    importlib.import_module(__name__ + '.' + module)


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
