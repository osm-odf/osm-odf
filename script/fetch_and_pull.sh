#!/bin/bash

# before you run this, you gotta go into osm-minutely-changes, run 
# python -m venv .venv
# pip install -r requirements.txt
# source .venv/bin/activate

source ../osm-minutely-changes/.venv/bin/activate
python ../osm-minutely-changes/consumer.py

cd ../data/berlin
kamu pull --all