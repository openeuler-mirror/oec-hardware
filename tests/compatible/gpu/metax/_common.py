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
import time
from typing import TYPE_CHECKING, Optional

from hwcompatible.command import Command

if TYPE_CHECKING:
    from hwcompatible.log import Logger

MXVS_PATH = "/opt/maca/bin/mxvs"
C500_BIOS_PATH = "/lib/firmware/metax/mxc500"
METAX_DRIVER_NAME = "metax"


class MetaXCommon:
    """MetaX GPU 测试共用工具。"""

    @staticmethod
    def normalize_bdf(bdf: str) -> str:
        """归一化 PCI BDF，去除可选的 ``0000:`` 域前缀。"""
        bdf = bdf.strip().lower()
        bdf = bdf.removeprefix("0000:")
        return bdf

    @staticmethod
    def build_mxvs_cmd(board_id: Optional[str], subcommand: str) -> str:
        """构建 mxvs 命令，并可选地限定目标板卡。"""
        if board_id is not None:
            return f"{MXVS_PATH} {subcommand} -d {board_id}"
        return f"{MXVS_PATH} {subcommand}"

    @staticmethod
    def build_pcie_mxvs_cmd(
            board_id: Optional[str], subcommand: str) -> str:
        """构建使用源、目标设备参数限定板卡的 mxvs PCIe 命令。"""
        if board_id is not None:
            return f"{MXVS_PATH} {subcommand} --src-devices {board_id} --dst-devices all"
        return f"{MXVS_PATH} {subcommand}"

    @staticmethod
    def warm_reset_metax_gpu(
            command: Command,
            logger: "Logger",
            target: str,
            wait_seconds: int = 0) -> bool:
        """热复位一张或全部 MetaX GPU，并可选地等待设备恢复。"""
        target_name = (
            "all MetaX GPU cards"
            if target == "all" else f"MetaX GPU {target}")
        logger.info(f"Warm reset {target_name}.")
        cmd = command.run_cmd(
            f"mx-smi -r -i {target}",
            ignore_errors=True)
        if cmd[2] != 0:
            logger.error(f"Warm reset {target_name} failed.")
            return False

        if wait_seconds > 0:
            logger.info(
                f"Wait {wait_seconds} seconds after MetaX GPU warm reset.")
            time.sleep(wait_seconds)

        return True

    @staticmethod
    def calculate_pcie_bandwidth(speed: str, width: str) -> float:
        """根据端口速率和链路宽度计算 PCIe 理论单向带宽（GB/s）。"""
        speed_match = re.search(
            r"([0-9]+(?:\.[0-9]+)?)\s*GT/s", speed, re.IGNORECASE)
        width_match = re.search(r"x\s*(\d+)", width, re.IGNORECASE)
        if not speed_match:
            raise ValueError(f"Invalid PCIe speed: {speed}")
        if not width_match:
            raise ValueError(f"Invalid PCIe width: {width}")

        speed_gts = float(speed_match.group(1))
        lane_count = int(width_match.group(1))

        return speed_gts * lane_count / 8.0

    @staticmethod
    def parse_mx_smi_pcie_status(
            output: str) -> dict[str, dict[str, str]]:
        """从 ``mx-smi --show-pcie`` 输出解析各 GPU 的 PCIe 状态。"""
        pcie_status: dict[str, dict[str, str]] = {}
        current_gpu_id: Optional[str] = None
        field_names = {
            "current speed": "current_speed",
            "current width": "current_width",
            "max width": "max_width",
        }

        for raw_line in output.splitlines():
            line = raw_line.strip()
            if line.startswith("GPU#"):
                parts = line.split()
                if parts and len(parts[0]) > 4:
                    current_gpu_id = parts[0][4:]
                    pcie_status[current_gpu_id] = {}
                continue

            if current_gpu_id is None or ":" not in line:
                continue

            name, _, value = line.partition(":")
            field_name = field_names.get(name.strip().lower())
            if field_name is not None:
                pcie_status[current_gpu_id][field_name] = value.strip()

        return pcie_status
