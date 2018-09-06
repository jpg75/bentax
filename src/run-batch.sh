#!/bin/bash
####################################################
# Experiments for BEN resources using multiple seeds

# Basic configuration:
BASE_EXP_PATH="./batch_experiments"
CFG_PATH="./ben/"
SIM_PATH="../../aesop-acp/src"
# Required to let the interpreter import the modules of the current project
# otherwise it will just see the folder from where we started the simulator! 
PYTHON_EXTRA_PATH="."

# Generate the default dir for data experiments
if [ ! -e $CFG_PATH/$BASE_EXP_PATH ] 
then 
	mkdir $CFG_PATH/$BASE_EXP_PATH
fi

CFG_FILES="schedule-100-add-nodyn.xlsx schedule-200-add-nodyn.xlsx schedule-400-add-nodyn.xlsx schedule-600-add-nodyn.xlsx schedule-800-add-nodyn.xlsx schedule-1000-add-nodyn.xlsx schedule-100-add-dyn.xlsx schedule-200-add-dyn.xlsx schedule-400-add-dyn.xlsx schedule-600-add-dyn.xlsx schedule-800-add-dyn.xlsx schedule-1000-add-dyn.xlsx"
# CFG_FILES="schedule-400-add-nodyn.xlsx schedule-1000-add-nodyn.xlsx schedule-100-add-dyn.xlsx schedule-200-add-dyn.xlsx schedule-400-add-dyn.xlsx schedule-1000-add-dyn.xlsx"
# CFG_FILES="schedule-600-add-nodyn.xlsx schedule-600-add-dyn.xlsx schedule-800-add-nodyn.xlsx schedule-800-add-dyn.xlsx"

TIME=400 # time duration of experiments

for cfile in $CFG_FILES; do
# cfgpars=$(echo $cfile | sed -e 's/schedule-//' -e 's/.xlsx//' ) 
# echo $cfgpars

for tax in 0.3 0.4 0.5; do

for ep in 0.3 0.5 0.8; do

# perform simulations on distinct random seeds:
# for seed in 1234567890 2345678901 3456789012 4567890123 5678901234 6789012345 7890123456 8901234567 9012345678 0123456789; do
for seed in 1234567890 2345678901 3456789012; do

cfgpars=$(echo $cfile | sed -e 's/schedule-//' -e 's/.xlsx//' )
cfgpars=$cfgpars-tax$tax-employedp$ep
echo $seed "with params: " $cfgpars

PYTHONPATH=$PYTHON_EXTRA_PATH python2.7 $SIM_PATH/startsim.py -d $CFG_PATH \
		-s $cfile -S $seed -u $TIME -p "ben.ecosystem.TaxPayer;TAX;$tax" \
		-p "ben.ecosystem.TaxPayer;PUBLIC_SECTOR_PROP;$ep" > log.txt

done # end seed
# after seeds save the data in a specific folder
if [ ! -e $CFG_PATH/$BASE_EXP_PATH/$cfgpars ] 
then 
	mkdir $CFG_PATH/$BASE_EXP_PATH/$cfgpars
fi

# put the file of the current configfile to the corresponding subdir
mv $CFG_PATH/$BASE_EXP_PATH/*.txt $CFG_PATH/$BASE_EXP_PATH/$cfgpars

done # end tax

done # end ep

done # end cfile

