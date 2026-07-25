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

import re
from typing import TYPE_CHECKING, Any, Callable, Optional

from hwcompatible.command import Command

from ._common import MetaXCommon

if TYPE_CHECKING:
    from hwcompatible.log import Logger

class MetaXBandwidthTest():
    RESULT_PATTERN = re.compile(
        r"^\s*(?P<src>\S+)\s+(?P<direction><<|>>|<>)\s+(?P<dst>\S+)"
        r"\s+(?P<size>\d+)\s+"
        r"(?P<effective>[0-9]+(?:\.[0-9]+)?)\s+GB/s\s+"
        r"(?P<raw>[0-9]+(?:\.[0-9]+)?)\s+GB/s\s+"
        r"(?P<delay>[0-9]+(?:\.[0-9]+)?)\s+(?P<validation>\S+)\s*$")
    P2P_RESULT_PATTERN = re.compile(
        r"^\s*(?P<src>GPU#\d+)\s+(?P<dst>GPU#\d+)\s+"
        r"(?P<topology>\S+)\s+(?P<size>\d+)\s+"
        r"(?P<effective>[0-9]+(?:\.[0-9]+)?)\s+GB/s\s+"
        r"(?P<raw>[0-9]+(?:\.[0-9]+)?)\s+GB/s\s+"
        r"(?P<delay>[0-9]+(?:\.[0-9]+)?)\s+(?P<validation>\S+)\s*$")

    def __init__(self, logger: "Logger", command: Command):
        self.logger: "Logger" = logger
        self.command: Command = command
        self.board_id: Optional[str] = None
        self.repeat_times = 3
        self.unidirectional_raw_tolerance = 0.03
        self.unidirectional_effective_tolerance = 0.15
        self.bidirectional_raw_tolerance = 0.06
        self.bidirectional_effective_tolerance = 0.30
        self.pcie_theoretical_bandwidths: dict[str, float] = {}

    @staticmethod
    def _parse_benchmark_output(
            output: str,
            pattern: "re.Pattern[str]") -> list[dict[str, Any]]:
        """按行解析 mxvs 带宽基准测试输出。

        兼容 PCIe（带 ``direction``）与 P2P（带 ``topology``）两种结果模式，可选命名组会复制到结果字典中。
        """
        benchmark_results: list[dict[str, Any]] = []
        for line in output.splitlines():
            match = pattern.match(line)
            if not match:
                continue
            groups = match.groupdict()
            result: dict[str, Any] = {
                "src": groups["src"],
                "direction": groups.get("direction", "->"),
                "dst": groups["dst"],
                "size": int(groups["size"]),
                "effective": float(groups["effective"]),
                "raw": float(groups["raw"]),
                "delay": float(groups["delay"]),
                "validation": groups["validation"],
            }
            if "topology" in groups:
                result["topology"] = groups["topology"]
            benchmark_results.append(result)
        return benchmark_results

    def parse_mx_smi_pcie_output(self, output: str) -> Optional[dict[str, float]]:
        theoretical_bandwidths = {}

        for gpu_id, status in MetaXCommon.parse_mx_smi_pcie_status(
                output).items():
            current_speed = status.get("current_speed")
            current_width = status.get("current_width")
            if current_speed is None or current_width is None:
                continue
            try:
                theoretical_bandwidths[gpu_id] = (
                    MetaXCommon.calculate_pcie_bandwidth(
                        current_speed, current_width))
            except ValueError as error:
                self.logger.error(
                    f"Parse PCIe theoretical bandwidth failed for GPU "
                    f"{gpu_id}: {error}.")
                return None

        return theoretical_bandwidths

    def get_pcie_theoretical_bandwidths(self) -> dict[str, float]:
        if self.pcie_theoretical_bandwidths:
            return self.pcie_theoretical_bandwidths

        self.logger.info("Get MetaX GPU PCIe speed and width.")
        cmd = self.command.run_cmd("mx-smi --show-pcie", ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error("Get MetaX GPU PCIe speed and width failed.")
            return {}

        theoretical_bandwidths = self.parse_mx_smi_pcie_output(cmd[0])
        if theoretical_bandwidths is None:
            return {}
        if not theoretical_bandwidths:
            self.logger.error(
                "No GPU PCIe theoretical bandwidth parsed from mx-smi --show-pcie.")
            return {}

        for gpu_id in sorted(theoretical_bandwidths, key=int):
            self.logger.info(
                f"  GPU#{gpu_id} PCIe theoretical bandwidth: "
                f"{theoretical_bandwidths[gpu_id]:.2f} GB/s.")
        self.pcie_theoretical_bandwidths = theoretical_bandwidths
        return theoretical_bandwidths

    @staticmethod
    def _get_result_board_ids(result: dict[str, Any]) -> list[str]:
        return re.findall(
            r"(?:BOARD|GPU)#(\d+)",
            f"{result['src']} {result['dst']}",
            re.IGNORECASE)

    def _check_result(
            self,
            result: dict[str, Any],
            theoretical_bandwidths: dict[str, float],
            run: int,
            raw_tolerance: float,
            effective_tolerance: float,
            theoretical_multiplier: float) -> bool:
        board_ids = self._get_result_board_ids(result)
        if not board_ids:
            self.logger.error(
                f"No board ID found in PCIe bandwidth result: "
                f"{result['src']} {result['direction']} {result['dst']} "
                f"({run}/{self.repeat_times}).")
            return False

        missing_board_ids = [
            board_id for board_id in board_ids
            if board_id not in theoretical_bandwidths
        ]
        if missing_board_ids:
            self.logger.error(
                f"No PCIe theoretical bandwidth found for boards: "
                f"{', '.join(missing_board_ids)} "
                f"({run}/{self.repeat_times}).")
            return False

        theoretical_bandwidth = min(
            theoretical_bandwidths[board_id] for board_id in board_ids)
        theoretical_bandwidth *= theoretical_multiplier
        raw_deviation = (
            abs(result["raw"] - theoretical_bandwidth) / theoretical_bandwidth)
        effective_deviation = (
            abs(result["effective"] - theoretical_bandwidth)
            / theoretical_bandwidth)

        self.logger.info(
            f"  {result['src']} {result['direction']} {result['dst']} "
            f"size {result['size']}: effective {result['effective']:.2f} GB/s, "
            f"raw {result['raw']:.2f} GB/s, "
            f"theoretical {theoretical_bandwidth:.2f} GB/s, "
            f"effective deviation {effective_deviation * 100:.2f}%, "
            f"raw deviation {raw_deviation * 100:.2f}%, "
            f"validation {result['validation']} ({run}/{self.repeat_times}).")

        if result["validation"].upper() != "PASS":
            self.logger.error(
                f"PCIe bandwidth data validation failed for {result['src']} "
                f"{result['direction']} {result['dst']}: "
                f"{result['validation']} ({run}/{self.repeat_times}).")
            return False
        if raw_deviation > raw_tolerance:
            self.logger.error(
                f"PCIe RAW bandwidth deviation exceeds "
                f"{raw_tolerance * 100:.2f}% for {result['src']} "
                f"{result['direction']} {result['dst']}: "
                f"raw {result['raw']:.2f} GB/s, "
                f"theoretical {theoretical_bandwidth:.2f} GB/s, "
                f"deviation {raw_deviation * 100:.2f}% "
                f"({run}/{self.repeat_times}).")
            return False
        if effective_deviation > effective_tolerance:
            self.logger.error(
                f"PCIe EFFECTIVE bandwidth deviation exceeds "
                f"{effective_tolerance * 100:.2f}% for {result['src']} "
                f"{result['direction']} {result['dst']}: "
                f"effective {result['effective']:.2f} GB/s, "
                f"theoretical {theoretical_bandwidth:.2f} GB/s, "
                f"deviation {effective_deviation * 100:.2f}% "
                f"({run}/{self.repeat_times}).")
            return False

        return True

    def _run_once(
            self,
            run: int,
            benchmark_name: str,
            benchmark_cmd: str,
            pattern: "re.Pattern[str]",
            raw_tolerance: float,
            effective_tolerance: float,
            theoretical_multiplier: float,
            result_precheck: Optional[Callable[[dict[str, Any]], bool]] = None,
            use_global_device_option: bool = False
            ) -> bool:
        """执行一次 PCIe 带宽基准测试。

        run 为 1 起始的迭代序号；其余参数控制子命令、解析模式、容差、理论带宽倍率与设备选择方式。
        """
        self.logger.info(
            f"Run PCIe {benchmark_name} bandwidth benchmark "
            f"({run}/{self.repeat_times}).")
        command_builder = (
            MetaXCommon.build_mxvs_cmd
            if use_global_device_option
            else MetaXCommon.build_pcie_mxvs_cmd)
        cmd = self.command.run_cmd(
            command_builder(self.board_id, benchmark_cmd),
            ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error(
                f"Run PCIe {benchmark_name} bandwidth benchmark failed "
                f"({run}/{self.repeat_times}).")
            return False

        benchmark_results = self._parse_benchmark_output(cmd[0], pattern)
        if not benchmark_results:
            self.logger.error(
                f"No PCIe {benchmark_name} bandwidth result parsed "
                f"({run}/{self.repeat_times}).")
            return False

        for result in benchmark_results:
            if result_precheck is not None and not result_precheck(result):
                return False
            if not self._check_result(
                    result, self.pcie_theoretical_bandwidths, run,
                    raw_tolerance, effective_tolerance,
                    theoretical_multiplier):
                return False

        return True

    def _run_repeated(
            self,
            name: str,
            once_runner: Callable[[int], bool]) -> bool:
        """连续执行 ``repeat_times`` 次带宽基准测试。

        once_runner 为单次迭代回调，返回 False 中止；全部通过返回 True。
        """
        self.logger.info(f"Check MetaX GPU PCIe {name} bandwidth.")
        for run in range(1, self.repeat_times + 1):
            if not once_runner(run):
                return False
        self.logger.info(
            f"MetaX GPU PCIe {name} bandwidth test succeed.")
        return True

    def check_p2p_unidirectional_bandwidth(self) -> bool:
        """测试 MetaX GPU P2P 单向带宽。"""
        if not self.get_pcie_theoretical_bandwidths():
            return False

        def topology_precheck(result: dict[str, Any]) -> bool:
            if result["topology"].lower() != "pcie":
                self.logger.error(
                    f"Unsupported P2P topology {result['topology']}, "
                    f"only PCIe is implemented.")
                return False
            return True

        return self._run_repeated(
            "P2P unidirectional",
            lambda run: self._run_once(
                run,
                "P2P unidirectional",
                "p2p --unidirection",
                self.P2P_RESULT_PATTERN,
                self.unidirectional_raw_tolerance,
                self.unidirectional_effective_tolerance,
                1.0,
                topology_precheck))

    def check_bandwidth(self) -> bool:
        """测试 MetaX GPU PCIe 单向、双向及 P2P 带宽。"""
        if not self.get_pcie_theoretical_bandwidths():
            return False

        if not self._run_repeated(
                "unidirectional",
                lambda run: self._run_once(
                    run,
                    "unidirectional",
                    "pcie benchmark unidirection",
                    self.RESULT_PATTERN,
                    self.unidirectional_raw_tolerance,
                    self.unidirectional_effective_tolerance,
                    1.0)):
            return False

        if not self._run_repeated(
                "bidirectional",
                lambda run: self._run_once(
                    run,
                    "bidirectional",
                    "pcie benchmark bidirection",
                    self.RESULT_PATTERN,
                    self.bidirectional_raw_tolerance,
                    self.bidirectional_effective_tolerance,
                    2.0,
                    use_global_device_option=True)):
            return False

        if not self.check_p2p_unidirectional_bandwidth():
            return False

        return True
