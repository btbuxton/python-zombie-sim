#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
echo $DIR
cd $DIR/..
export PYTHONPATH=$(pwd)
python zombiesim/main.py
