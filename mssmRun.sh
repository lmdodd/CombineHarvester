# Script to make a convenient directory strucutre
# for the MSSM Phi->TauTau analysis
# masses are currently limited to completed
# ntuple root files.  More to come.

# Additionally, runs asymptotic limits for
# each channel by each mass


DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $DIR
LIMITDIR="LIMITS"
ERA="13TeV"

for signal in ggH bbH;
do
    for channel in et mt;
    do
        pushd ${DIR}
        HTT3 ${channel} ${signal}
    done
done

pushd $DIR/${LIMITDIR}

for channel in et mt;
do
    for signal in ggH;
    do
    	pushd $DIR/${LIMITDIR}/${signal}/${channel}
        #80-140:10,140-180:20,250,400,450,500-1000:100,1200,1500,1600,1800,2000,2600,2900,3200
        for mass in 80 90 100 110 120 130 140 160 180 250 400 500 600 700 900 1000 1200 1500 1600 1800 2000 2600 2900 3200;
        do
            for category in 2; 
            do 
                combine -M Asymptotic -m ${mass} ${mass}/htt_${channel}_${category}_${ERA}.txt
            done
        done
    done
done
pushd ${DIR} 

