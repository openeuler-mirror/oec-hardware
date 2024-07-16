# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2024 Intel Corporation
# @Author   yi.sun@intel.com

#/bin/bash

#CUR_PATH="${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}")"
CUR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR_CONFIG_AVOCADO=/root/.config/avocado

PKG_CPUID=https://dl.fedoraproject.org/pub/epel/9/Everything/x86_64/Packages/c/cpuid-20230614-2.el9.x86_64.rpm
PKG_MSR_TOOLS=https://mirror.centos.no/epel/9/Everything/x86_64/Packages/m/msr-tools-1.3-17.el9.x86_64.rpm

REPO_IDXD_CONFIG=https://github.com/intel/idxd-config.git
REPO_LKVS=https://gitee.com/openeuler/intel-lkvs.git
CONFIG_AVOCADO=$DIR_CONFIG_AVOCADO/avocado.conf

URL_KERNEL6=https://kernel.org/pub/linux/kernel/v6.x
DIR_TURBOSTAT=linux-6.10/tools/power/x86/turbostat
DIR_CPUPOWER=linux-6.10/tools/power/cpupower

TAR_KERNEL_610=linux-6.10.tar.xz
BIN_STRESS=/usr/local/bin/stress

# Define error handler function
handle_error() {
    echo "[Error] $BASH_SOURCE at line: $1"
    exit 1
}

# trap exception call error handler
trap 'handle_error $LINENO' ERR

#pip install git+https://github.com/avocado-framework/avocado
pip3 install avocado-framework || let ret+=$?

mkdir -p $DIR_CONFIG_AVOCADO
cat > $CONFIG_AVOCADO <<EOF
[run]
max_parallel_tasks=1
EOF

rm -rf lkvs && git clone $REPO_LKVS lkvs
cd lkvs && git fetch origin --tags --force && git reset --hard emr-oe
cd -

rm -rf idxd-config && git clone $REPO_IDXD_CONFIG
cd idxd-config
./autogen.sh && ./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64 --enable-test=yes
make -j16
make install
cd -

yum install -y $PKG_MSR_TOOLS $PKG_CPUID

[ ! -f $BIN_STRESS ] && ln -s `which stress-ng` $BIN_STRESS

rm -rf $TAR_KERNEL_610 && wget $URL_KERNEL6/$TAR_KERNEL_610

tar xvf $TAR_KERNEL_610
cd $CUR_DIR/$DIR_CPUPOWER && make && make install
cd $CUR_DIR/$DIR_TURBOSTAT && make && make install

## Install dependent packages here
$CUR_DIR/lkvs/BM/instruction-check/setup.sh
