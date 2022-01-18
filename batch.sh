#!/bin/bash

# move to script's directory
cd `dirname $0`


DATA_DIR='data'
ITEM_XLSX='items.xlsx'
MATERIAL_XLSX='materials.xlsx'

RESULT_DIR='results'
mkdir -p $RESULT_DIR


# xlsx to csv
echo 'converting xlsx to csv'
xlsx2csv -s 1 $DATA_DIR/$ITEM_XLSX $RESULT_DIR/items.csv
xlsx2csv -s 1 $DATA_DIR/$MATERIAL_XLSX $RESULT_DIR/materials.csv

# calculate profits
echo 'calculating profits'
python calc_profit.py $RESULT_DIR/items.csv $RESULT_DIR/materials.csv > $RESULT_DIR/profit.tsv 2> errorlog.txt

# convert character set
iconv -f UTF-8 -t CP932 $RESULT_DIR/profit.tsv -o $RESULT_DIR/profit_cp932.tsv

