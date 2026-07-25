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

from typing import TYPE_CHECKING, Optional

from hwcompatible.command import Command

from ._common import MetaXCommon

if TYPE_CHECKING:
    from hwcompatible.log import Logger

class MetaXWarmResetTest():
    """MetaX GPU 热复位可靠性测试。

    反复热复位选中的 MetaX GPU 卡，校验各次迭代中 PCIe 链路状态与 GPU 可用性保持稳定。
    """

    def __init__(self, logger: "Logger", command: Command):
        self.logger: "Logger" = logger
        self.command: Command = command
        self.repeat_times = 10
        self.reset_wait_seconds = 60

    def _kill_all_processes(self) -> bool:
        self.logger.info("Kill all MetaX GPU processes.")
        cmd = self.command.run_cmd(
            "mx-smi --kill-all-process", ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Kill all MetaX GPU processes failed.")
            return False
        return True

    def _get_pcie_status(self) -> Optional[dict[str, dict[str, str]]]:
        cmd = self.command.run_cmd("mx-smi --show-pcie", ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Get MetaX GPU PCIe status failed.")
            return None
        return MetaXCommon.parse_mx_smi_pcie_status(cmd[0])

    def _check_pcie_status(
            self,
            expected_count: int,
            expected_speed: str,
            expected_width: str) -> bool:
        self.logger.info("Check MetaX GPU PCIe status.")
        pcie_status = self._get_pcie_status()
        if pcie_status is None:
            return False
        if not pcie_status:
            self.logger.error("No MetaX GPU PCIe status found.")
            return False
        if len(pcie_status) != expected_count:
            self.logger.error(
                f"MetaX GPU PCIe status count {len(pcie_status)} "
                f"does not match expected {expected_count}.")
            return False

        failed = []
        for gpu_id in sorted(pcie_status, key=int):
            status = pcie_status[gpu_id]
            speed = status.get("current_speed", "")
            width = status.get("max_width", "")
            self.logger.info(
                f"  GPU#{gpu_id} PCIe Current Speed: {speed}, Max Width: {width}.")
            if expected_speed not in speed or expected_width not in width:
                failed.append((gpu_id, speed, width))

        if failed:
            failed_text = ", ".join(
                f"GPU#{gpu_id} speed={speed} width={width}"
                for gpu_id, speed, width in failed
            )
            self.logger.error(
                "MetaX GPU PCIe status mismatch (expected Current Speed "
                f"contains {expected_speed}, Max Width contains "
                f"{expected_width}): "
                f"{failed_text}.")
            return False

        self.logger.info(
            f"MetaX GPU PCIe status check succeed, all {expected_count} GPUs "
            f"keep Current Speed {expected_speed} and Max Width "
            f"{expected_width}.")
        return True

    def _check_availability(self, expected_count: int) -> bool:
        self.logger.info("Check MetaX GPU availability.")
        cmd = self.command.run_cmd("mx-smi -L", ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Get MetaX GPU availability failed.")
            return False

        gpu_lines = [
            line.strip() for line in cmd[0].splitlines()
            if line.strip().startswith("GPU#")
        ]
        if not gpu_lines:
            self.logger.error("No MetaX GPU found in mx-smi -L output.")
            return False
        if len(gpu_lines) != expected_count:
            self.logger.error(
                f"MetaX GPU availability count {len(gpu_lines)} "
                f"does not match expected {expected_count}.")
            return False

        for line in gpu_lines:
            self.logger.info(f"  {line}")

        unavailable = [line for line in gpu_lines if "Available" not in line]
        if unavailable:
            self.logger.error(
                f"MetaX GPU not available: {', '.join(unavailable)}.")
            return False

        self.logger.info(
            f"MetaX GPU availability check succeed, all {expected_count} "
            f"GPUs are available.")
        return True

    def _capture_baseline(
            self, gpu_count: int) -> Optional[tuple[str, str]]:
        baseline = self._get_pcie_status()
        if baseline is None:
            self.logger.error("Capture baseline PCIe status failed.")
            return None
        if len(baseline) != gpu_count:
            self.logger.error(
                f"Baseline MetaX GPU count {len(baseline)} does not match "
                f"expected {gpu_count}.")
            return None

        speeds: set[str] = set()
        widths: set[str] = set()
        for status in baseline.values():
            speed = status.get("current_speed")
            width = status.get("max_width")
            if speed:
                speeds.add(speed)
            if width:
                widths.add(width)
        if len(speeds) != 1 or len(widths) != 1:
            self.logger.error(
                "Baseline PCIe speed/width inconsistent across GPUs: "
                f"speeds={', '.join(sorted(speeds))}, "
                f"widths={', '.join(sorted(widths))}.")
            return None

        return next(iter(speeds)), next(iter(widths))

    def warm_reset_test(self, gpu_count: int, target_id: str) -> bool:
        """执行 MetaX GPU 热复位可靠性测试。

        反复热复位选中的 GPU 卡并校验 PCIe 状态与可用性；期望速率/宽度取自首次复位前的基线，
        因此同时适配 x86（如 32 GT/s x16）与 arm64（如 16 GT/s x8）平台。
        """
        self.logger.info(
            f"Start MetaX GPU {target_id} warm reset test with {gpu_count} "
            f"GPUs, repeat {self.repeat_times} times.")

        baseline = self._capture_baseline(gpu_count)
        if baseline is None:
            return False
        expected_speed, expected_width = baseline
        self.logger.info(
            f"Baseline PCIe status: Current Speed {expected_speed}, "
            f"Max Width {expected_width}.")

        for run in range(1, self.repeat_times + 1):
            self.logger.info(
                f"Run warm reset test ({run}/{self.repeat_times}).")

            if not self._kill_all_processes():
                self.logger.error(
                    f"Warm reset test failed on run "
                    f"{run}/{self.repeat_times}.")
                return False
            if not MetaXCommon.warm_reset_metax_gpu(
                    self.command,
                    self.logger,
                    target_id,
                    self.reset_wait_seconds):
                self.logger.error(
                    f"Warm reset test failed on run "
                    f"{run}/{self.repeat_times}.")
                return False

            if not self._check_pcie_status(
                    gpu_count, expected_speed, expected_width):
                self.logger.error(
                    f"Warm reset test failed on run "
                    f"{run}/{self.repeat_times}.")
                return False
            if not self._check_availability(gpu_count):
                self.logger.error(
                    f"Warm reset test failed on run "
                    f"{run}/{self.repeat_times}.")
                return False

            self.logger.info(
                f"Warm reset test run {run}/{self.repeat_times} succeed.")

        self.logger.info("MetaX GPU warm reset test succeed.")
        return True
