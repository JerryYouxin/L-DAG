#!/bin/bash
set -e
cat 2.txt
for (( i=0; i<10; i=i+1 ))
do
  touch ${i}.2.txt
done
