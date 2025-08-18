#!/usr/bin/env sh
set -eu
IFS='
	 '

# --- Load environment file ---------------------------------------------------
ENV_FILE=${ENV_FILE:-.env}
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  . "$ENV_FILE"
fi

# --- Config with defaults ----------------------------------------------------
DATASOURCE_ID=${DATASOURCE_ID:-1}
JOIN_IGNORE_CASE=${JOIN_IGNORE_CASE:-0}
OUTPUT_DIR_DEFAULT=${OUTPUT_DIR:-.}
OUTPUT_FILENAME=${OUTPUT_FILENAME:-}
KEEP_INTERMEDIATE=${KEEP_INTERMEDIATE:-0}

# Unified date config
DATE_SOURCE_COL=${DATE_SOURCE_COL:-'Accession Date'}   # e.g., 'Accession Date' or 'Last Seen On'
DATE_SOURCE_FORMAT=${DATE_SOURCE_FORMAT:-"%Y"}          # "%Y" or "%d-%m-%Y", etc.
FILTER_BEFORE_DATE=${FILTER_BEFORE_DATE:-}              # "YYYY-MM-DD", empty=skip

# --- Usage -------------------------------------------------------------------
if [ $# -lt 1 ]; then
  echo "Usage: $0 <kew-species-list.csv> [outdir] [outfile]" >&2
  exit 1
fi

INPUT=$1
OUTDIR=${2:-$OUTPUT_DIR_DEFAULT}
OUTFILE_ARG=${3:-}

# --- Dependencies ------------------------------------------------------------
command -v xan >/dev/null 2>&1 || { echo "Error: xan not found in PATH" >&2; exit 1; }
command -v gnverifier >/dev/null 2>&1 || { echo "Error: gnverifier not found in PATH" >&2; exit 1; }

# --- Paths -------------------------------------------------------------------
mkdir -p "$OUTDIR"
base=$(basename "$INPUT")
stem=${base%.*}

LEFT_NONA="$OUTDIR/${stem}-nona.csv"
TAXON_NAMES="$OUTDIR/taxon_names.csv"
GN_OUT="$OUTDIR/taxon_name_gnverified_col.csv"
GN_DEDUP="$OUTDIR/taxon_name_gnverified_col_deduped.csv"

# Final output path (CLI arg3 > .env OUTPUT_FILENAME > default)
if [ -n "$OUTFILE_ARG" ]; then
  case "$OUTFILE_ARG" in */*) JOINED="$OUTFILE_ARG" ;; *) JOINED="$OUTDIR/$OUTFILE_ARG" ;; esac
elif [ -n "$OUTPUT_FILENAME" ]; then
  case "$OUTPUT_FILENAME" in */*) JOINED="$OUTPUT_FILENAME" ;; *) JOINED="$OUTDIR/$OUTPUT_FILENAME" ;; esac
else
  JOINED="$OUTDIR/${stem}-gnverified-col.csv"
fi
mkdir -p "$(dirname "$JOINED")"

TMPDIR=$(mktemp -d)
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT INT HUP TERM

echo "Config:"
echo "  DATASOURCE_ID      = $DATASOURCE_ID"
echo "  OUTPUT_DIR         = $OUTDIR"
echo "  OUTPUT_FILE        = $JOINED"
echo "  KEEP_INTERMEDIATE  = $KEEP_INTERMEDIATE"
echo "  JOIN_IGNORE_CASE   = $JOIN_IGNORE_CASE"
echo "  DATE_SOURCE_COL    = $DATE_SOURCE_COL"
echo "  DATE_SOURCE_FORMAT = $DATE_SOURCE_FORMAT"
echo "  FILTER_BEFORE_DATE = ${FILTER_BEFORE_DATE:-<unset>}"
echo

echo "Filtering out empty TaxonomicName -> $LEFT_NONA"
xan filter 'len(trim(TaxonomicName)) > 0' "$INPUT" > "$LEFT_NONA"

echo "Standardizing $DATE_SOURCE_COL to ISO (column: StandardDateISO)"
tmp="$TMPDIR/std_date.tmp.csv"
if [ "$DATE_SOURCE_FORMAT" = "%Y" ]; then
  # Year-only source: no datetime(); build an ISO date safely.
  xan map 'fmt("{}-01-01", trim(col("'"$DATE_SOURCE_COL"'")))' \
    StandardDateISO "$LEFT_NONA" > "$tmp" && mv "$tmp" "$LEFT_NONA"
else
  xan map 'strftime(datetime(trim(col("'"$DATE_SOURCE_COL"'")), "'"$DATE_SOURCE_FORMAT"'"), "%Y-%m-%d")' \
    StandardDateISO "$LEFT_NONA" > "$tmp" && mv "$tmp" "$LEFT_NONA"
fi

if [ -n "$FILTER_BEFORE_DATE" ]; then
  echo "Filtering rows with StandardDateISO < $FILTER_BEFORE_DATE"
  tmp="$TMPDIR/left_filtered.tmp.csv"
  xan filter 'len(StandardDateISO) > 0 and datetime(StandardDateISO) < datetime("'"$FILTER_BEFORE_DATE"'")' \
    "$LEFT_NONA" > "$tmp" && mv "$tmp" "$LEFT_NONA"
else
  echo "No FILTER_BEFORE_DATE set — skipping date filter."
fi

echo "Subsetting only TaxonomicName -> $TAXON_NAMES"
xan select TaxonomicName "$LEFT_NONA" > "$TAXON_NAMES"

echo "Running gnverifier (datasource $DATASOURCE_ID) -> $GN_OUT"
gnverifier -f csv -s "$DATASOURCE_ID" "$TAXON_NAMES" > "$GN_OUT"

echo "Deduplicating on ScientificName (keep first) -> $GN_DEDUP"
xan dedup -s ScientificName "$GN_OUT" > "$GN_DEDUP"

echo "Left joining Kew (TaxonomicName) with gnverified (ScientificName) -> $JOINED"
JOIN_FLAGS=""
[ "$JOIN_IGNORE_CASE" = "1" ] && JOIN_FLAGS="-i"
# shellcheck disable=SC2086
xan join --left $JOIN_FLAGS TaxonomicName "$LEFT_NONA" ScientificName "$GN_DEDUP" > "$JOINED"

if [ "$KEEP_INTERMEDIATE" = "0" ]; then
  echo "Removing intermediate files"
  rm -f "$LEFT_NONA" "$TAXON_NAMES" "$GN_OUT" "$GN_DEDUP"
else
  echo "Keeping intermediate files"
fi

echo "Done ✅  Final file: $JOINED"
