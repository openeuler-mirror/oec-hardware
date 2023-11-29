import os
import time

from hwcompatible.constants import FILE_FLAGS, FILE_MODES
from hwcompatible.test import Test

NAME = 'qemu_001'
PASSWORD = 'openEuler12#$'
VCPU_NUM = '4'

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)


class Qemu001(Test):

    def test(self):
        self.logger.info('Start testcase qemu_001.')

        # 创建
        result = self.create_vm('qemu', NAME, VCPU_NUM)
        if not result:
            return False

        # 获取CPU数量
        cmd = '"lscpu|grep \'^CPU(s)\'|awk \'{print\\\\\\$2}\'"'
        r = self.command.run_cmd(f'bash ../console_cmd.sh {NAME} {PASSWORD} {cmd}')
        vcpu_num = r[0].split('\n')[-2]
        if vcpu_num != VCPU_NUM:
            self.logger.error('The number of vCPUs is incorrect.')
            return False
        self.logger.info('The number of vCPUs is correct.')

        return True

    def teardown(self):
        self.logger.info('Teardown testcase qemu_001.')
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
