#!/bin/bash

outpath=~/uhmc-sigcomm24

./redis-ddio.sh $outpath aug23-redis redis-p2mread redis-p2mread-ddio redis-p2mread
./redis-ddio.sh $outpath redis-set-iso redis-set-p2mread redis-set-p2mread-ddio redis-set-p2mread

./gapbs-ddio.sh $outpath aug23-gapbs gapbs-p2mread gapbs-p2mread-ddio gapbs-p2mread
./gapbs-ddio.sh $outpath gapbs-bc-iso gapbs-bc-p2mread gapbs-bc-p2mread-ddio gapbs-bc-p2mread