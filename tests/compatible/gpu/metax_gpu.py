# coding: utf-8

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

import os
import re
from typing import TYPE_CHECKING, Any, Optional

from metax._bandwidth import MetaXBandwidthTest
from metax._check import MetaXCheck
from metax._common import (
    C500_BIOS_PATH,
    METAX_DRIVER_NAME,
    MXVS_PATH,
    MetaXCommon,
)
from metax._mccl import MetaXMCCLTest
from metax._system_prepare import MetaXSystemPrepare
from metax._warm_reset import MetaXWarmResetTest

from hwcompatible.command import Command

if TYPE_CHECKING:
    from hwcompatible.log import Logger

gpu_dir = os.path.dirname(os.path.realpath(__file__))

__all__ = [
    "C500_BIOS_PATH",
    "METAX_DRIVER_NAME",
    "MXVS_PATH",
    "MetaXBandwidthTest",
    "MetaXCheck",
    "MetaXCommon",
    "MetaXGpuTest",
    "MetaXMCCLTest",
    "MetaXSystemPrepare",
    "MetaXWarmResetTest",
    "gpu_dir",
]


class MetaXGpuTest():
    def __init__(self, device, logger: "Logger", command: Command):
        self.device = device
        self.logger: Logger = logger
        self.command: Command = command
        self.board_id: Optional[str] = None
        self.system_prepare_runner = MetaXSystemPrepare(device, logger, command)
        self.check_runner = MetaXCheck(
            logger, command, self.system_prepare_runner)
        self.bandwidth_test_runner = MetaXBandwidthTest(logger, command)
        self.warm_reset_test_runner = MetaXWarmResetTest(logger, command)
        self.mccl_test_runner = MetaXMCCLTest(logger, command)

    def get_driver_info(self) -> None:
        """获取驱动信息，包括驱动名称与版本。"""
        self.logger.info("Vendor Info:", terminal_print=False)
        self.command.run_cmd(f'lspci -vs {self.device.pci}')

        self.logger.info("Driver Info:", terminal_print=False)
        driver = self.device.driver
        self.logger.info(f"Driver Name: {driver}")

        driver_version = self.device.get_driver_version()
        if driver_version:
            self.logger.info(f"Driver Version: {driver_version}")
        else:
            self.logger.warning(
                "The driver version information cannot be obtained. Please view it manually.")

    def _discover_board_id(self) -> Optional[str]:
        """查找当前 oech 选中设备对应的 mxvs board ID。

        运行一次 ``mxvs devices``，匹配 BDF 与 ``self.device.pci`` 的条目即为结果；
        后续所有 mxvs 测试通过 ``-d <id>`` 仅针对该设备执行。
        """
        self.logger.info(
            f"Discover mxvs board ID for device {self.device.pci}.")
        cmd = self.command.run_cmd(
            MetaXCommon.build_mxvs_cmd(None, "devices"), ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Run mxvs devices for board ID discovery failed.")
            return None

        device_pattern = re.compile(
            r"^\s*(?P<board_id>\d+)\s+\d+\s+.+?\s+"
            r"(?P<bdf>(?:[0-9a-fA-F]{4}:)?[0-9a-fA-F]{2}:"
            r"[0-9a-fA-F]{2}\.[0-7])(?:\s|$)")

        target_bdf = MetaXCommon.normalize_bdf(self.device.pci)
        for line in cmd[0].splitlines():
            match = device_pattern.match(line)
            if not match:
                continue
            board_id = match.group("board_id")
            bdf = match.group("bdf")
            if MetaXCommon.normalize_bdf(bdf) == target_bdf:
                self.logger.info(
                    f"Found mxvs board ID {board_id} for device "
                    f"{self.device.pci} (BDF {bdf}).")
                return board_id

        self.logger.error(
            f"No mxvs board ID found for device {self.device.pci}.")
        return None

    def reload_driver(self, params: dict[str, Any]) -> bool:
        """使用 modprobe 参数重新加载 MetaX 驱动。

        params 为驱动参数字典，例如 ``{"disable_pci_cpl_timeout": 1}``。
        """
        param_string = " ".join(
            f"{key}={value}" for key, value in params.items())
        load_cmd = f"modprobe {METAX_DRIVER_NAME}"
        if param_string:
            load_cmd = f"{load_cmd} {param_string}"

        self.logger.info("Reload MetaX GPU driver.")
        cmd = self.command.run_cmd(
            f"modprobe -r {METAX_DRIVER_NAME}",
            ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Unload MetaX GPU driver failed.")
            return False

        self.logger.info(
            f"Load MetaX GPU driver with parameters: "
            f"{param_string if param_string else 'none'}.")
        cmd = self.command.run_cmd(load_cmd, ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Load MetaX GPU driver failed.")
            return False
        return True

    def test_metax_gpu(self) -> bool:
        """MetaX GPU 完整测试入口，依次执行环境准备与各子项检查。"""
        self.logger.info("Start MetaX GPU test.")
        # 准备系统环境
        gpu_count = self.system_prepare_runner.prepare_system()
        if gpu_count is None:
            return False

        # 检查MetaX GPU BIOS版本，版本不是最新时提示用户手动升级并终止测试
        if not self.check_runner.check_card_bios_version():
            return False

        # 检查oech选择的device在mxvs中的board id，后续所有mxvs测试都加入 -d <id>
        self.board_id = self._discover_board_id()
        if self.board_id is None:
            return False
        self.check_runner.board_id = self.board_id
        self.bandwidth_test_runner.board_id = self.board_id

        if not self.reload_driver({"runpm": 0}):
            return False
        self.get_driver_info()

        # 检查MetaX GPU ECC状态
        if not self.check_runner.check_ecc():
            return False
        
        # 检查MetaX GPU HBM带宽
        if not self.check_runner.check_hbm():
            return False
        
        # 检查MetaX GPU算子性能
        if not self.check_runner.check_ops():
            return False
        
        # 检查MetaX GPU PCIe眼图
        if not self.check_runner.check_pcie_eye():
            return False
        
        # 检查MetaX GPU带宽
        if not self.bandwidth_test_runner.check_bandwidth():
            return False
        if not self.warm_reset_test_runner.warm_reset_test(
                gpu_count, self.board_id):
            return False
        if not self.mccl_test_runner.mccl_test(self.board_id):
            return False

        self.logger.info("MetaX GPU test completed successfully.")
        return True
