#!/bin/bash

outpath=~/uhmc-sigcomm24

./redis-icelake.sh $outpath icelake-redis-set-iso icelake-redis-set redis-set p2mwrite
./redis-icelake.sh $outpath redis-iso-prefetch icelake-redis-p2mread redis-p2mread p2mread
./redis-icelake.sh $outpath icelake-redis-set-iso icelake-redis-set-p2mread redis-set-p2mread p2mread

./gapbs-icelake.sh $outpath icelake-gapbs-bc-iso icelake-gapbs-bc gapbs-bc p2mwrite
./gapbs-icelake.sh $outpath gapbs-iso-prefetch icelake-gapbs-p2mread gapbs-p2mread p2mread
./gapbs-icelake.sh $outpath icelake-gapbs-bc-iso icelake-gapbs-bc-p2mread gapbs-bc-p2mread p2mread