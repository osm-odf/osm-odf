#!/bin/bash

source ../osm-minutely-changes/.venv/bin/activate
python ../osm-minutely-changes/consumer.py

cd ../data/berlin
kamu pull --all