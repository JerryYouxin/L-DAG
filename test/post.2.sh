#!/bin/bash
set -e
for (( i=0; i<10; i=i+1 ))
do
  cat ${i}.res.txt
done
touch res.txt
