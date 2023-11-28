#!/usr/bin/bash
# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @meitingli
# Create: 2022-05-05
# Desc: Shell script used for testing nvidia gpu

cuda_version=$(nvidia-smi -q | grep "CUDA Version" | awk '{print $4}')
cuda_name="cuda-samples-${cuda_version}"

function install_gpu_burn() {
    cd /opt
    res_code=0
    if [ ! -d gpu-burn ]; then
        git clone https://github.com/wilicc/gpu-burn.git
    fi
    cd gpu-burn
    lsmod | grep bi_driver >/dev/null
    if [ $? -eq 0 ]; then
        COREX_PATH=${COREX_PATH:-/usr/local/corex}
        clang++ compare.cu -o compare.ll -I${COREX_PATH}/include --cuda-gpu-arch=ivcore10 --cuda-path=${COREX_PATH} --cuda-device-only -S -x cuda || res_code=1
        llc -mcpu=ivcore10 -mtriple=bi-iluvatar-ilurt -show-mc-encoding -filetype=obj compare.ll -o compare.o || res_code=1
        lld -flavor ld.lld --no-undefined compare.o -o compare.ptx || res_code=1
        rm compare.ll compare.o
        sed -i '/cuFuncSet/d' gpu_burn-drv.cpp
        sed -i '/cuParamSet/d' gpu_burn-drv.cpp
        sed -i 's/nvidia-smi/ixsmi/g' gpu_burn-drv.cpp
        sed -i 's/.*cuLaunchGridAsync.*/void\* kargs[] = {\&d_Cdata, \&d_faultyElemData, \&d_iters};checkError(cuLaunchKernel(d_function, SIZE\/g_blockSize, SIZE\/g_blockSize, 1, g_blockSize, g_blockSize, 1, 0, 0, kargs, nullptr));/g' gpu_burn-drv.cpp
        clang++ -std=c++11 -I${COREX_PATH}/include -L${COREX_PATH}/lib64 -lcudart -lcuda -lcublas -o gpu_burn ./gpu_burn-drv.cpp || res_code=1
    else
        make &>/dev/null || res_code=1
    fi
    return $res_code
}

function install_cuda_samples() {
    cd /opt
    if [ ! -d ${cuda_name} ]; then
        wget https://github.com/NVIDIA/cuda-samples/archive/refs/tags/v${cuda_version}.zip
        unzip v${cuda_version}.zip >/dev/null
        rm -rf v${cuda_version}.zip
    fi
    return 0
}

function test_nvidia_case() {
    casename=$1
    logfile=$2
    res_code=0
    cd /opt/${cuda_name}
    path=$(find ./ -name $casename -type d)
    cd $path
    make &>/dev/null
    ./$casename &>>$logfile
    if [[ $? -eq 0 ]]; then
        echo "Test $casename succeed." >>$logfile
    else
        echo "Test $casename failed." >>$logfile
        res_code=1
    fi
    return $res_code
}

function test_iluvatar_case() {
    casename=$1
    logfile=$2
    res_code=0
    CUDA_PATH=${CUDA_PATH:-/usr/local/corex}
    cd /opt/${cuda_name}
    path=$(find ./ -name $casename)
    cd $path
    src_file=${casename}.cu
    if [ ! -f ./$src_file ] && [ -f ./${casename}.cpp ]; then
        src_file=${casename}.cpp
    fi
    clang++ -std=c++11 -I../../../Common -I${CUDA_PATH}/include --cuda-path=${CUDA_PATH} -L${CUDA_PATH}/lib64 -lcudart -lixlogger -lcuda -lixthunk -o ${casename} ./${src_file}
    ./$casename &>>$logfile
    if [[ $? -eq 0 ]]; then
        echo "Test $casename succeed."
    else
        echo "Test $casename failed."
        res_code=1
    fi
    return $res_code
}

function test_cuda_samples() {
    logfile=$1
    allcases=(${2//,/ })
    res_code=0
    install_cuda_samples
    cd /opt/${cuda_name}
    lsmod | grep bi_driver
    if [[ $? -eq 0 ]]; then
        for casename in ${allcases[@]}; do
            test_iluvatar_case $casename $logfile
            if [[ $? -eq 1 ]]; then
                res_code=1
            fi
        done
    else
        for casename in ${allcases[@]}; do
            test_nvidia_case $casename $logfile
            if [[ $? -eq 1 ]]; then
                res_code=1
            fi
        done
    fi
    return $res_code
}

function main() {
    func_name=$1
    param_list=$2

    if [[ $func_name == "install_gpu_burn" ]]; then
        install_gpu_burn
    elif [[ $func_name == "install_cuda_samples" ]]; then
        install_cuda_samples
    elif [[ $func_name == "test_cuda_samples" ]]; then
        test_cuda_samples $param_list
    else
        echo "The function doesn't exist, please check!"
        return 1
    fi
}

main "$@"
