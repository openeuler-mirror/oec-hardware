#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) 2020 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01

import os
import re
import time

import paramiko

from hwcompatible.constants import FILE_FLAGS, FILE_MODES
from hwcompatible.test import Test

NAME = 'qemu_010'
PASSWORD = 'openEuler12#$'

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)


class Qemu010(Test):
    
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["python3-paramiko"]

    def test(self):
        self.logger.info('Start testcase qemu_010.')

        # 创建
        result = self.create_vm('qemu', NAME)
        if not result:
            return False

        # 获取IP
        r = self.command.run_cmd(f'bash ../console_cmd.sh {NAME} {PASSWORD} ""')
        ip = re.search(r'IP address: \t((\d+\.){3}\d+)', r[0]).group(1)
        self.logger.info(f'IP: {ip}')

        # 获取IO速率
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(ip, username='root', password=PASSWORD)

        stdin, stdout, stderr = ssh_client.exec_command(
            'dd if=/dev/zero of=/tmp/test.disk bs=8k count=10000 2>&1|'
            'awk -F ", " \'NR==3{printf "Write time: %s\\tWrite speed: %s\\n",$3,$4}\''
        )
        io_write_info = stdout.read().decode('utf-8').strip()
        self.logger.info(io_write_info)

        stdin, stdout, stderr = ssh_client.exec_command(
            'dd if=/tmp/test.disk of=/dev/null bs=8 2>&1|'
            'awk -F ", " \'NR==3{printf "Read time: %s\\tRead speed: %s\\n",$3,$4}\''
        )
        io_read_info = stdout.read().decode('utf-8').strip()
        self.logger.info(io_read_info)

        stdin, stdout, stderr = ssh_client.exec_command(
            'dd if=/tmp/test.disk of=/tmp/test.disk2 bs=8 2>&1|'
            'awk -F ", " \'NR==3{printf "Read/Write time: %s\\tRead/Write speed: %s\\n",$3,$4}\''
        )
        io_read_info = stdout.read().decode('utf-8').strip()
        self.logger.info(io_read_info)

        return True

    def teardown(self):
        self.logger.info('Teardown testcase qemu_010.')
        r = self.command.run_cmd(f'virsh destroy {NAME}')
        if r[2]:
            self.logger.error('Destroy vm failed.')
        else:
            self.logger.info('Destroy vm succeed.')

    def create_vm(self, category, name, vcpu_num='4'):
        with open(f'../{category}.xml') as f:
            content = f.read()
        content = content.replace('#VM_NAME#', name)
        content = content.replace('#VCPU_NUM#', vcpu_num)
        with os.fdopen(os.open('/tmp/test.xml', FILE_FLAGS, FILE_MODES), "w") as f:
            f.write(content)
        r = self.command.run_cmd('virsh create /tmp/test.xml')
        if r[2]:
            self.logger.error('Create vm failed.')
            return False
        else:
            self.logger.info('Create vm succeed.')
        time.sleep(10)
        return True
