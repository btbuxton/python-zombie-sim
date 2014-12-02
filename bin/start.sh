#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
echo $DIR
cd $DIR/..
python2.7 zombiesim/main.py
