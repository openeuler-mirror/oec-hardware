import os
import time

from hwcompatible.constants import FILE_FLAGS, FILE_MODES
from hwcompatible.test import Test

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

NAME = 'qemu_008'
PASSWORD = 'openEuler12#$'
DISK_FILE = f'{dir_path}/disk_008'
DISK_SIZE = '5'
DISK_XML = '/tmp/disk.xml'
DISK_CONTENT = f'''
<disk type="file" device="disk">
    <driver name="qemu" type="qcow2" cache="none" io="native"/>
    <source file="{DISK_FILE}"/>
    <backingStore/>
    <target dev="sdb" bus="scsi"/>
    <address type="drive" controller="0" bus="0" target="1" unit="0"/>
</disk>
'''


class Qemu008(Test):

    def test(self):
        self.logger.info('Start testcase qemu_008.')

        # 创建
        result = self.create_vm('qemu', NAME)
        if not result:
            return False

        # 创建磁盘
        self.command.run_cmd(f'qemu-img create -f qcow2 {DISK_FILE} {DISK_SIZE}G')

        # 挂载磁盘
        with os.fdopen(os.open(DISK_XML, FILE_FLAGS, FILE_MODES), "w") as f:
            f.write(DISK_CONTENT)
        r = self.command.run_cmd(f'virsh attach-device {NAME} {DISK_XML}')
        r1 = self.command.run_cmd(f'virsh domblklist {NAME}')
        if 'Device attached successfully' not in r[0] or DISK_FILE not in r1[0]:
            self.logger.error('Attach disk failed.')
            return False
        self.logger.info('Attach disk succeed.')

        # 删除虚拟机
        r = self.command.run_cmd(f'virsh destroy {NAME}')
        r1 = self.command.run_cmd(f'qemu-img info {DISK_FILE}')
        if r[2] or r1[2]:
            self.logger.error('Destroy vm failed.')
            return False
        self.logger.info('Destroy vm succeed.')

        return True

    def teardown(self):
        self.logger.info('Teardown testcase qemu_008.')
        self.command.run_cmd(f'virsh destroy {NAME}')
        r = self.command.run_cmd(f'rm -f {DISK_FILE}')
        if r[2]:
            self.logger.error('Delete disk file failed.')
        else:
            self.logger.info('Delete disk file succeed.')

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
