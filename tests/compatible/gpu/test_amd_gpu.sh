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
# Create: 2022-10-13
# Desc: Shell script used for testing AMD gpu

function install_readontop() {
    cd /opt
    res_code=0
    if [ ! -d radeontop ]; then
        git clone https://github.com/clbr/radeontop.git
        dnf install -y libdrm-devel ncurses-devel ncurses-libs libpciaccess-devel libxcb-devel
    fi
    cd radeontop
    make &>/dev/null || res_code=1

    return $res_code
}

function install_glmark2() {
    cd /opt
    res_code=0
    if [ ! -d glmark2 ]; then
        git clone https://github.com/glmark2/glmark2.git
        dnf install -y meson libX11-devel libpng-devel cmake pkgconf libjpeg libjpeg-turbo-devel libdrm-devel mesa-libgbm-devel libgudev-devel
    fi
    cd glmark2
    meson setup build -Dflavors=drm-gl,drm-glesv2,wayland-gl,wayland-glesv2,x11-gl,x11-glesv2
    ninja -C build &>/dev/null
    ninja -C build install &>/dev/null || res_code=1

    return $res_code
}

function main() {
    func_name=$1

    if [[ $func_name == "install_readontop" ]]; then
        install_readontop
    elif [[ $func_name == "install_glmark2" ]]; then
        install_glmark2
    else
        echo "The function doesn't exist, please check!"
        return 1
    fi
}

main "$@"
