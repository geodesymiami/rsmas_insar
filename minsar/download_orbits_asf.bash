#!/usr/bin/env bash
#############################################################
# download latest orbits from ASF mirror
#!/usr/bin/env bash
set -euo pipefail

show_help() {
    echo "Usage: ${0##*/}"
    echo
    echo "Downloads the latest orbits from ASF."
    echo
    echo "Options:"
    echo "  --help    Show this help message and exit"
    echo
    echo "Examples:"
    echo "  ${0##*/}"
}

# ---------------------------------------------
# Handle command-line arguments (if any)
# ---------------------------------------------
if [[ $# -gt 0 ]]; then
  case "$1" in
    --help|-h)
      show_help
      exit 0
      ;;
    *)
      echo "Error: Unknown argument '$1'" >&2
      show_help
      exit 1
      ;;
  esac
fi

    echo "Preparing to download latest poe and res orbits from ASF..."
    year=$(date +%Y)
    current_month=$(date +%Y%m)
    previous_month=$(date -d'-1 month' +%Y%m)

    cd $SENTINEL_ORBITS
    curl --ftp-ssl-reqd --silent --use-ascii --ftp-method nocwd --list-only https://s1qc.asf.alaska.edu/aux_poeorb/ > ASF_poeorb.txt
    curl --ftp-ssl-reqd --silent --use-ascii --ftp-method nocwd --list-only https://s1qc.asf.alaska.edu/aux_resorb/ > ASF_resorb.txt
    cat ASF_poeorb.txt | awk '{printf "if ! test -f %s; then  wget -c https://s1qc.asf.alaska.edu/aux_poeorb/%s; fi\n", substr($0,10,77), substr($0,10,77)}' | grep $year > ASF_poeorb_latest.txt
    cat ASF_resorb.txt | awk '{printf "if ! test -f %s; then  wget -c https://s1qc.asf.alaska.edu/aux_resorb/%s; fi\n", substr($0,10,77), substr($0,10,77)}' | grep $current_month  >  ASF_resorb_latest.txt
    cat ASF_resorb.txt | awk '{printf "if ! test -f %s; then  wget -c https://s1qc.asf.alaska.edu/aux_resorb/%s; fi\n", substr($0,10,77), substr($0,10,77)}' | grep $previous_month >> ASF_resorb_latest.txt
    echo "Downloading poe orbits: running bash ASF_poeorb_latest.txt in orbit directory  $SENTINEL_ORBITS  ..."
    bash ASF_poeorb_latest.txt
    echo "Downloading res orbits: running bash ASF_resorb_latest.txt in orbit directory  $SENTINEL_ORBITS  ..."
    bash ASF_resorb_latest.txt
    cd -
