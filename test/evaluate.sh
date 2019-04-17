#!/bin/bash
set -e
evaluate() {
  MODE=${3}
  { time python3 DagGenerator.py --xml=./xmls/input-template.xml --parameter=para.txt --mode=${MODE} --out=./${1}_${2}_${MODE}/; } 2>>time_${1}_${2}_${3}.txt
  cp *.sh ./${1}_${2}_${MODE}
  cd ./${1}_${2}_${MODE}
  condor_submit_dag submit.dag

  start=`date "+%s"`

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

  end=`date "+%s"`
  t=$((end-start))

  echo "Finish : $t sec"

  cd ..
  echo $3 $1 $2 $t >> time.txt 
}

for i in $( seq 2 16 )
do
   for j in $( seq 2 16 )
   do
      echo "outer=$i" > para.txt
      echo "inner=$j" >> para.txt
      evaluate $j $i foo
      evaluate $j $i sub
   done
done

#MODE=sub
#python3 DagGenerator.py --xml=input-${1}-${2}.xml --mode=${MODE} --out=./${1}_${2}_${MODE}/
#cp *.sh ./${1}_${2}_${MODE}
#cd ./${1}_${2}_${MODE}
#condor_submit_dag submit.dag

#while true
#do
#  Q=`condor_q`
#  #condor_q
#  if [[ $Q == *submit* ]] 
#  then
#    sleep 1
#  elif [[ $Q == *DAG* ]]
#  then
#    sleep 1
#  else
#    break
#  fi
#done
#
#echo Finish
#
#cd ..
