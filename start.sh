#!/bin/sh

BASEDIR=$(dirname $0)
cd $BASEDIR &&
pip install -r requirements.txt &&
python igg.py
