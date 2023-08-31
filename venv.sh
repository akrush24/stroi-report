#!/bin/bash
set -ex
python3 -m venv ./venv
source ./venv/bin/activate
if [[ ${1} == '-i' ]]; then
  shift
  python3 -m pip install --upgrade pip
  pip3 install -r ./requirements.txt
fi
./run.me ${1}
