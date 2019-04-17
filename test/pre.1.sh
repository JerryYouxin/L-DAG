#!/bin/bash
set -e
for (( i=0; i<20; i=i+1 ))
do
  touch ${i}.1.txt
done
