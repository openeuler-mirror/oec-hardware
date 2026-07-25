# Copyright (c) 2020-2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2022-10-14
# Desc: MetaX GPU test

import re
from typing import TYPE_CHECKING, Optional

from hwcompatible.command import Command

if TYPE_CHECKING:
    from hwcompatible.log import Logger


class MetaXSystemPrepare():
    def __init__(self, device, logger: "Logger", command: Command):
        self.device = device
        self.logger: "Logger" = logger
        self.command: Command = command

    def check_metax_device(self) -> bool:
        self.logger.info("Check MetaX GPU device.")
        cmd = self.command.run_cmd("lspci | grep 9999", ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("No MetaX GPU device found.")
            return False
        return True

    def check_pcie_srcvalid(self) -> bool:
        self.logger.info("Check MetaX GPU PCIe SrcValid status.")
        cmd = self.command.run_cmd(f"lspci -vvvs {self.device.pci}", ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Get MetaX GPU PCIe information failed.")
            return False
        srcvalid_count = sum(
            1 for line in cmd[0].splitlines()
            if line.strip().startswith("ACSCtl:") and "SrcValid+" in line
        )
        if srcvalid_count > 1:
            self.logger.error(
                f"MetaX GPU PCIe ACSCtl SrcValid+ count is {srcvalid_count}.")
            return False
        return True

    def check_iommu_status(self) -> bool:
        self.logger.info("Check IOMMU status in kernel parameters.")
        cmd = self.command.run_cmd("cat /proc/cmdline | grep iommu=off", ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Kernel parameters do not contain iommu=off.")
            return False
        return True

    def get_cpu_governors(self):
        cmd = self.command.run_cmd(
            "bash -c 'cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'",
            ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Get CPU scaling governor failed.")
            return None
        return [governor.strip() for governor in cmd[0].splitlines()]

    def ensure_cpu_performance_governor(self) -> bool:
        self.logger.info("Check CPU scaling governor.")
        cpu_governors = self.get_cpu_governors()
        if cpu_governors is None:
            return False

        if not cpu_governors:
            self.logger.error("CPU scaling governor is empty.")
            return False

        if any(governor != "performance" for governor in cpu_governors):
            self.logger.info(
                "CPU scaling governor is not performance, try to set it.")
            cmd = self.command.run_cmd(
                "sudo cpupower -c all frequency-set -g performance",
                ignore_errors=True)
            if cmd[2] != 0:
                self.logger.warning(
                    "Set CPU scaling governor by cpupower failed, try sysfs.")
                cmd = self.command.run_cmd(
                    "sudo bash -c 'for i in $(seq 0 $((nproc - 1))); "
                    "do echo performance > "
                    "/sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor; "
                    "done'",
                    ignore_errors=True)
                if cmd[2] != 0:
                    self.logger.error("Set CPU scaling governor failed.")
                    return False

            cpu_governors = self.get_cpu_governors()
            if cpu_governors is None:
                return False
            if (not cpu_governors
                    or any(governor != "performance"
                           for governor in cpu_governors)):
                self.logger.error(
                    "CPU scaling governor is still not performance after setting.")
                return False

        return True

    def get_card_versions(self) -> Optional[dict[int, dict[str, str]]]:
        """通过 mx-smi 获取所有 MetaX GPU 版本信息。

        返回 GPU ID 到版本项字典的映射；失败时返回 None。
        """
        attached_gpus_pattern = re.compile(r"^\s*Attached GPUs\s*:\s*(\d+)\s*$")
        gpu_pattern = re.compile(r"^\s*GPU#(\d+)\s+")
        version_pattern = re.compile(
            r"^\s*(?P<name>[A-Za-z][A-Za-z0-9_-]*)\s*:\s*(?P<version>\S+)\s*$")

        self.logger.info("Get MetaX GPU version information.")
        cmd = self.command.run_cmd("mx-smi --show-version", ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Get MetaX GPU version information failed.")
            return None

        attached_gpus = None
        current_gpu_id = None
        gpu_versions = {}
        for line in cmd[0].splitlines():
            attached_gpus_match = attached_gpus_pattern.match(line)
            if attached_gpus_match:
                attached_gpus = int(attached_gpus_match.group(1))
                continue

            gpu_match = gpu_pattern.match(line)
            if gpu_match:
                current_gpu_id = int(gpu_match.group(1))
                gpu_versions.setdefault(current_gpu_id, {})
                continue

            if current_gpu_id is None:
                continue

            version_match = version_pattern.match(line)
            if version_match:
                gpu_versions[current_gpu_id][version_match.group("name")] = (
                    version_match.group("version"))

        if not gpu_versions:
            self.logger.error("No MetaX GPU version information found.")
            return None

        empty_gpu_ids = [
            gpu_id for gpu_id, versions in sorted(gpu_versions.items())
            if not versions
        ]
        if empty_gpu_ids:
            self.logger.error(
                f"No MetaX GPU version items found on GPU: "
                f"{', '.join(str(gpu_id) for gpu_id in empty_gpu_ids)}.")
            return None

        if attached_gpus is not None and len(gpu_versions) != attached_gpus:
            self.logger.error(
                f"MetaX GPU version information count {len(gpu_versions)} "
                f"does not match attached GPU count {attached_gpus}.")
            return None

        return gpu_versions

    def prepare_system(self) -> Optional[int]:
        if not self.check_metax_device():
            return None
        if not self.check_pcie_srcvalid():
            return None
        if not self.check_iommu_status():
            return None
        if not self.ensure_cpu_performance_governor():
            return None
        card_versions = self.get_card_versions()
        if card_versions is None:
            return None
        self.logger.info("MetaX GPU version information:")
        for gpu_id in sorted(card_versions):
            version_text = ", ".join(
                f"{name}={version}"
                for name, version in card_versions[gpu_id].items()
            )
            self.logger.info(
                f"  GPU#{gpu_id}: {version_text}")
        return len(card_versions)
