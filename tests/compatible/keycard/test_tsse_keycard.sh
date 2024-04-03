#!/usr/bin/bash
# Copyright (c) 2024 Montage Technology.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2024-03-20
# Desc: Shell script used for testing tsse keycard

function main() {
    res_code=0
    cd /opt
    if [ ! -f openssl-3.1.5.tar.gz ]; then
        wget https://www.openssl.org/source/openssl-3.1.5.tar.gz
    fi
    if [ ! -d openssl-3.1.5 ]; then
        tar -xvzf openssl-3.1.5.tar.gz -C . &>/dev/null
    fi
    if [ ! -d /opt/local/ssl ]; then
        cd openssl-3.1.5
        ./Configure --prefix=/opt/local/ssl --openssldir=/opt/local/ssl
        echo "doing make and make install ..."
        make &>/dev/null || res_code=1
        make install &>/dev/null || res_code=1
        echo "make and make install completed"
    fi
    if [ ! -f /usr/lib64/libssl.so.3 ]; then
        ln -s /opt/local/ssl/lib64/libssl.so.3 /usr/lib64/libssl.so.3
    fi
    if [ ! -f /usr/lib64/libcrypto.so.3 ]; then
        ln -s /opt/local/ssl/lib64/libcrypto.so.3 /usr/lib64/libcrypto.so.3
    fi
    return $res_code
}

main "$@"