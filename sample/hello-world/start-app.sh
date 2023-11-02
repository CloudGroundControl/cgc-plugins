#!/bin/sh
requestFile=$1
resultFolder=$2
resultFile=$3
stopFile=$4
outputChannelFolder=$5
inputChannelFolder=$6
telemetryStreamFolder=$7

python3 main.py --request-file "$requestFile" --result-folder "$resultFolder" --result-file "$resultFile" --stop-file "$stopFile" --output-channel-folder "$outputChannelFolder" --input-channel-folder "$inputChannelFolder" --telemetry-stream-folder "$telemetryStreamFolder"
