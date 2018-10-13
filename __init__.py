# LOING
import logging
logging.basicConfig(filename="example.log",
                            format='%(asctime)s | %(name)-25s | [ %(levelname)s ]'
                                                       ' | %(filename)s:%(lineno)d | %(message)s',
                                                                           level=logging.DEBUG)
#testingtesting
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
logger.error('YO WHATS GOOD?')
