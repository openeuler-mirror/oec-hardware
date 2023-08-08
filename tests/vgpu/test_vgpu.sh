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
# Create: 2022-06-20

arch=$(uname -m)
vmfile="test_vm_"${arch}".xml"
kernel_version=$(uname -r)


# Desc: Create virtual machine
# Input: vgpu testcase direcotry, gpu device name
function create_vm() {
    vgpu_dir=$1
    name=$2
    bus=$(echo $name | cut -d '-' -f 2)
    if [[ $arch == "aarch64" ]]; then
        dnf install -y edk2-aarch64
    else
        dnf install -y edk2-ovmf
    fi
    systemctl start libvirtd
    cp ${vgpu_dir}"/vm_"${arch}".xml" /opt/${vmfile}
    os_version=$(grep openeulerversion /etc/openEuler-latest | cut -d = -f 2)
    qcow2_name="${os_version}-${arch}.qcow2"
    if [[ ! -f /opt/${qcow2_name} ]]; then
        qcow2_url="https://repo.openeuler.org/${os_version}/virtual_machine_img/${arch}/${os_version}-${arch}.qcow2.xz"
        wget $qcow2_url -P /opt
        xz -d /opt/${qcow2_name}".xz"
    fi
    uuid=$(create_uuid $bus)
    sed -i "s#/xxxx.qcow2#/${qcow2_name}#" /opt/${vmfile}
    sed -i "s#test_uuid#${uuid}#" /opt/${vmfile}
    virsh define /opt/${vmfile}
    virsh start openEulerVM
    sleep 60
    return 0
}


# Desc: Create vgpu uuid fro vm
# Input: gpu device bus number
function create_uuid() {
    bus=$1
    dir=$(ls /sys/class/mdev_bus/${bus}/mdev_supported_types | head -n 1)
    uuid=$(ls /sys/class/mdev_bus/${bus}/mdev_supported_types/${dir}/devices | head -n 1)
    if [[ "${uuid}" -ne "" ]]; then 
        printf $uuid
        return
    fi
    uuidgen >/sys/class/mdev_bus/${bus}/mdev_supported_types/${dir}/create
    uuid=$(ls /sys/class/mdev_bus/${bus}/mdev_supported_types/${dir}/devices | head -n 1)
    printf $uuid
}


# Desc: Destory virtual machine and remove vgpu uuid
# Input: gpu device name
function destory_vm() {
    name=$1
    bus=$(echo $name | cut -d '-' -f 2)
    virsh shutdown openEulerVM
    virsh undefine openEulerVM --nvram
    rm -f /opt/${vmfile}
    sleep 10
    dir=$(ls /sys/class/mdev_bus/${bus}/mdev_supported_types | head -n 1)
    uuid=$(ls /sys/class/mdev_bus/${bus}/mdev_supported_types/${dir}/devices | head -n 1)
    echo 1 > /sys/class/mdev_bus/${bus}/${uuid}/remove
    return 0
}


# Desc: Install nvidia driver in vm and test vgpu
function test_vgpu_client() {
    # Get virtual machine ip
    vm_mac=$(virsh dumpxml openEulerVM | grep "mac address" | cut -d \' -f 2)
    vm_ip=$(arp -an | grep $vm_mac | awk '{print $2}')
    vm_ip=$(echo ${vm_ip:1:-1})
    passwd="openEuler12#$"

    echo "Get kvm driver and scp to vm."
    vm_driver=$(find /root -name "NVIDIA*grid.run")
    scpfile ${vm_driver} "root@${vm_ip}:/root" $passwd
 
    echo "Install dependency rpms."
    dep_cmd="dnf install -y pciutils tar kernel-source-${kernel_version} rpm-build openssl-devel bc rsync gcc gcc-c++ flex bison m4 elfutils-libelf-devel kernel-devel-${kernel_version} make"
    sshcmd $vm_ip $passwd "${dep_cmd}"

    echo "Check vgpu device in vm."
    testcmd="lspci | grep -i nvidia"
    sshcmd $vm_ip $passwd "${testcmd}"
    if [[ $? -ne 0 ]]; then
        return 1
    fi

    echo "Start to install driver."
    install_cmd="bash ${vm_driver} --disable-nouveau --ui=none --no-questions"
    sshcmd $vm_ip $passwd "${install_cmd}"
    if [[ $? -ne 0 ]]; then
        return 1
    fi

    echo "Check vgpu version and test."
    testcmd="nvidia-installer -i; nvidia-installer --sanity --ui=none; nvidia-smi"
    sshcmd $vm_ip $passwd "${testcmd}"
    if [[ $? -ne 0 ]]; then
        return 1
    fi
    return 0
}


# Desc: SCP file from server to vm
# Input: file name, remote machine ip and path, remote machine password
function scpfile() {
    file=$1
    remote=$2
    passwd=$3
    expect <<-SCPEOF
        set timeout -1
        spawn scp $file $remote
        expect {
            "Are you sure you want to continue connecting*"
            {
                send "yes\r";exp_continue
            }
            "*\[P|p]assword:"
            {
                send "${passwd}\r"
            }
            timeout 
            {
                send_user "connection to remote timed out: \$expect_out(buffer)\n"
                exit 101
            }
            eof
            {
                catch wait result
                exit [lindex \$result 3] 
            }
        }
        expect {
            eof 
            {
                catch wait result
                exit [lindex \$result 3]
            }
            -re "\[P|p]assword:" 
            {
                send_user "invalid password or account. \$expect_out(buffer)\n"
                exit 13
            }
            timeout 
            {
                send_user "connection to remote timed out : \$expect_out(buffer)\n"
                exit 101
            }
        }
SCPEOF
    return $? 
}


# Desc: SSH vm to execute special command
# Input: remote machine ip, remote machine password, special command
function sshcmd() {
    ip=$1
    passwd=$2
    cmd=$3
    timeout=600
    expect <<-SSHEOF
        set timeout $timeout
        spawn ssh -o "ConnectTimeout=${timeout}" root@${ip} "${cmd}"
            expect {
                "Are you sure you want to continue connecting*"
                {
                    send "yes\r";exp_continue
                }
                "*\[P|p]assword:"
                {
                    send "${passwd}\r"
                }
                timeout 
                {
                    end_user "connection to remote timed out: \$expect_out(buffer)\n"
                    exit 101
                }
                eof 
                {
                    catch wait result
                    exit [lindex \$result 3] 
                }
            }
            expect {
                eof {
                    catch wait result
                    exit [lindex \$result 3] 
                }
                "\[P|p]assword:" 
                {
                    send_user "invalid password or account again.\$expect_out(buffer)\n"
                    send "${passwd}\r"
                }
                timeout 
                {
                    send_user "connection to remote timed out: \$expect_out(buffer)\n"
                    exit 101
                }
            }
        }
SSHEOF
    return $?
}


function main() {
    func_name=$1
    para=$2
    if [[ $func_name == "create_vm" ]]; then
        create_vm $para
    elif [[ $func_name == "test_vgpu_client" ]]; then
        test_vgpu_client
    elif [[ $func_name == "destory_vm" ]]; then
        destory_vm $para
    else
        echo "The function doesn't exist, please check!"
        return 1
    fi
}

main "$@"
