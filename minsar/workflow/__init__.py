## Dynamic import for modules used in routine workflows
## Recommended usage:
##     import minsar
##     import minsar.workflow


from pathlib import Path
import importlib
import logging
import warnings


warnings.filterwarnings("ignore")

mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

sg_logger = logging.getLogger('shapely.geos')
sg_logger.setLevel(logging.WARNING)


# expose the following modules
__all__ = [
    'dem_rsmas',
    'download_rsmas',
    'create_runfiles',
    'email_results',
    'execute_runfiles',
    'export_amplitude_tif',
    'export_ortho_geo',
    'ifgramStack_to_ifgram_and_coherence',
    'upload_data_products',
    'ingest_insarmaps',
    'job_submission',
    'smallbaseline_wrapper',
    'minopy_wrapper',
    'process_rsmas',
    'version',
]

root_module = Path(__file__).parent.parent.name   # minsar
for module in __all__:
    importlib.import_module(root_module + '.' + module)
