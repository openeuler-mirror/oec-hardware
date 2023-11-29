import os
import re
import time

import paramiko

from hwcompatible.constants import FILE_FLAGS, FILE_MODES
from hwcompatible.test import Test

NAME = 'stratovirt_004'
PASSWORD = 'openEuler12#$'
IP = '192.168.122.2'
VCPU_NUM = '22'

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)


class Stratovirt004(Test):

    def test(self):
        self.logger.info('Start testcase stratovirt_004.')

        # 创建
        result = self.create_vm('stratovirt', NAME, VCPU_NUM)
        if not result:
            return False

        # 配IP
        cmd = (
            '"dev=\\`ip link show|grep -m 1 enp|awk -F \': \' \'{print\\\\\\$2}\'\\`&& '
            r'ip link set \\\$dev up && '
            fr'ip addr add {IP}/24 dev \\\$dev"'
        )
        os.popen(f'bash ../console_cmd.sh {NAME} {PASSWORD} {cmd}')

        # 获取CPU数量
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(IP, username='root', password=PASSWORD)

        stdin, stdout, stderr = ssh_client.exec_command('cat /proc/cpuinfo|grep processor|wc -l')
        vcpu_num = stdout.read().decode('utf-8').strip()
        if vcpu_num != VCPU_NUM:
            self.logger.error('The number of vCPUs is incorrect.')
            return False
        self.logger.info('The number of vCPUs is correct.')

        # 获取内存数量
        stdin, stdout, stderr = ssh_client.exec_command('free -k|grep Mem|awk \'{print$2}\'')
        total_mem = stdout.read().decode('utf-8').strip()
        self.logger.info(f'Total memor: {total_mem}')

        # 获取磁盘信息
        stdin, stdout, stderr = ssh_client.exec_command('lsblk')
        result = stdout.read().decode('utf-8').strip()
        disk_info = re.search(r'NAME.*', result, re.S).group(0)
        self.logger.info(f'Disk info:\n{disk_info}\n')

        return True

    def teardown(self):
        self.logger.info('Teardown testcase stratovirt_004.')
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
