import os
import re
import time

import paramiko

from hwcompatible.constants import FILE_FLAGS, FILE_MODES
from hwcompatible.test import Test

NAME = 'qemu_003'
PASSWORD = 'openEuler12#$'
LOCAL_IP = '192.168.122.1'

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)


class Qemu003(Test):

    def test(self):
        self.logger.info('Start testcase qemu_003.')

        # 创建
        result = self.create_vm('qemu', NAME)
        if not result:
            return False

        # 获取IP
        r = self.command.run_cmd(f'bash ../console_cmd.sh {NAME} {PASSWORD} ""')
        ip = re.search(r'IP address: \t((\d+\.){3}\d+)', r[0]).group(1)
        self.logger.info(f'IP: {ip}')

        # 重启
        r = self.command.run_cmd(f'virsh reboot {NAME}')
        if 'rebooted' not in r[0]:
            self.logger.error('Reboot failed.')
            return False
        self.logger.info('Reboot succeed.')
        time.sleep(15)

        # ping通外部IP
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(ip, username='root', password=PASSWORD)

        stdin, stdout, stderr = ssh_client.exec_command(f'ping {LOCAL_IP} -c 3')
        result = stdout.read().decode('utf-8').strip()
        return_code = stdout.channel.recv_exit_status()
        if '0 received' in result or return_code:
            self.logger.error(f'VM ping {LOCAL_IP} failed.')
            return False
        self.logger.info(f'VM ping {LOCAL_IP} succeed.')

        return True

    def teardown(self):
        self.logger.info('Teardown testcase qemu_003.')
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
