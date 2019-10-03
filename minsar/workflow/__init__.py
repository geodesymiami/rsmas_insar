## Dynamic import for modules used in routine workflows
## Recommended usage:
##     import minsar
##     import minsar.workflow


from pathlib import Path
import importlib
import logging
import os
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

# expose the following modules
__all__ = [
    'dem_rsmas',
    'download_rsmas',
    'create_runfiles',
    'email_results',
    'execute_runfiles',
    'export_amplitude_tif',
    'ifgramStack_to_ifgram_and_coherence',
    'ingest_insarmaps',
    'job_submission',
    'smallbaseline_wrapper',
    'process_rsmas',
    'version',
]

stack_path = os.path.basename(os.getenv('ISCE_STACK'))
if stack_path == 'topsStack':
    __all__ = __all__ + ['export_ortho_geo']

print(__all__)

root_module = Path(__file__).parent.parent.name   # minsar
for module in __all__:
    importlib.import_module(root_module + '.' + module)
