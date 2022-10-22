#!/bin/bash

mnt=$1
sz=$2
num=$3
bs=$((1*1024*1024))

for i in $(seq 0 $(($num-1))); do
    dd if=/dev/zero of=$mnt/datafile$i bs=$bs count=$(($sz/$bs)) &
done
