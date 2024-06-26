# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2024 Intel Corporation
# @Author   yi.sun@intel.com

#/bin/bash

pip install avocado
#pip install git+https://github.com/avocado-framework/avocado

if [ ! -d lkvs ]; then
  git clone https://gitee.com/openeuler/intel-lkvs.git
fi

cd lkvs
git fetch origin --tags && git reset --hard emr-oe

## Install dependent packages here
./BM/instruction-check/setup.sh

