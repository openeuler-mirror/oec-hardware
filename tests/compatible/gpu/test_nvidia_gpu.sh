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
cuda_name=$(ls /opt | grep cuda-samples)
vulkansdk_version="1.3.296.0"

function install_clpeak() {
    cd /opt
    res_code=0
    if [ ! -d clpeak ]; then
       git clone https://gitee.com/shangbaogen/clpeak.git
    fi
    cd clpeak
    git checkout 1.1.2 &>/dev/null
    if [ ! -d build ]; then
        mkdir build
    fi
    cd build
    if [ ! -d sdk_install ]; then
        cmake .. &>/dev/null || res_code=1
    fi
    cmake --build . &>/dev/null || res_code=1
    return $res_code
}

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
    if [ -z ${cuda_name} ]; then
        wget https://github.com/NVIDIA/cuda-samples/archive/refs/tags/v${cuda_version}.zip
        if [ $? -eq 0 ]; then
            unzip v${cuda_version}.zip >/dev/null
            rm -rf v${cuda_version}.zip
        else
            echo "Download cuda-samples-${cuda_version} error!!!"
            return 1;
        fi
    fi

    cuda_name=$(ls /opt | grep cuda-samples)
    cd /opt/${cuda_name}
    sed -i 's/centos/openEuler/g' Samples/5_Domain_Specific/simpleVulkan/findvulkan.mk
    sed -i 's/CENTOS/OPENEULER/g' Samples/5_Domain_Specific/simpleVulkan/findvulkan.mk
    sed -i 's/centos/openEuler/g' Samples/5_Domain_Specific/simpleVulkanMMAP/findvulkan.mk
    sed -i 's/CENTOS/OPENEULER/g' Samples/5_Domain_Specific/simpleVulkanMMAP/findvulkan.mk
    sed -i 's/centos/openEuler/g' Samples/5_Domain_Specific/vulkanImageCUDA/findvulkan.mk
    sed -i 's/CENTOS/OPENEULER/g' Samples/5_Domain_Specific/vulkanImageCUDA/findvulkan.mk
    if uname -m | grep -q 'aarch64'; then
       sed -i 's/build: cdpAdvancedQuicksort/build:/g' Samples/3_CUDA_Features/cdpAdvancedQuicksort/Makefile
       sed -i 's/build: cdpBezierTessellation/build:/g' Samples/3_CUDA_Features/cdpBezierTessellation/Makefile
       sed -i 's/build: cdpQuadtree/build:/g' Samples/3_CUDA_Features/cdpQuadtree/Makefile
       sed -i 's/build: cdpSimplePrint/build:/g' Samples/3_CUDA_Features/cdpSimplePrint/Makefile
       sed -i 's/build: cdpSimpleQuicksort/build:/g' Samples/3_CUDA_Features/cdpSimpleQuicksort/Makefile
    fi

    if [ ! -d "/tmp/xdg-runtime" ]; then
        mkdir /tmp/xdg-runtime
    fi

    export XDG_RUNTIME_DIR=/tmp/xdg-runtime

    return 0
}

function install_Vulkansdk_Depend_Packages() {
    if uname -m | grep -q 'x86_64'; then
        rm -rf /opt/vulkansdk
        rm -rf /opt/vulkansdk-linux-x86_64-${vulkansdk_version}.tar.xz
        cd /opt
        mkdir vulkansdk
        cd vulkansdk
        wget https://sdk.lunarg.com/sdk/download/${vulkansdk_version}/linux/vulkansdk-linux-x86_64-${vulkansdk_version}.tar.xz
        if [ $? -eq 0 ]; then
            dnf install -y qt xinput xz libXinerama
            tar xvf vulkansdk-linux-x86_64-${vulkansdk_version}.tar.xz >/dev/null
            rm -rf ./vulkansdk-linux-x86_64-${vulkansdk_version}.tar.xz
            source /opt/vulkansdk/${vulkansdk_version}/setup-env.sh
        else
            echo "Download vulkansdk-linux-x86_64-${vulkansdk_version}.tar.xz error!!!"
            rm -rf /opt/vulkansdk
            return 1;
        fi
    fi

    rm -rf /opt/glfw
    cd /opt
    git clone https://gitee.com/baogen_shang/glfw.git
    if [ $? -eq 0 ]; then
        dnf install -y wayland-devel libxkbcommon-devel libXcursor-devel libXi-devel libXinerama-devel libXrandr-devel doxygen
        cd /opt/glfw
        git checkout tags/3.4
        mkdir build
        cd build
        cmake -DBUILD_SHARED_LIBS=ON ..
        make
        make install
        export PKG_CONFIG_PATH=/usr/local/lib64/pkgconfig:$PKG_CONFIG_PATH
        export LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH
    else
        echo "Download glfw error!!!"
        rm -rf /opt/glfw
        return 1;
    fi

    dnf install -y mesa-libGLU mesa-libGLU-devel openmpi-devel openmpi freeglut freeglut-devel
    return 0
}

function install_VulkanSamples() {
    cd /opt
    res_code=0
    if [ ! -d Vulkan-Samples ]; then
        git clone --recurse-submodules https://github.com/KhronosGroup/Vulkan-Samples.git
        if [ $? -ne 0 ]; then
            echo "Download the Vulkan-Samples failed, Please check your network!!!"
            exit 1
        fi
    fi
    cd Vulkan-Samples
    cmake -G "Unix Makefiles" -Bbuild/linux -DCMAKE_BUILD_TYPE=Release &>/dev/null
    if [[ $? -eq 0 ]]; then
        cmake --build build/linux --config Release --target vulkan_samples -j4 &>/dev/null || res_code=1
    else
        echo "Generate Makefile Failed!!!"
        res_code=1
    fi

    if [ ! -d "/opt/vulkansdk" ]; then
        install_Vulkansdk_Depend_Packages
    else
        source /opt/vulkansdk/${vulkansdk_version}/setup-env.sh
    fi

    return $res_code
}

function test_nvidia_case() {
    casename=$1
    logfile=$2
    res_code=0

    cd /opt/${cuda_name}
    if [[ $casename == 'cuda_maketest' ]];then
        make test &>>$logfile
    else
        path=$(find ./ -name $casename -type d)
        cd $path
        ./$casename &>>$logfile
    fi

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
    install_Vulkansdk_Depend_Packages
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
        cd /opt/${cuda_name}
        make &>/dev/null
        for casename in ${allcases[@]}; do
            test_nvidia_case $casename $logfile
            if [[ $? -eq 1 ]]; then
                res_code=1
            fi
        done
    fi
    return $res_code
}

function test_clpeak() {
    logfile=$1
    res_code=0
    install_clpeak
    if [[ $? -eq 1 ]]; then
        echo "Install clpeak failed."
        res_code=1
        return $res_code
    fi
    /opt/clpeak/build/clpeak &> $logfile
    if [[ $? -eq 0 ]]; then
        echo "Test clpeak succeed."
        res_code=0
    else
        echo "Test clpeak failed."
        res_code=1
    fi
    return $res_code
}

sm_clock=`nvidia-smi -q|grep "SM "|head -n 1|cut -d ':' -f 2|awk '{print $1}'`
memory_clock=`nvidia-smi -q -d SUPPORTED_CLOCKS|grep Memory|head -n 1|cut -d ':' -f 2|awk '{print $1}'`
min_power_limit=`nvidia-smi -q|grep "Min Power Limit"|head -n 1|cut -d ':' -f 2|awk '{print $1}'`
max_power_limit=`nvidia-smi -q|grep "Max Power Limit"|head -n 1|cut -d ':' -f 2|awk '{print $1}'`
if nvidia-smi |grep -q 'Tesla V100'; then
    RESET_CASE=""
else
    RESET_CASE="nvidia-smi -r;"
fi

allcases="nvidia-smi; \
         nvidia-smi -L; \
         nvidia-smi -q; \
         nvidia-smi -q -d SUPPORTED_CLOCKS; \
         nvidia-smi topo --matrix; \
         nvidia-smi -pm 0; \
         nvidia-smi -pm 1; \
         nvidia-smi -e 0; \
         nvidia-smi -e 1; \
         nvidia-smi -p 0; \
         nvidia-smi -p 1; \
         nvidia-smi -c 0; \
         nvidia-smi -c 2; \
         nvidia-smi -c 3; \
         nvidia-smi -pl $min_power_limit; \
         nvidia-smi -pl $max_power_limit; \
         nvidia-smi -ac $memory_clock,$sm_clock; \
         nvidia-smi -am 1; \
         nvidia-smi -am 0; \
         nvidia-smi -caa; \
         $RESET_CASE \
"

function test_nvidia_smi() {
    logfile=$1
    IFS_OLD=$IFS
    IFS=$';'
    res_code=0
    for casename in ${allcases[@]}; do
        eval $casename
        if [[ $? -eq 1 ]]; then
            res_code=1
        fi
    done
    IFS=${IFS_OLD}
    return $res_code
}

function test_VulkanSamples() {
    logfile=$1
    res_code=0
    install_VulkanSamples
    if [[ $? -eq 1 ]]; then
        echo "Install VulkanSamples failed." &>> $logfile
        exit 1
    fi
    if [ -n "$DISPLAY" ]; then
        cd /opt/Vulkan-Samples
        ./build/linux/app/bin/Release/x86_64/vulkan_samples batch &>> $logfile
        if [[ $? -eq 0 ]]; then
            echo "Test VulkanSamples succeed." &>> $logfile
            res_code=0
        else
            echo "Test VulkanSamples failed." &>> $logfile
            res_code=1
        fi
    else
        echo "Please set the DISPLAY environment variables!" &>> $logfile
        res_code=1
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
    elif [[ $func_name == "test_clpeak" ]]; then
        test_clpeak $param_list
    elif [[ $func_name == "test_nvidia_smi" ]]; then
        test_nvidia_smi $param_list
    elif [[ $func_name == "test_VulkanSamples" ]]; then
        test_VulkanSamples $param_list
    else
        echo "The function doesn't exist, please check!"
        return 1
    fi
}

main "$@"
