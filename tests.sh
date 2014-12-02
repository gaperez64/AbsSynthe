#!/bin/bash

# This is a benchmark framework that may be useful for evaluating
# synthesis tools developed for SyntComp.
#
# Version: 1.0.1
# Created by Robert Koenighofer, robert.koenighofer@iaik.tugraz.at
# Comments/edits by Swen Jacobs, swen.jacobs@iaik.tugraz.at

# This directory:
DIR=`dirname $0`/

# Time limit in seconds:
TIME_LIMIT=10
# Memory limit in kB:
MEMORY_LIMIT=2000000

# Maybe change the following line to point to GNU time:
GNU_TIME="gtime"
MODEL_CHECKER="$DIR/../blimc/blimc"
SYNT_CHECKER="$DIR/../aiger/syntactic_checker.py"

# The directory where the benchmarks are located:
BM_DIR="${DIR}/../bench-syntcomp14/"

REAL=10
UNREAL=20

# The benchmarks to be used.
# The files have to be located in ${BM_DIR}.
FILES=(
add10n    $REAL
add10y    $REAL
add12n    $REAL
add12y    $REAL
add14n    $REAL
add14y    $REAL
add16n    $REAL
add16y    $REAL
add18n    $REAL
add18y    $REAL
add20n    $REAL
add20y    $REAL
add2n    $REAL
add2y    $REAL
add4n    $REAL
add4y    $REAL
add6n    $REAL
add6y    $REAL
add8n    $REAL
add8y    $REAL
amba10b4unrealn    $UNREAL
amba10b4unrealy    $UNREAL
amba10b5n    $REAL
amba10b5y    $REAL
amba10c4unrealn    $UNREAL
amba10c4unrealy    $UNREAL
amba10c5n    $REAL
amba10c5y    $REAL
amba10f36unrealn    $UNREAL
amba10f36unrealy    $UNREAL
amba10f37n    $REAL
amba10f37y    $REAL
amba2b8unrealn    $UNREAL
amba2b8unrealy    $UNREAL
amba2b9n    $REAL
amba2b9y    $REAL
amba2c6unrealn    $UNREAL
amba2c6unrealy    $UNREAL
amba2c7n    $REAL
amba2c7y    $REAL
amba2f8unrealn    $UNREAL
amba2f8unrealy    $UNREAL
amba2f9n    $REAL
amba2f9y    $REAL
amba3b4unrealn    $UNREAL
amba3b4unrealy    $UNREAL
amba3b5n    $REAL
amba3b5y    $REAL
amba3c4unrealn    $UNREAL
amba3c4unrealy    $UNREAL
amba3c5n    $REAL
amba3c5y    $REAL
amba3f8unrealn    $UNREAL
amba3f8unrealy    $UNREAL
amba3f9n    $REAL
amba3f9y    $REAL
amba4b8unrealn    $UNREAL
amba4b8unrealy    $UNREAL
amba4b9n    $REAL
amba4b9y    $REAL
amba4c6unrealn    $UNREAL
amba4c6unrealy    $UNREAL
amba4c7n    $REAL
amba4c7y    $REAL
amba4f24unrealn    $UNREAL
amba4f24unrealy    $UNREAL
amba4f25n    $REAL
amba4f25y    $REAL
amba5b4unrealn    $UNREAL
amba5b4unrealy    $UNREAL
amba5b5n    $REAL
amba5b5y    $REAL
amba5c4unrealn    $UNREAL
amba5c4unrealy    $UNREAL
amba5c5n    $REAL
amba5c5y    $REAL
amba5f16unrealn    $UNREAL
amba5f16unrealy    $UNREAL
amba5f17n    $REAL
amba5f17y    $REAL
amba6b4unrealn    $UNREAL
amba6b4unrealy    $UNREAL
amba6b5n    $REAL
amba6b5y    $REAL
amba6c4unrealn    $UNREAL
amba6c4unrealy    $UNREAL
amba6c5n    $REAL
amba6c5y    $REAL
amba6f20unrealn    $UNREAL
amba6f20unrealy    $UNREAL
amba6f21n    $REAL
amba6f21y    $REAL
amba7b4unrealn    $UNREAL
amba7b4unrealy    $UNREAL
amba7b5n    $REAL
amba7b5y    $REAL
amba7c4unrealn    $UNREAL
amba7c4unrealy    $UNREAL
amba7c5n    $REAL
amba7c5y    $REAL
amba7f24unrealn    $UNREAL
amba7f24unrealy    $UNREAL
amba7f25n    $REAL
amba7f25y    $REAL
amba8b5unrealn    $UNREAL
amba8b5unrealy    $UNREAL
amba8b6n    $REAL
amba8b6y    $REAL
amba8c6unrealn    $UNREAL
amba8c6unrealy    $UNREAL
amba8c7n    $REAL
amba8c7y    $REAL
amba8f56unrealn    $UNREAL
amba8f56unrealy    $UNREAL
amba8f57n    $REAL
amba8f57y    $REAL
amba9b4unrealn    $UNREAL
amba9b4unrealy    $UNREAL
amba9b5n    $REAL
amba9b5y    $REAL
amba9c4unrealn    $UNREAL
amba9c4unrealy    $UNREAL
amba9c5n    $REAL
amba9c5y    $REAL
amba9f32unrealn    $UNREAL
amba9f32unrealy    $UNREAL
amba9f33n    $REAL
amba9f33y    $REAL
bs128n    $REAL
bs128y    $REAL
bs16n    $REAL
bs16y    $REAL
bs32n    $REAL
bs32y    $REAL
bs64n    $REAL
bs64y    $REAL
bs8n    $REAL
bs8y    $REAL
cnt10n    $REAL
cnt10y    $REAL
cnt11n    $REAL
cnt11y    $REAL
cnt15n    $REAL
cnt15y    $REAL
cnt20n    $REAL
cnt20y    $REAL
cnt25n    $REAL
cnt25y    $REAL
cnt2n    $REAL
cnt2y    $REAL
cnt30n    $REAL
cnt30y    $REAL
cnt3n    $REAL
cnt3y    $REAL
cnt4n    $REAL
cnt4y    $REAL
cnt5n    $REAL
cnt5y    $REAL
cnt6n    $REAL
cnt6y    $REAL
cnt7n    $REAL
cnt7y    $REAL
cnt8n    $REAL
cnt8y    $REAL
cnt9n    $REAL
cnt9y    $REAL
demo-v10_2_REAL    $REAL
demo-v10_5_REAL    $REAL
demo-v11_2_UNREAL    $UNREAL
demo-v11_5_UNREAL    $UNREAL
demo-v12_2_REAL    $REAL
demo-v12_5_REAL    $REAL
demo-v13_2_REAL    $REAL
demo-v13_5_REAL    $REAL
demo-v14_2_REAL    $REAL
demo-v14_5_REAL    $REAL
demo-v15_2_REAL    $REAL
demo-v15_5_REAL    $REAL
demo-v16_2_REAL    $REAL
demo-v16_5_REAL    $REAL
demo-v17_2_REAL    $REAL
demo-v17_5_REAL    $REAL
demo-v18_2_UNREAL    $UNREAL
demo-v18_5_REAL    $REAL
demo-v19_2_REAL    $REAL
demo-v19_5_REAL    $REAL
demo-v1_2_UNREAL    $UNREAL
demo-v1_5_UNREAL    $UNREAL
demo-v20_2_REAL    $REAL
demo-v20_5_REAL    $REAL
demo-v21_2_REAL    $REAL
demo-v21_5_REAL    $REAL
demo-v22_2_REAL    $REAL
demo-v22_5_REAL    $REAL
demo-v23_2_REAL    $REAL
demo-v23_5_REAL    $REAL
demo-v24_2_REAL    $REAL
demo-v24_5_REAL    $REAL
demo-v25_2_UNREAL    $UNREAL
demo-v25_5_UNREAL    $UNREAL
demo-v2_2_UNREAL    $UNREAL
demo-v2_5_UNREAL    $UNREAL
demo-v3_2_REAL    $REAL
demo-v3_5_REAL    $REAL
demo-v4_2_UNREAL    $UNREAL
demo-v4_5_REAL    $REAL
demo-v5_2_REAL    $REAL
demo-v5_5_REAL    $REAL
demo-v6_2_UNREAL    $UNREAL
demo-v6_5_REAL    $REAL
demo-v7_2_REAL    $REAL
demo-v7_5_REAL    $REAL
demo-v8_2_REAL    $REAL
demo-v8_5_REAL    $REAL
demo-v9_2_REAL    $REAL
demo-v9_5_REAL    $REAL
factory_assembly_3x3_1_1errors    $UNREAL
factory_assembly_4x3_1_1errors    $REAL
factory_assembly_5x3_1_0errors    $REAL
factory_assembly_5x3_1_4errors    $REAL
factory_assembly_5x3_1_5errors    $UNREAL
factory_assembly_5x4_1_0errors    $UNREAL
factory_assembly_5x5_2_0errors    $REAL
factory_assembly_5x5_2_10errors    $REAL
factory_assembly_5x5_2_11errors    $UNREAL
factory_assembly_5x5_2_1errors    $REAL
factory_assembly_5x6_2_0errors    $UNREAL
factory_assembly_7x3_1_0errors    $REAL
factory_assembly_7x5_2_0errors    $REAL
factory_assembly_7x5_2_10errors    $REAL
factory_assembly_7x5_2_11errors    $REAL
gb_s2_r2_1_UNREAL    $UNREAL
gb_s2_r2_2_REAL    $REAL
gb_s2_r2_3_REAL    $REAL
gb_s2_r2_4_REAL    $REAL
genbuf10b3unrealn    $UNREAL
genbuf10b3unrealy    $UNREAL
genbuf10b4n    $REAL
genbuf10b4y    $REAL
genbuf10c2unrealn    $UNREAL
genbuf10c2unrealy    $UNREAL
genbuf10c3n    $REAL
genbuf10c3y    $REAL
genbuf10f10n    $REAL
genbuf10f10y    $REAL
genbuf10f9unrealn    $UNREAL
genbuf10f9unrealy    $UNREAL
genbuf11b3unrealn    $UNREAL
genbuf11b3unrealy    $UNREAL
genbuf11b4n    $REAL
genbuf11b4y    $REAL
genbuf11c2unrealn    $UNREAL
genbuf11c2unrealy    $UNREAL
genbuf11c3n    $REAL
genbuf11c3y    $REAL
genbuf11f10unrealn    $UNREAL
genbuf11f10unrealy    $UNREAL
genbuf11f11n    $REAL
genbuf11f11y    $REAL
genbuf12b3unrealn    $UNREAL
genbuf12b3unrealy    $UNREAL
genbuf12b4n    $REAL
genbuf12b4y    $REAL
genbuf12c2unrealn    $UNREAL
genbuf12c2unrealy    $UNREAL
genbuf12c3n    $REAL
genbuf12c3y    $REAL
genbuf12f11unrealn    $UNREAL
genbuf12f11unrealy    $UNREAL
genbuf12f12n    $REAL
genbuf12f12y    $REAL
genbuf13b3unrealn    $UNREAL
genbuf13b3unrealy    $UNREAL
genbuf13b4n    $REAL
genbuf13b4y    $REAL
genbuf13c2unrealn    $UNREAL
genbuf13c2unrealy    $UNREAL
genbuf13c3n    $REAL
genbuf13c3y    $REAL
genbuf13f12unrealn    $UNREAL
genbuf13f12unrealy    $UNREAL
genbuf13f13n    $REAL
genbuf13f13y    $REAL
genbuf14b3unrealn    $UNREAL
genbuf14b3unrealy    $UNREAL
genbuf14b4n    $REAL
genbuf14b4y    $REAL
genbuf14c2unrealn    $UNREAL
genbuf14c2unrealy    $UNREAL
genbuf14c3n    $REAL
genbuf14c3y    $REAL
genbuf14f13unrealn    $UNREAL
genbuf14f13unrealy    $UNREAL
genbuf14f14n    $REAL
genbuf14f14y    $REAL
genbuf15b3unrealn    $UNREAL
genbuf15b3unrealy    $UNREAL
genbuf15b4n    $REAL
genbuf15b4y    $REAL
genbuf15c2unrealn    $UNREAL
genbuf15c2unrealy    $UNREAL
genbuf15c3n    $REAL
genbuf15c3y    $REAL
genbuf15f14unrealn    $UNREAL
genbuf15f14unrealy    $UNREAL
genbuf15f15n    $REAL
genbuf15f15y    $REAL
genbuf16b3unrealn    $UNREAL
genbuf16b3unrealy    $UNREAL
genbuf16b4n    $REAL
genbuf16b4y    $REAL
genbuf16c2unrealn    $UNREAL
genbuf16c2unrealy    $UNREAL
genbuf16c3n    $REAL
genbuf16c3y    $REAL
genbuf16f15unrealn    $UNREAL
genbuf16f15unrealy    $UNREAL
genbuf16f16n    $REAL
genbuf16f16y    $REAL
genbuf1b3unrealn    $UNREAL
genbuf1b3unrealy    $UNREAL
genbuf1b4n    $REAL
genbuf1b4y    $REAL
genbuf1c2unrealn    $UNREAL
genbuf1c2unrealy    $UNREAL
genbuf1c3n    $REAL
genbuf1c3y    $REAL
genbuf1f3unrealn    $UNREAL
genbuf1f3unrealy    $UNREAL
genbuf1f4n    $REAL
genbuf1f4y    $REAL
genbuf2b3unrealn    $UNREAL
genbuf2b3unrealy    $UNREAL
genbuf2b4n    $REAL
genbuf2b4y    $REAL
genbuf2c2unrealn    $UNREAL
genbuf2c2unrealy    $UNREAL
genbuf2c3n    $REAL
genbuf2c3y    $REAL
genbuf2f3unrealn    $UNREAL
genbuf2f3unrealy    $UNREAL
genbuf2f4n    $REAL
genbuf2f4y    $REAL
genbuf3b3unrealn    $UNREAL
genbuf3b3unrealy    $UNREAL
genbuf3b4n    $REAL
genbuf3b4y    $REAL
genbuf3c2unrealn    $UNREAL
genbuf3c2unrealy    $UNREAL
genbuf3c3n    $REAL
genbuf3c3y    $REAL
genbuf3f3unrealn    $UNREAL
genbuf3f3unrealy    $UNREAL
genbuf3f4n    $REAL
genbuf3f4y    $REAL
genbuf4b3unrealn    $UNREAL
genbuf4b3unrealy    $UNREAL
genbuf4b4n    $REAL
genbuf4b4y    $REAL
genbuf4c2unrealn    $UNREAL
genbuf4c2unrealy    $UNREAL
genbuf4c3n    $REAL
genbuf4c3y    $REAL
genbuf4f3unrealn    $UNREAL
genbuf4f3unrealy    $UNREAL
genbuf4f4n    $REAL
genbuf4f4y    $REAL
genbuf5b3unrealn    $UNREAL
genbuf5b3unrealy    $UNREAL
genbuf5b4n    $REAL
genbuf5b4y    $REAL
genbuf5c2unrealn    $UNREAL
genbuf5c2unrealy    $UNREAL
genbuf5c3n    $REAL
genbuf5c3y    $REAL
genbuf5f4unrealn    $UNREAL
genbuf5f4unrealy    $UNREAL
genbuf5f5n    $REAL
genbuf5f5y    $REAL
genbuf6b3unrealn    $UNREAL
genbuf6b3unrealy    $UNREAL
genbuf6b4n    $REAL
genbuf6b4y    $REAL
genbuf6c2unrealn    $UNREAL
genbuf6c2unrealy    $UNREAL
genbuf6c3n    $REAL
genbuf6c3y    $REAL
genbuf6f5unrealn    $UNREAL
genbuf6f5unrealy    $UNREAL
genbuf6f6n    $REAL
genbuf6f6y    $REAL
genbuf7b3unrealn    $UNREAL
genbuf7b3unrealy    $UNREAL
genbuf7b4n    $REAL
genbuf7b4y    $REAL
genbuf7c2unrealn    $UNREAL
genbuf7c2unrealy    $UNREAL
genbuf7c3n    $REAL
genbuf7c3y    $REAL
genbuf7f6unrealn    $UNREAL
genbuf7f6unrealy    $UNREAL
genbuf7f7n    $REAL
genbuf7f7y    $REAL
genbuf8b3unrealn    $UNREAL
genbuf8b3unrealy    $UNREAL
genbuf8b4n    $REAL
genbuf8b4y    $REAL
genbuf8c2unrealn    $UNREAL
genbuf8c2unrealy    $UNREAL
genbuf8c3n    $REAL
genbuf8c3y    $REAL
genbuf8f7unrealn    $UNREAL
genbuf8f7unrealy    $UNREAL
genbuf8f8n    $REAL
genbuf8f8y    $REAL
genbuf9b3unrealn    $UNREAL
genbuf9b3unrealy    $UNREAL
genbuf9b4n    $REAL
genbuf9b4y    $REAL
genbuf9c2unrealn    $UNREAL
genbuf9c2unrealy    $UNREAL
genbuf9c3n    $REAL
genbuf9c3y    $REAL
genbuf9f8unrealn    $UNREAL
genbuf9f8unrealy    $UNREAL
genbuf9f9n    $REAL
genbuf9f9y    $REAL
load_2c_comp_2_REAL    $REAL
load_3c_comp_2_REAL    $REAL
load_full_2_2_REAL    $REAL
load_full_2_5_UNREAL    $UNREAL
load_full_3_2_REAL    $REAL
ltl2dba_01_1_REAL    $REAL
ltl2dba_01_2_REAL    $REAL
ltl2dba_02_1_REAL    $REAL
ltl2dba_02_2_REAL    $REAL
ltl2dba_03_1_REAL    $REAL
ltl2dba_03_2_REAL    $REAL
ltl2dba_04_2_REAL    $REAL
ltl2dba_05_2_REAL    $REAL
ltl2dba_06_2_REAL    $REAL
ltl2dba_07_2_REAL    $REAL
ltl2dba_08_2_REAL    $REAL
ltl2dba_09_2_REAL    $REAL
ltl2dba_10_2_REAL    $REAL
ltl2dba_11_2_REAL    $REAL
ltl2dba_12_2_REAL    $REAL
ltl2dba_13_2_REAL    $REAL
ltl2dba_14_2_REAL    $REAL
ltl2dba_15_2_UNREAL    $UNREAL
ltl2dba_16_2_REAL    $REAL
ltl2dba_17_2_REAL    $REAL
ltl2dba_18_2_REAL    $REAL
ltl2dba_19_2_REAL    $REAL
ltl2dba_20_2_REAL    $REAL
ltl2dpa_01_2_REAL    $REAL
ltl2dpa_02_2_REAL    $REAL
ltl2dpa_03_2_REAL    $REAL
ltl2dpa_04_2_REAL    $REAL
ltl2dpa_05_2_REAL    $REAL
ltl2dpa_06_2_REAL    $REAL
ltl2dpa_07_2_REAL    $REAL
ltl2dpa_08_2_REAL    $REAL
ltl2dpa_09_2_REAL    $REAL
ltl2dpa_10_2_REAL    $REAL
ltl2dpa_11_2_REAL    $REAL
ltl2dpa_12_2_REAL    $REAL
ltl2dpa_13_2_REAL    $REAL
ltl2dpa_14_2_REAL    $REAL
ltl2dpa_15_2_REAL    $REAL
ltl2dpa_16_2_REAL    $REAL
ltl2dpa_17_2_REAL    $REAL
ltl2dpa_18_2_REAL    $REAL
moving_obstacle_128x128_59glitches    $REAL
moving_obstacle_128x128_60glitches    $REAL
moving_obstacle_16x16_3glitches    $REAL
moving_obstacle_16x16_4glitches    $UNREAL
moving_obstacle_24x24_7glitches    $REAL
moving_obstacle_24x24_8glitches    $UNREAL
moving_obstacle_32x32_11glitches    $REAL
moving_obstacle_32x32_12glitches    $UNREAL
moving_obstacle_48x48_19glitches    $REAL
moving_obstacle_48x48_20glitches    $UNREAL
moving_obstacle_64x64_27glitches    $REAL
moving_obstacle_64x64_28glitches    $UNREAL
moving_obstacle_8x8_0glitches    $REAL
moving_obstacle_8x8_1glitches    $UNREAL
moving_obstacle_96x96_43glitches    $REAL
moving_obstacle_96x96_44glitches    $UNREAL
mult10    $REAL
mult11    $REAL
mult12    $REAL
mult13    $REAL
mult14    $REAL
mult15    $REAL
mult16    $REAL
mult2    $REAL
mult4    $REAL
mult5    $REAL
mult6    $REAL
mult7    $REAL
mult8    $REAL
mult9    $REAL
mv10n    $REAL
mv10y    $REAL
mv11n    $REAL
mv11y    $REAL
mv12n    $REAL
mv12y    $REAL
mv14n    $REAL
mv14y    $REAL
mv16n    $REAL
mv16y    $REAL
mv20n    $REAL
mv20y    $REAL
mv2n    $REAL
mv2y    $REAL
mv4n    $REAL
mv4y    $REAL
mv8n    $REAL
mv8y    $REAL
mv9n    $REAL
mv9y    $REAL
mvs12n    $REAL
mvs12y    $REAL
mvs14n    $REAL
mvs14y    $REAL
mvs16n    $REAL
mvs16y    $REAL
mvs18n    $REAL
mvs18y    $REAL
mvs20n    $REAL
mvs20y    $REAL
mvs22n    $REAL
mvs22y    $REAL
mvs24n    $REAL
mvs24y    $REAL
mvs28n    $REAL
mvs28y    $REAL
mvs2n    $REAL
mvs2y    $REAL
mvs4n    $REAL
mvs4y    $REAL
mvs8n    $REAL
mvs8y    $REAL
stay10n    $REAL
stay10y    $REAL
stay12n    $REAL
stay12y    $REAL
stay14n    $REAL
stay14y    $REAL
stay16n    $REAL
stay16y    $REAL
stay18n    $REAL
stay18y    $REAL
stay20n    $REAL
stay20y    $REAL
stay22n    $REAL
stay22y    $REAL
stay24n    $REAL
stay24y    $REAL
stay2n    $REAL
stay2y    $REAL
stay4n    $REAL
stay4y    $REAL
stay6n    $REAL
stay6y    $REAL
stay8n    $REAL
stay8y    $REAL
)

CALL_SYNTH_TOOL="./start abssynthe.py -v L $@ "
TIMESTAMP=`date +%s`
RES_TXT_FILE="${DIR}tests/results_${TIMESTAMP}.txt"
RES_DIR="${DIR}tests/results_${TIMESTAMP}/"
mkdir -p "${DIR}tests/"
mkdir -p ${RES_DIR}

ulimit -m ${MEMORY_LIMIT} -v ${MEMORY_LIMIT} -t ${TIME_LIMIT}
for element in $(seq 0 2 $((${#FILES[@]} - 1)))
do
     file_name=${FILES[$element]}
     infile_path=${BM_DIR}${file_name}.aag
     outfile_path=${RES_DIR}${file_name}_synth.aag
     correct_real=${FILES[$element+1]}
     echo "Synthesizing ${file_name}.aag ..."
     echo "=====================  $file_name.aag =====================" 1>> $RES_TXT_FILE

     #------------------------------------------------------------------------------
     # BEGIN execution of synthesis tool
     echo " Running the synthesizer ... "
     ${GNU_TIME} --output=${RES_TXT_FILE} -a -f "Synthesis time: %e sec (Real time) / %U sec (User CPU time)" ${CALL_SYNTH_TOOL} $infile_path >> ${RES_TXT_FILE}
     #"-o" $outfile_path "-ot" >> ${RES_TXT_FILE}
     exit_code=$?
     echo "  Done running the synthesizer. "
     # END execution of synthesis tool

     if [[ $exit_code == 137 ]];
     then
         echo "  Timeout!"
         echo "Timeout: 1" 1>> $RES_TXT_FILE
         continue
     else
         echo "Timeout: 0" 1>> $RES_TXT_FILE
     fi

     if [[ $exit_code != $REAL && $exit_code != $UNREAL ]];
     then
         echo "  Strange exit code: $exit_code (crash or out-of-memory)!"
         echo "Crash or out-of-mem: 1 (Exit code: $exit_code)" 1>> $RES_TXT_FILE
         continue
     else
         echo "Crash or out-of-mem: 0" 1>> $RES_TXT_FILE
     fi

     #------------------------------------------------------------------------------
     # BEGIN analyze realizability verdict
#     if [[ $exit_code == $REAL && $correct_real == $UNREAL ]];
#     then
#         echo "  ERROR: Tool reported 'realizable' for an unrealizable spec!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
#         echo "Realizability correct: 0 (tool reported 'realizable' instead of 'unrealizable')" 1>> $RES_TXT_FILE
#         continue
#     fi
#     if [[ $exit_code == $UNREAL && $correct_real == $REAL ]];
#     then
#         echo "  ERROR: Tool reported 'unrealizable' for a realizable spec!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
#         echo "Realizability correct: 0 (tool reported 'unrealizable' instead of 'realizable')" 1>> $RES_TXT_FILE
#         continue
#     fi
     if [[ $exit_code == $UNREAL ]];
     then
         echo "  The spec has been correctly identified as 'unrealizable'."
         echo "Realizability correct: 1 (unrealizable)" 1>> $RES_TXT_FILE
     else
         echo "  The spec has been correctly identified as 'realizable'."
         echo "Realizability correct: 1 (realizable)" 1>> $RES_TXT_FILE
#
#         # END analyze realizability verdict
#
#         #------------------------------------------------------------------------------
#         # BEGIN syntactic check
#         echo " Checking the synthesis result syntactically ... "
#         if [ -f $outfile_path ];
#         then
#             echo "  Output file has been created."
#             python $SYNT_CHECKER $infile_path $outfile_path
#             exit_code=$?
#             if [[ $exit_code == 0 ]];
#             then
#               echo "  Output file is OK syntactically."
#               echo "Output file OK: 1" 1>> $RES_TXT_FILE
#             else
#               echo "  Output file is NOT OK syntactically."
#               echo "Output file OK: 0" 1>> $RES_TXT_FILE
#             fi
#         else
#             echo "  Output file has NOT been created!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
#             echo "Output file OK: 0 (no output file created)" 1>> $RES_TXT_FILE
#             continue
#         fi
#         # TODO: perform syntactic check here.
#         # END syntactic check
#
#         #------------------------------------------------------------------------------
#         # BEGIN model checking
#         echo -n " Model checking the synthesis result ... "
#         ${GNU_TIME} --output=${RES_TXT_FILE} -a -f "Model-checking time: %e sec (Real time) / %U sec (User CPU time)" $MODEL_CHECKER $outfile_path > /dev/null 2>&1
#         check_res=$?
#         echo " done. "
#         if [[ $check_res == 20 ]];
#         then
#             echo "  Model-checking was successful."
#             echo "Model-checking: 1" 1>> $RES_TXT_FILE
#         else
#             echo "  Model-checking the resulting circuit failed!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
#             echo "Model-checking: 0 (exit code: $check_res)" 1>> $RES_TXT_FILE
#         fi
#         # END end checking
#
#         #------------------------------------------------------------------------------
         # BEGIN determining circuit size
#         aig_header_in=$(head -n 1 $infile_path)
#         aig_header_out=$(head -n 1 $outfile_path)
#         echo "Raw AIGER input size: $aig_header_in" 1>> $RES_TXT_FILE
#         echo "Raw AIGER output size: $aig_header_out" 1>> $RES_TXT_FILE
#         # START ABC optimization to compare sizes
#         ../aiger/aigtoaig $outfile_path "${outfile_path}.aig"
#         ../ABC/abc -c "read_aiger ${outfile_path}.aig; strash; refactor; rewrite; dfraig; scleanup; rewrite; dfraig; write_aiger -s ${outfile_path}_opt.aig"
#         ../aiger/aigtoaig "${outfile_path}_opt.aig" "${outfile_path}_opt.aag"
#         aig_header_opt=$(head -n 1 "${outfile_path}_opt.aag")
#         echo "Raw AIGER opt size: $aig_header_opt" 1>> $RES_TXT_FILE
#         # END determining circuit size           
     fi
done
