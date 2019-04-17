#!/bin/bash
set -e
MODE=foo
python3 DagGenerator.py --xml=input-${1}-${2}.xml --mode=${MODE} --out=./${1}_${2}_${MODE}/
cp *.sh ./${1}_${2}_${MODE}
cd ./${1}_${2}_${MODE}
condor_submit_dag submit.dag

while true
do
  Q=`condor_q`
  #condor_q
  if [[ $Q == *submit* ]]
  then
    sleep 1
  elif [[ $Q == *DAG* ]]
  then
    sleep 1
  else
    break
  fi
done

echo Finish

cd ..

MODE=sub
python3 DagGenerator.py --xml=input-${1}-${2}.xml --mode=${MODE} --out=./${1}_${2}_${MODE}/
cp *.sh ./${1}_${2}_${MODE}
cd ./${1}_${2}_${MODE}
condor_submit_dag submit.dag

while true
do
  Q=`condor_q`
  #condor_q
  if [[ $Q == *submit* ]] 
  then
    sleep 1
  elif [[ $Q == *DAG* ]]
  then
    sleep 1
  else
    break
  fi
done

echo Finish

cd ..
