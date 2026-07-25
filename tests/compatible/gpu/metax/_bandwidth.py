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
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Optional

from hwcompatible.command import Command

from ._common import MetaXCommon

if TYPE_CHECKING:
    from hwcompatible.log import Logger


@dataclass(frozen=True)
class _BandwidthBenchmarkConfig:
    name: str
    command: str
    pattern: "re.Pattern[str]"
    raw_tolerance: float
    effective_tolerance: float
    theoretical_multiplier: float
    result_precheck: Optional[Callable[[dict[str, Any]], bool]] = None
    use_global_device_option: bool = False


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
            run: int,
            config: _BandwidthBenchmarkConfig) -> bool:
        board_ids = self._get_result_board_ids(result)
        if not board_ids:
            self.logger.error(
                f"No board ID found in PCIe bandwidth result: "
                f"{result['src']} {result['direction']} {result['dst']} "
                f"({run}/{self.repeat_times}).")
            return False

        missing_board_ids = [
            board_id for board_id in board_ids
            if board_id not in self.pcie_theoretical_bandwidths
        ]
        if missing_board_ids:
            self.logger.error(
                f"No PCIe theoretical bandwidth found for boards: "
                f"{', '.join(missing_board_ids)} "
                f"({run}/{self.repeat_times}).")
            return False

        theoretical_bandwidth = min(
            self.pcie_theoretical_bandwidths[board_id]
            for board_id in board_ids)
        theoretical_bandwidth *= config.theoretical_multiplier
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
        if raw_deviation > config.raw_tolerance:
            self.logger.error(
                f"PCIe RAW bandwidth deviation exceeds "
                f"{config.raw_tolerance * 100:.2f}% for {result['src']} "
                f"{result['direction']} {result['dst']}: "
                f"raw {result['raw']:.2f} GB/s, "
                f"theoretical {theoretical_bandwidth:.2f} GB/s, "
                f"deviation {raw_deviation * 100:.2f}% "
                f"({run}/{self.repeat_times}).")
            return False
        if effective_deviation > config.effective_tolerance:
            self.logger.error(
                f"PCIe EFFECTIVE bandwidth deviation exceeds "
                f"{config.effective_tolerance * 100:.2f}% "
                f"for {result['src']} "
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
            config: _BandwidthBenchmarkConfig
            ) -> bool:
        """执行一次 PCIe 带宽基准测试。

        run 为 1 起始的迭代序号；config 封装子命令、解析模式、容差、
        理论带宽倍率与设备选择方式。
        """
        self.logger.info(
            f"Run PCIe {config.name} bandwidth benchmark "
            f"({run}/{self.repeat_times}).")
        command_builder = (
            MetaXCommon.build_mxvs_cmd
            if config.use_global_device_option
            else MetaXCommon.build_pcie_mxvs_cmd)
        cmd = self.command.run_cmd(
            command_builder(self.board_id, config.command),
            ignore_errors=True)
        if cmd[2] != 0:
            self.logger.error(
                f"Run PCIe {config.name} bandwidth benchmark failed "
                f"({run}/{self.repeat_times}).")
            return False

        benchmark_results = self._parse_benchmark_output(
            cmd[0], config.pattern)
        if not benchmark_results:
            self.logger.error(
                f"No PCIe {config.name} bandwidth result parsed "
                f"({run}/{self.repeat_times}).")
            return False

        for result in benchmark_results:
            if (config.result_precheck is not None
                    and not config.result_precheck(result)):
                return False
            if not self._check_result(result, run, config):
                return False

        return True

    def _run_repeated(
            self,
            config: _BandwidthBenchmarkConfig) -> bool:
        """按 config 连续执行 ``repeat_times`` 次带宽基准测试。

        单次迭代返回 False 时中止；全部通过时返回 True。
        """
        self.logger.info(
            f"Check MetaX GPU PCIe {config.name} bandwidth.")
        for run in range(1, self.repeat_times + 1):
            if not self._run_once(run, config):
                return False
        self.logger.info(
            f"MetaX GPU PCIe {config.name} bandwidth test succeed.")
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

        return self._run_repeated(_BandwidthBenchmarkConfig(
            name="P2P unidirectional",
            command="p2p --unidirection",
            pattern=self.P2P_RESULT_PATTERN,
            raw_tolerance=self.unidirectional_raw_tolerance,
            effective_tolerance=self.unidirectional_effective_tolerance,
            theoretical_multiplier=1.0,
            result_precheck=topology_precheck))

    def check_bandwidth(self) -> bool:
        """测试 MetaX GPU PCIe 单向、双向及 P2P 带宽。"""
        if not self.get_pcie_theoretical_bandwidths():
            return False

        if not self._run_repeated(_BandwidthBenchmarkConfig(
                name="unidirectional",
                command="pcie benchmark unidirection",
                pattern=self.RESULT_PATTERN,
                raw_tolerance=self.unidirectional_raw_tolerance,
                effective_tolerance=self.unidirectional_effective_tolerance,
                theoretical_multiplier=1.0)):
            return False

        if not self._run_repeated(_BandwidthBenchmarkConfig(
                name="bidirectional",
                command="pcie benchmark bidirection",
                pattern=self.RESULT_PATTERN,
                raw_tolerance=self.bidirectional_raw_tolerance,
                effective_tolerance=self.bidirectional_effective_tolerance,
                theoretical_multiplier=2.0,
                use_global_device_option=True)):
            return False

        if not self.check_p2p_unidirectional_bandwidth():
            return False

        return True
