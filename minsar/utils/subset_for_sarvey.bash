#!/usr/bin/env bash
set -e

function print_help {
    echo "Usage: subset_for_sarvey.bash MIAPLPY_DIR [--lat LAT_MIN LAT_MAX --lon LON_MIN LON_MAX] [--outdir OUTPUT_DIR]"
    echo "       or"
    echo "       subset_for_sarvey.bash MIAPLPY_DIR LAT_MIN:LAT_MAX,LON_MIN:LON_MAX --outdir OUTPUT_DIR"
    echo "           requires Falk's  MintPy modification supporting subsetting of non-geocoded data: "
    echo "           https://github.com/falkamelung/MintPy"
    echo "           (in Miami using alias setmintpyfalk)"
    echo ""
    echo "Examples:"
    echo "  subset_for_sarvey.bash miaplpy_MDCBeach_201710_202310 --lat 25.937 25.958 --lon -80.125 -80.118 --outdir Oceana"
    echo "  subset_for_sarvey.bash miaplpy_MDCBeach_201710_202310 25.937:25.958,-80.125:-80.118 --outdir Oceana"
    echo ""
    echo "  subset_for_sarvey.bash miaplpy_SN_201606_201608 --lat -0.84 -0.83 --lon -91.17 -91.16 --outdir minas"
    echo "  subset_for_sarvey.bash miaplpy_SN_201606_201608 -0.84:-0.83,-91.17:-91.16 --outdir minas"
    exit 0
}

[[ "$1" == "-h" || "$1" == "--help" ]] && print_help

args=( "$@" )

INPUT_DIR="$1"
shift

LAT_MIN=""
LAT_MAX=""
LON_MIN=""
LON_MAX=""
OUTDIR=""

# Parse bbox shorthand
if [[ "$1" =~ ^[0-9.+-]+:[0-9.+-]+,[-0-9.]+:[-0-9.]+$ ]]; then
    BBOX="$1"
    shift
    LAT_PART="${BBOX%%,*}"
    LON_PART="${BBOX##*,}"
    LAT_MIN="${LAT_PART%%:*}"
    LAT_MAX="${LAT_PART##*:}"
    LON_MIN="${LON_PART%%:*}"
    LON_MAX="${LON_PART##*:}"
    OUTDIR="$2"
else
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            --lat)
                LAT_MIN="$2"
                LAT_MAX="$3"
                shift 3
                ;;
            --lon)
                LON_MIN="$2"
                LON_MAX="$3"
                shift 3
                ;;
            --outdir)
                OUTDIR="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1"
                print_help
                ;;
        esac
    done
fi

[[ -z "$LAT_MIN" || -z "$LAT_MAX" || -z "$LON_MIN" || -z "$LON_MAX" ]] && {
    echo "Error: latitude and longitude bounds must be specified."
    exit 1
}

[[ -z "$OUTDIR" ]] && {
    echo "Error: --outdir must be specified."
    exit 1
}

# Remove trailing slash if present
INPUT_DIR="${INPUT_DIR%/}"

# Assign input dir and extract base dir
if [[ "$INPUT_DIR" == inputs ]]; then
    BASE_DIR="$PWD"
else
    BASE_DIR="$INPUT_DIR"
    INPUT_DIR="inputs"
    OUTDIR=../$OUTDIR
    echo "cd into $BASE_DIR ..."
    cd "$BASE_DIR"
fi

[[ -f "$INPUT_DIR/slcStack.h5" ]] || { echo "Missing $INPUT_DIR/slcStack.h5"; exit 1; }
[[ -f "$INPUT_DIR/geometryRadar.h5" ]] || { echo "Missing $INPUT_DIR/geometryRadar.h5"; exit 1; }

mkdir -p "$OUTDIR/inputs"
echo "$(date +'%Y-%m-%d %H:%M:%S')  subset_for_sarvey.bash ${args[@]}" >> "${OUTDIR}/subset.log"
echo "Running... subset.py $INPUT_DIR/slcStack.h5 --lat $LAT_MIN $LAT_MAX --lon $LON_MIN $LON_MAX --output $OUTDIR/inputs/slcStack.h5"
subset.py $INPUT_DIR/slcStack.h5 --lat $LAT_MIN $LAT_MAX --lon $LON_MIN $LON_MAX --output $OUTDIR/inputs/slcStack.h5
echo "Running... subset.py $INPUT_DIR/geometryRadar.h5 --lat $LAT_MIN $LAT_MAX --lon $LON_MIN $LON_MAX --output $OUTDIR/inputs/geometryRadar.h5"
subset.py "$INPUT_DIR/geometryRadar.h5" --lat "$LAT_MIN" "$LAT_MAX" --lon "$LON_MIN" "$LON_MAX" --output "$OUTDIR/inputs/geometryRadar.h5"

PHASE_FILE="inverted/phase_series.h5"
if [[ -f "$PHASE_FILE" ]]; then
    mkdir -p "$OUTDIR/inverted"
    echo "Running... subset.py $PHASE_FILE --lat $LAT_MIN $LAT_MAX --lon $LON_MIN $LON_MAX --output $OUTDIR/inverted/phase_series.h5"
    subset.py "$PHASE_FILE" --lat "$LAT_MIN" "$LAT_MAX" --lon "$LON_MIN" "$LON_MAX" --output "$OUTDIR/inverted/phase_series.h5"
else
    echo "inverted/phase_series.h5 does not exist, can’t subset"
fi

cd - >/dev/null
