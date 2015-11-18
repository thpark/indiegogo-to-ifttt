#!/bin/sh

BASEDIR=$(dirname $0)
cd $BASEDIR &&
sudo pip install -r requirements.txt &&
python igg.py
