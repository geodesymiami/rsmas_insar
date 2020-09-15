###  Known issues with data
* Data unpacking problems
run_02_unpack_secondary_slc (Sentinel1_TOPS) may fail because of issues with the data. `check_job_outputs.py` raises an exception when one of the following strings is found:

```
`There appears to be a gap between slices. Cannot stitch them successfully`
`no element found: line`
`Trying to combine SLC products from different IPF versions`
`Exiting .......`
```

Currently  you need to add problem scenes into `topsStack.excludeDates`.  In principle we could remove the offending dates from the run_files, but this hasnot been implemented.


* Other potential errors for which excpetions are raised
```
                   'Segmentation fault',
                    'Bus',
                    'Aborted',
                    'ERROR',
                    'Error',
                    'FileNotFoundError',
                    'IOErr',
                    'Traceback'
```
