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

function install_gpu_burn() {
    cd /opt
    git clone https://github.com/wilicc/gpu-burn.git
    cd gpu-burn
    make &>/dev/null
    return 0
}

function install_cuda_samples() {
    cd /opt
    wget https://github.com/NVIDIA/cuda-samples/archive/refs/heads/master.zip
    unzip master.zip >/dev/null
    rm -rf master.zip
    return 0
}

function test_nvidia_case() {
    casename=$1
    logfile=$2
    res_code=0
    cd /opt/cuda-samples-master
    path=$(find ./ -name $casename)
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
    logfile=$1
    export CUDA_PATH=/usr/local/corex
    res_code=0
    cd /opt/cuda-samples-master
    path=$(find ./ -name simpleOccupancy)
    cd $path
    clang++ -std=c++11 -I../../common/inc -I$CUDA_PATH/include --cuda-path=$CUDA_PATH -L$CUDA_PATH/lib64 -lcudart -lixlogger -lcuda -o simpleOccupancy simpleOccupancy.cu
    ./simpleOccupancy &>>$logfile
    if [[ $? -eq 0 ]]; then
        echo "Test simpleOccupancy succeed." >>$logfile
    else
        echo "Test simpleOccupancy failed." >>$logfile
        res_code=1
    fi

    path=$(find ./ -name clock)
    cd $path
    clang++ --cuda-path=$CUDA_PATH -I$CUDA_PATH/include -L$CUDA_PATH/lib64 -I../../common/inc -lcudart -lixlogger -lcuda -o clock ./clock.cu
    ./clock &>>$logfile
    if [[ $? -eq 0 ]]; then
        echo "Test clock succeed." >>$logfile
    else
        echo "Test clock failed." >>$logfile
        res_code=1
    fi

    path=$(find ./ -name bandwidthTest)
    cd $path
    clang++ --cuda-path=$CUDA_PATH -I$CUDA_PATH/include -L$CUDA_PATH/lib64 -I../../common/inc -lcudart -lixlogger -lcuda -lixthunk -o bandwidthTest bandwidthTest.cu
    ./bandwidthTest &>>$logfile
    if [[ $? -eq 0 ]]; then
        echo "Test bandwidthTest succeed." >>$logfile
    else
        echo "Test bandwidthTest failed." >>$logfile
        res_code=1
    fi

    path=$(find ./ -name p2pBandwidthLatencyTest)
    cd $path
    clang++ --cuda-path=$CUDA_PATH -I$CUDA_PATH/include -L$CUDA_PATH/lib64 -I../../common/inc -lcudart -o p2pBandwidthLatencyTest p2pBandwidthLatencyTest.cu
    ./p2pBandwidthLatencyTest &>>$logfile
    if [[ $? -eq 0 ]]; then
        echo "Test p2pBandwidthLatencyTest succeed." >>$logfile
    else
        echo "Test p2pBandwidthLatencyTest failed." >>$logfile
        res_code=1
    fi

    path=$(find ./ -name deviceQuery)
    cd $path
    clang++ --cuda-path=$CUDA_PATH -I$CUDA_PATH/include -L$CUDA_PATH/lib64 -I../../common/inc -lcudart -lixlogger -lcuda -o deviceQuery deviceQuery.cpp
    ./deviceQuery &>>$logfile
    if [[ $? -eq 0 ]]; then
        echo "Test deviceQuery succeed." >>$logfile
    else
        echo "Test deviceQuery failed." >>$logfile
        res_code=1
    fi

    return $res_code
}

function test_cuda_samples() {
    logfile=$1
    allcases=(${2//,/ })
    res_code=0
    install_cuda_samples
    cd /opt/cuda-samples-master
    lsmod | grep bi_driver
    if [[ $? -eq 0 ]]; then
        test_iluvatar_case
        res_code=$?
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
