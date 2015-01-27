#!/bin/bash

# This directory:
DIR=`dirname $0`/

# The directory where the benchmarks are located:
BM_DIR="\$HOME/bench-syntcomp14/"

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
amba8b6n    $UNREAL
amba8b6y    $UNREAL
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
gb_s2_r2_comp1_UNREAL   $UNREAL
gb_s2_r2_comp2_UNREAL   $UNREAL
gb_s2_r2_comp3_REAL   $REAL
gb_s2_r2_comp4_REAL   $REAL
gb_s2_r2_comp5_REAL   $REAL
gb_s2_r2_comp6_REAL   $REAL
gb_s2_r2_comp7_REAL   $REAL
gb_s2_r3_comp1_UNREAL   $UNREAL
gb_s2_r3_comp2_UNREAL   $UNREAL
gb_s2_r3_comp3_REAL   $REAL
gb_s2_r3_comp4_REAL   $REAL
gb_s2_r3_comp5_REAL   $REAL
gb_s2_r3_comp6_REAL   $REAL
gb_s2_r3_comp7_REAL   $REAL
gb_s2_r4_comp1_UNREAL   $UNREAL
gb_s2_r4_comp2_REAL   $REAL
gb_s2_r4_comp3_REAL   $REAL
gb_s2_r4_comp4_REAL   $REAL
gb_s2_r4_comp5_REAL   $REAL
gb_s2_r4_comp6_REAL   $REAL
gb_s2_r4_comp7_REAL   $REAL
gb_s2_r5_comp1_UNREAL   $UNREAL
gb_s2_r5_comp2_UNREAL   $UNREAL
gb_s2_r5_comp3_REAL   $REAL
gb_s2_r5_comp4_REAL   $REAL
gb_s2_r5_comp5_REAL   $REAL
gb_s2_r5_comp6_REAL   $REAL
gb_s2_r5_comp7_REAL   $REAL
gb_s2_r6_comp1_UNREAL   $UNREAL
gb_s2_r6_comp2_UNREAL   $UNREAL
gb_s2_r6_comp3_REAL   $REAL
gb_s2_r6_comp4_REAL   $REAL
gb_s2_r6_comp5_REAL   $REAL
gb_s2_r6_comp6_REAL   $REAL
gb_s2_r6_comp7_REAL   $REAL
gb_s2_r7_comp1_UNREAL   $UNREAL
gb_s2_r7_comp2_REAL   $REAL
gb_s2_r7_comp3_REAL   $REAL
gb_s2_r7_comp4_REAL   $REAL
gb_s2_r7_comp5_REAL   $REAL
gb_s2_r7_comp6_REAL   $REAL
gb_s2_r7_comp7_REAL   $REAL
load_full_2_comp1_UNREAL   $UNREAL
load_full_2_comp2_REAL   $REAL
load_full_2_comp3_REAL   $REAL
load_full_2_comp4_REAL   $REAL
load_full_2_comp5_REAL   $REAL
load_full_2_comp6_REAL   $REAL
load_full_2_comp7_REAL   $REAL
load_full_3_comp1_UNREAL   $UNREAL
load_full_3_comp2_REAL   $REAL
load_full_3_comp3_REAL   $REAL
load_full_3_comp4_REAL   $REAL
load_full_3_comp5_REAL   $REAL
load_full_3_comp6_REAL   $REAL
load_full_3_comp7_REAL   $REAL
load_full_4_comp1_REAL   $REAL
load_full_4_comp2_REAL   $REAL
load_full_4_comp3_REAL   $REAL
load_full_4_comp4_REAL   $REAL
load_full_4_comp5_REAL   $REAL
load_full_4_comp6_REAL   $REAL
load_full_4_comp7_REAL   $REAL
load_full_5_comp1_REAL   $REAL
load_full_5_comp2_REAL   $REAL
load_full_5_comp3_REAL   $REAL
load_full_5_comp4_REAL   $REAL
load_full_5_comp5_REAL   $REAL
load_full_5_comp6_REAL   $REAL
load_full_5_comp7_REAL   $REAL
load_full_6_comp1_UNREAL   $UNREAL
load_full_6_comp2_REAL   $REAL
load_full_6_comp3_REAL   $REAL
load_full_6_comp4_REAL   $REAL
load_full_6_comp5_REAL   $REAL
load_full_6_comp6_REAL   $REAL
load_full_6_comp7_REAL   $REAL
load_2c_comp_comp1_REAL   $REAL
load_2c_comp_comp2_REAL   $REAL
load_2c_comp_comp3_REAL   $REAL
load_2c_comp_comp4_REAL   $REAL
load_2c_comp_comp5_REAL   $REAL
load_2c_comp_comp6_REAL   $REAL
load_2c_comp_comp7_REAL   $REAL
load_3c_comp_comp1_REAL   $REAL
load_3c_comp_comp2_REAL   $REAL
load_3c_comp_comp3_REAL   $REAL
load_3c_comp_comp4_REAL   $REAL
load_3c_comp_comp5_REAL   $REAL
load_3c_comp_comp6_REAL   $REAL
load_3c_comp_comp7_REAL   $REAL
load_4c_comp_comp1_UNREAL   $UNREAL
load_4c_comp_comp2_REAL   $REAL
load_4c_comp_comp3_REAL   $REAL
load_4c_comp_comp4_REAL   $REAL
load_4c_comp_comp5_REAL   $REAL
load_4c_comp_comp6_REAL   $REAL
load_4c_comp_comp7_REAL   $REAL
load_5c_comp_comp1_UNREAL   $UNREAL
load_5c_comp_comp2_UNREAL   $UNREAL
load_5c_comp_comp3_UNREAL   $UNREAL
load_5c_comp_comp4_REAL   $REAL
load_5c_comp_comp5_REAL   $REAL
load_5c_comp_comp6_REAL   $REAL
load_5c_comp_comp7_REAL   $REAL
)

DECOMPABLE=(
amba10b4unrealn     
amba10b4unrealy     
amba10b5n           
amba10b5y           
amba10c4unrealn     
amba10c4unrealy     
amba10c5n           
amba10c5y           
amba10f36unrealn    
amba10f36unrealy    
amba10f37n          
amba10f37y          
amba2b8unrealn      
amba2b8unrealy      
amba2b9n            
amba2b9y            
amba2c6unrealn      
amba2c6unrealy      
amba2c7n            
amba2c7y            
amba2f8unrealn      
amba2f8unrealy      
amba2f9n            
amba2f9y            
amba3b4unrealn      
amba3b4unrealy      
amba3b5n            
amba3b5y            
amba3c4unrealn      
amba3c4unrealy      
amba3c5n            
amba3c5y            
amba3f8unrealn      
amba3f8unrealy      
amba3f9n            
amba3f9y            
amba4b8unrealn      
amba4b8unrealy      
amba4b9n            
amba4b9y            
amba4c6unrealn      
amba4c6unrealy      
amba4c7n            
amba4c7y            
amba4f24unrealn     
amba4f24unrealy     
amba4f25n           
amba4f25y           
amba5b4unrealn      
amba5b4unrealy      
amba5b5n            
amba5b5y            
amba5c4unrealn      
amba5c4unrealy      
amba5c5n            
amba5c5y            
amba5f16unrealn     
amba5f16unrealy     
amba5f17n           
amba5f17y           
amba6b4unrealn      
amba6b4unrealy      
amba6b5n            
amba6b5y            
amba6c4unrealn      
amba6c4unrealy      
amba6c5n            
amba6c5y            
amba6f20unrealn     
amba6f20unrealy     
amba6f21n           
amba6f21y           
amba7b4unrealn      
amba7b4unrealy      
amba7b5n            
amba7b5y            
amba7c4unrealn      
amba7c4unrealy      
amba7c5n            
amba7c5y            
amba7f24unrealn     
amba7f24unrealy     
amba7f25n           
amba7f25y           
amba8b5unrealn      
amba8b5unrealy      
amba8b6n            
amba8b6y            
amba8c6unrealn      
amba8c6unrealy      
amba8c7n            
amba8c7y            
amba8f56unrealn     
amba8f56unrealy     
amba8f57n           
amba8f57y           
amba9b4unrealn      
amba9b4unrealy      
amba9b5n            
amba9b5y            
amba9c4unrealn      
amba9c4unrealy      
amba9c5n            
amba9c5y            
amba9f32unrealn     
amba9f32unrealy     
amba9f33n           
amba9f33y           
demo-v12_5_REAL     
demo-v17_2_REAL     
demo-v18_2_UNREAL   
demo-v18_5_REAL     
demo-v1_2_UNREAL    
demo-v1_5_UNREAL    
demo-v21_5_REAL     
demo-v25_2_UNREAL   
demo-v25_5_UNREAL   
demo-v5_2_REAL      
demo-v5_5_REAL      
factory_assembly_5x5_2_0errors
factory_assembly_5x5_2_10errors
factory_assembly_5x5_2_11errors
factory_assembly_5x5_2_1errors
factory_assembly_5x6_2_0errors
factory_assembly_7x5_2_0errors
factory_assembly_7x5_2_10errors
factory_assembly_7x5_2_11errors
gb_s2_r2_1_UNREAL   
gb_s2_r2_2_REAL     
gb_s2_r2_3_REAL     
gb_s2_r2_4_REAL     
genbuf10b3unrealn   
genbuf10b3unrealy   
genbuf10b4n         
genbuf10b4y         
genbuf10c2unrealn   
genbuf10c2unrealy   
genbuf10c3n         
genbuf10c3y         
genbuf10f10n        
genbuf10f10y        
genbuf10f9unrealn   
genbuf10f9unrealy   
genbuf11b3unrealn   
genbuf11b3unrealy   
genbuf11b4n         
genbuf11b4y         
genbuf11c2unrealn   
genbuf11c2unrealy   
genbuf11c3n         
genbuf11c3y         
genbuf11f10unrealn  
genbuf11f10unrealy  
genbuf11f11n        
genbuf11f11y        
genbuf12b3unrealn   
genbuf12b3unrealy   
genbuf12b4n         
genbuf12b4y         
genbuf12c2unrealn   
genbuf12c2unrealy   
genbuf12c3n         
genbuf12c3y         
genbuf12f11unrealn  
genbuf12f11unrealy  
genbuf12f12n        
genbuf12f12y        
genbuf13b3unrealn   
genbuf13b3unrealy   
genbuf13b4n         
genbuf13b4y         
genbuf13c2unrealn   
genbuf13c2unrealy   
genbuf13c3n         
genbuf13c3y         
genbuf13f12unrealn  
genbuf13f12unrealy  
genbuf13f13n        
genbuf13f13y        
genbuf14b3unrealn   
genbuf14b3unrealy   
genbuf14b4n         
genbuf14b4y         
genbuf14c2unrealn   
genbuf14c2unrealy   
genbuf14c3n         
genbuf14c3y         
genbuf14f13unrealn  
genbuf14f13unrealy  
genbuf14f14n        
genbuf14f14y        
genbuf15b3unrealn   
genbuf15b3unrealy   
genbuf15b4n         
genbuf15b4y         
genbuf15c2unrealn   
genbuf15c2unrealy   
genbuf15c3n         
genbuf15c3y         
genbuf15f14unrealn  
genbuf15f14unrealy  
genbuf15f15n        
genbuf15f15y        
genbuf16b3unrealn   
genbuf16b3unrealy   
genbuf16b4n         
genbuf16b4y         
genbuf16c2unrealn   
genbuf16c2unrealy   
genbuf16c3n         
genbuf16c3y         
genbuf16f15unrealn  
genbuf16f15unrealy  
genbuf16f16n        
genbuf16f16y        
genbuf1b3unrealn    
genbuf1b3unrealy    
genbuf1b4n          
genbuf1b4y          
genbuf1c2unrealn    
genbuf1c2unrealy    
genbuf1c3n          
genbuf1c3y          
genbuf1f3unrealn    
genbuf1f3unrealy    
genbuf1f4n          
genbuf1f4y          
genbuf2b3unrealn    
genbuf2b3unrealy    
genbuf2b4n          
genbuf2b4y          
genbuf2c2unrealn    
genbuf2c2unrealy    
genbuf2c3n          
genbuf2c3y          
genbuf2f3unrealn    
genbuf2f3unrealy    
genbuf2f4n          
genbuf2f4y          
genbuf3b3unrealn    
genbuf3b3unrealy    
genbuf3b4n          
genbuf3b4y          
genbuf3c2unrealn    
genbuf3c2unrealy    
genbuf3c3n          
genbuf3c3y          
genbuf3f3unrealn    
genbuf3f3unrealy    
genbuf3f4n          
genbuf3f4y          
genbuf4b3unrealn    
genbuf4b3unrealy    
genbuf4b4n          
genbuf4b4y          
genbuf4c2unrealn    
genbuf4c2unrealy    
genbuf4c3n          
genbuf4c3y          
genbuf4f3unrealn    
genbuf4f3unrealy    
genbuf4f4n          
genbuf4f4y          
genbuf5b3unrealn    
genbuf5b3unrealy    
genbuf5b4n          
genbuf5b4y          
genbuf5c2unrealn    
genbuf5c2unrealy    
genbuf5c3n          
genbuf5c3y          
genbuf5f4unrealn    
genbuf5f4unrealy    
genbuf5f5n          
genbuf5f5y          
genbuf6b3unrealn    
genbuf6b3unrealy    
genbuf6b4n          
genbuf6b4y          
genbuf6c2unrealn    
genbuf6c2unrealy    
genbuf6c3n          
genbuf6c3y          
genbuf6f5unrealn    
genbuf6f5unrealy    
genbuf6f6n          
genbuf6f6y          
genbuf7b3unrealn    
genbuf7b3unrealy    
genbuf7b4n          
genbuf7b4y          
genbuf7c2unrealn    
genbuf7c2unrealy    
genbuf7c3n          
genbuf7c3y          
genbuf7f6unrealn    
genbuf7f6unrealy    
genbuf7f7n          
genbuf7f7y          
genbuf8b3unrealn    
genbuf8b3unrealy    
genbuf8b4n          
genbuf8b4y          
genbuf8c2unrealn    
genbuf8c2unrealy    
genbuf8c3n          
genbuf8c3y          
genbuf8f7unrealn    
genbuf8f7unrealy    
genbuf8f8n          
genbuf8f8y          
genbuf9b3unrealn    
genbuf9b3unrealy    
genbuf9b4n          
genbuf9b4y          
genbuf9c2unrealn    
genbuf9c2unrealy    
genbuf9c3n          
genbuf9c3y          
genbuf9f8unrealn    
genbuf9f8unrealy    
genbuf9f9n          
genbuf9f9y          
ltl2dba_01_1_REAL   
ltl2dba_07_2_REAL   
ltl2dba_12_2_REAL   
ltl2dba_19_2_REAL   
ltl2dba_20_2_REAL   
ltl2dpa_10_2_REAL   
ltl2dpa_12_2_REAL   
ltl2dpa_17_2_REAL   
ltl2dpa_18_2_REAL   
moving_obstacle_128x128_59glitches
moving_obstacle_128x128_60glitches
moving_obstacle_32x32_11glitches
moving_obstacle_48x48_19glitches
moving_obstacle_48x48_20glitches
moving_obstacle_64x64_27glitches
moving_obstacle_96x96_43glitches
moving_obstacle_96x96_44glitches
gb_s2_r2_comp1_UNREAL
gb_s2_r2_comp2_UNREAL
gb_s2_r2_comp3_REAL 
gb_s2_r2_comp4_REAL 
gb_s2_r2_comp5_REAL 
gb_s2_r2_comp6_REAL 
gb_s2_r2_comp7_REAL 
gb_s2_r3_comp1_UNREAL
gb_s2_r3_comp2_UNREAL
gb_s2_r3_comp3_REAL 
gb_s2_r3_comp4_REAL 
gb_s2_r3_comp5_REAL 
gb_s2_r3_comp6_REAL 
gb_s2_r3_comp7_REAL 
gb_s2_r4_comp1_UNREAL
gb_s2_r4_comp2_REAL 
gb_s2_r4_comp3_REAL 
gb_s2_r4_comp4_REAL 
gb_s2_r4_comp5_REAL 
gb_s2_r4_comp6_REAL 
gb_s2_r4_comp7_REAL 
gb_s2_r5_comp1_UNREAL
gb_s2_r5_comp2_UNREAL
gb_s2_r5_comp3_REAL 
gb_s2_r5_comp4_REAL 
gb_s2_r5_comp5_REAL 
gb_s2_r5_comp6_REAL 
gb_s2_r5_comp7_REAL 
gb_s2_r6_comp1_UNREAL
gb_s2_r6_comp2_UNREAL
gb_s2_r6_comp3_REAL 
gb_s2_r6_comp4_REAL 
gb_s2_r6_comp5_REAL 
gb_s2_r6_comp6_REAL 
gb_s2_r6_comp7_REAL 
gb_s2_r7_comp1_UNREAL
gb_s2_r7_comp2_REAL 
gb_s2_r7_comp3_REAL 
gb_s2_r7_comp4_REAL 
gb_s2_r7_comp5_REAL 
gb_s2_r7_comp6_REAL 
gb_s2_r7_comp7_REAL 
load_full_2_comp1_UNREAL
load_full_2_comp2_REAL
load_full_2_comp3_REAL
load_full_2_comp4_REAL
load_full_2_comp5_REAL
load_full_2_comp6_REAL
load_full_2_comp7_REAL
load_full_3_comp1_UNREAL
load_full_3_comp2_REAL
load_full_3_comp3_REAL
load_full_3_comp4_REAL
load_full_3_comp5_REAL
load_full_3_comp6_REAL
load_full_3_comp7_REAL
load_full_4_comp1_REAL
load_full_4_comp2_REAL
load_full_4_comp3_REAL
load_full_4_comp4_REAL
load_full_4_comp5_REAL
load_full_4_comp6_REAL
load_full_4_comp7_REAL
load_full_5_comp1_REAL
load_full_5_comp2_REAL
load_full_5_comp3_REAL
load_full_5_comp4_REAL
load_full_5_comp5_REAL
load_full_5_comp6_REAL
load_full_5_comp7_REAL
load_full_6_comp1_UNREAL
load_full_6_comp2_REAL
load_full_6_comp3_REAL
load_full_6_comp4_REAL
load_full_6_comp5_REAL
load_full_6_comp6_REAL
load_full_6_comp7_REAL
load_2c_comp_comp1_REAL
load_2c_comp_comp2_REAL
load_2c_comp_comp3_REAL
load_2c_comp_comp4_REAL
load_2c_comp_comp5_REAL
load_2c_comp_comp6_REAL
load_2c_comp_comp7_REAL
load_3c_comp_comp1_REAL
load_3c_comp_comp2_REAL
load_3c_comp_comp3_REAL
load_3c_comp_comp4_REAL
load_3c_comp_comp5_REAL
load_3c_comp_comp6_REAL
load_3c_comp_comp7_REAL
load_4c_comp_comp1_UNREAL
load_4c_comp_comp2_REAL
load_4c_comp_comp3_REAL
load_4c_comp_comp4_REAL
load_4c_comp_comp5_REAL
load_4c_comp_comp6_REAL
load_4c_comp_comp7_REAL
load_5c_comp_comp1_UNREAL
load_5c_comp_comp2_UNREAL
load_5c_comp_comp3_UNREAL
load_5c_comp_comp4_REAL
load_5c_comp_comp5_REAL
load_5c_comp_comp6_REAL
load_5c_comp_comp7_REAL
)

for element in $(seq 0 2 $((${#FILES[@]} - 1)))
do
     for de in $(seq 0 1 $((${#DECOMPABLE[@]} - 1)))
     do
     if [[ ${FILES[$element]} == ${DECOMPABLE[$de]} ]]; then
	     file_name=${FILES[$element]}
	     infile_path=${BM_DIR}${file_name}.aag
	     correct_real=${FILES[$element+1]}
		for solver in $(seq 0 1 4)
		do
			echo "\$HOME/AbsSynthe/start_co"$solver".sh" $infile_path $correct_real >> ${DIR}"jobs.list"
		done
     		break
     fi
     done
done
