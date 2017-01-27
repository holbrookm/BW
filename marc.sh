#!/bin/bash

HOST="10.144.134.198"
PORT="2208"
TIMEOUT=5

fixxml()
{
    gawk 'BEGIN {RS="><"} printf $0"\n<"}';
}

timeout -s INT $TIMEOUT bash -c "exec 3<>/dev/tcp/$HOST/$PORT";
echo "Checking Connection"
if [ $? -ne 0 ]; then
    echo "No Connection";
    exec 3>&-;
    exit -1;
fi;


exec 3<>/dev/tcp/$HOST/$PORT;

echo "Start with NONCE"
NONCE=$(cat ./temp.xml.tmpl >&3);
head <&3;
echo $NONCE;
