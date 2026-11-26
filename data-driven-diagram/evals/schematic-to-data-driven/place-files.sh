#!/usr/bin/env bash
set -eu
# the project of the kmeans-overview-figure case, plus the schematic that is to be replaced
cp -R "$(dirname "$0")/../kmeans-overview-figure/files/." .
cp -R "$(dirname "$0")/files/." .
