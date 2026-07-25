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
# Desc: MetaX GPU checks

import os
import re
from typing import TYPE_CHECKING, Callable, Optional

from hwcompatible.command import Command

from ._common import C500_BIOS_PATH, MetaXCommon
from ._system_prepare import MetaXSystemPrepare

if TYPE_CHECKING:
    from hwcompatible.log import Logger


class MetaXCheck():
    """Run MetaX GPU firmware, state, and performance checks."""

    def __init__(
            self,
            logger: "Logger",
            command: Command,
            system_prepare_runner: MetaXSystemPrepare):
        self.logger: "Logger" = logger
        self.command: Command = command
        self.system_prepare_runner = system_prepare_runner
        self.board_id: Optional[str] = None

    def _run_repeated_mxvs_test(
            self,
            test_name: str,
            benchmark_name: str,
            subcommand: str,
            repeat_times: int,
            result_checker: Callable[[str, int, int], bool]) -> bool:
        """重复执行同一 mxvs 基准测试并校验结果。"""
        self.logger.info(f"Check {test_name}.")
        for run in range(1, repeat_times + 1):
            self.logger.info(
                f"Run {benchmark_name} ({run}/{repeat_times}).")
            command_text = MetaXCommon.build_mxvs_cmd(
                self.board_id, subcommand)
            cmd = self.command.run_cmd(command_text, ignore_errors=True)
            if cmd[2] != 0:
                self.logger.error(
                    f"Run {benchmark_name} failed ({run}/{repeat_times}).")
                return False
            if not result_checker(cmd[0], run, repeat_times):
                return False

        self.logger.info(f"{test_name} test succeed.")
        return True

    def _get_latest_c500_bios_file(self) -> Optional[tuple[str, str]]:
        """获取最新的 MetaX C500 BIOS 文件及其版本。

        返回 (BIOS 文件名, 期望 BIOS 版本)；未找到时返回 None。
        """
        bios_pattern = re.compile(
            r"^mxvbios-(?P<version>\d+(?:\.\d+)+)(?:-[^-]+)*-C500\.bin$")

        if not os.path.isdir(C500_BIOS_PATH):
            self.logger.error(
                f"MetaX C500 BIOS directory does not exist: {C500_BIOS_PATH}.")
            return None

        bios_files = []
        for filename in os.listdir(C500_BIOS_PATH):
            match = bios_pattern.match(filename)
            if (match
                    and os.path.isfile(os.path.join(C500_BIOS_PATH, filename))):
                bios_files.append((filename, match.group("version")))

        if not bios_files:
            self.logger.error(
                f"No MetaX C500 BIOS file found in {C500_BIOS_PATH}.")
            return None

        def bios_sort_key(filename: str):
            return [
                int(part) if part.isdigit() else part
                for part in re.split(r"(\d+)", filename)
            ]

        bios_file, expected_bios_version = sorted(
            bios_files, key=lambda item: bios_sort_key(item[0]))[-1]
        self.logger.info(f"Use MetaX C500 BIOS file: {bios_file}.")
        return bios_file, expected_bios_version

    def check_card_bios_version(self) -> bool:
        """将所有 MetaX C500 GPU 的 BIOS 版本与最新固件比对。

        不会自动升级 BIOS；任一 GPU 版本过旧时提示用户手动升级并终止测试，全部最新返回 True。
        """
        self.logger.info("Check MetaX GPU BIOS version.")
        bios_info = self._get_latest_c500_bios_file()
        if bios_info is None:
            return False

        _, expected_bios_version = bios_info
        card_versions = self.system_prepare_runner.get_card_versions()
        if card_versions is None:
            return False

        bios_versions = [
            (gpu_id, versions.get("BIOS"))
            for gpu_id, versions in sorted(card_versions.items())
        ]
        if not bios_versions:
            self.logger.error("No MetaX GPU BIOS version found.")
            return False

        missing_gpu_ids = [
            gpu_id for gpu_id, bios_version in bios_versions
            if not bios_version
        ]
        if missing_gpu_ids:
            self.logger.error(
                f"No MetaX GPU BIOS version found on GPU: "
                f"{', '.join(str(gpu_id) for gpu_id in missing_gpu_ids)}.")
            return False

        outdated_versions = [
            (gpu_id, bios_version)
            for gpu_id, bios_version in bios_versions
            if bios_version != expected_bios_version
        ]
        if outdated_versions:
            outdated_text = ", ".join(
                f"GPU#{gpu_id}={bios_version}"
                for gpu_id, bios_version in outdated_versions
            )
            self.logger.error(
                "MetaX GPU BIOS version is outdated, please upgrade the BIOS "
                f"manually and rerun the test. Latest version: "
                f"{expected_bios_version}, outdated: "
                f"{outdated_text}.")
            return False

        self.logger.info(
            f"MetaX GPU BIOS version check succeed, all cards are "
            f"{expected_bios_version}.")
        return True

    def check_ecc(self) -> bool:
        def get_ecc_states():
            cmd = self.command.run_cmd(
                "mx-smi --show-ecc-state", ignore_errors=True)
            if cmd[2] != 0:
                self.logger.error("Get MetaX GPU ECC state failed.")
                return None

            ecc_states = []
            for line in cmd[0].splitlines():
                line = line.strip()
                if line.lower().startswith("state") and ":" in line:
                    ecc_states.append(line.split(":", 1)[1].strip())

            if not ecc_states:
                self.logger.error("No MetaX GPU ECC state found.")
                return None
            return ecc_states

        self.logger.info("Check MetaX GPU ECC state.")
        ecc_states = get_ecc_states()
        if ecc_states is None:
            return False

        disabled_gpu_ids = [
            gpu_id for gpu_id, state in enumerate(ecc_states)
            if state.lower().startswith("disable")
        ]
        if disabled_gpu_ids:
            self.logger.warning(
                f"MetaX GPU ECC is disabled on GPU: "
                f"{', '.join(str(gpu_id) for gpu_id in disabled_gpu_ids)}. "
                f"Enable ECC for these GPUs.")
            for gpu_id in disabled_gpu_ids:
                cmd = self.command.run_cmd(
                    f"mx-smi --set-ecc-state 1 -i {gpu_id}",
                    ignore_errors=True)
                if cmd[2] != 0:
                    self.logger.error(
                        f"Set MetaX GPU {gpu_id} ECC state failed.")
                    return False
            for gpu_id in disabled_gpu_ids:
                if not MetaXCommon.warm_reset_metax_gpu(
                        self.command, self.logger, str(gpu_id)):
                    return False

            ecc_states = get_ecc_states()
            if ecc_states is None:
                return False
            if any(state.lower().startswith("disable") for state in ecc_states):
                self.logger.error(
                    f"MetaX GPU ECC state is still disabled after enabling: "
                    f"{', '.join(ecc_states)}.")
                return False

        if any(not state.lower().startswith("enable") for state in ecc_states):
            self.logger.error(
                f"Unexpected MetaX GPU ECC state: {', '.join(ecc_states)}.")
            return False

        self.logger.info("MetaX GPU ECC state is enabled.")
        return True

    def check_pcie_eye(self) -> bool:
        """测试 MetaX GPU PCIe 眼图，执行 3 次 ``mxvs eye``。

        每条结果需满足 WIDTH > 0.3 UI 且 HEIGHT > 15 mV 方为通过。
        """
        repeat_times = 3
        width_threshold = 0.3
        height_threshold = 15.0
        eye_pattern = re.compile(
            r"^\s*(\d+)\s+([0-9a-fA-F:.]+)\s+(\d+)\s+(\d+)\s+"
            r"([0-9]+(?:\.[0-9]+)?)\s+mV\s+"
            r"([0-9]+(?:\.[0-9]+)?)\s+UI\s*$")

        def check_result(output: str, run: int, total: int) -> bool:
            eye_results = []
            skipped_other_board = 0
            for line in output.splitlines():
                match = eye_pattern.match(line)
                if not match:
                    continue
                dev_id, bdf, phy, lane, height, width = match.groups()
                # 只保留选中 board 的眼图结果，确保只测一张卡
                if self.board_id is not None and dev_id != self.board_id:
                    skipped_other_board += 1
                    continue
                eye_results.append({
                    "dev_id": dev_id,
                    "bdf": bdf,
                    "phy": phy,
                    "lane": lane,
                    "height": float(height),
                    "width": float(width),
                })

            if skipped_other_board:
                self.logger.warning(
                    f"Skipped {skipped_other_board} PCIe eye result line(s) "
                    f"not belonging to board {self.board_id} "
                    f"({run}/{total}).")

            if not eye_results:
                self.logger.error(
                    f"No PCIe eye result parsed for board {self.board_id} "
                    f"({run}/{total}).")
                return False

            for result in eye_results:
                self.logger.info(
                    f"  Dev {result['dev_id']} ({result['bdf']}) "
                    f"PHY {result['phy']} lane {result['lane']} PCIe eye: "
                    f"height {result['height']:.2f} mV, "
                    f"width {result['width']:.2f} UI ({run}/{total}).")

            failed = [
                result for result in eye_results
                if result["width"] <= width_threshold
                or result["height"] <= height_threshold
            ]
            if failed:
                failed_descriptions = [
                    f"dev {result['dev_id']} ({result['bdf']}) "
                    f"PHY {result['phy']} lane {result['lane']} "
                    f"height {result['height']:.2f} mV "
                    f"width {result['width']:.2f} UI"
                    for result in failed
                ]
                self.logger.error(
                    f"PCIe eye result below threshold "
                    f"(height {height_threshold:.2f} mV, "
                    f"width {width_threshold:.2f} UI): "
                    f"{', '.join(failed_descriptions)} "
                    f"({run}/{total}).")
                return False

            return True

        return self._run_repeated_mxvs_test(
            "MetaX GPU PCIe eye", "PCIe eye test", "eye", repeat_times,
            check_result)

    def check_hbm(self) -> bool:
        """测试 MetaX GPU HBM 带宽，连续执行 3 次 ``mxvs memory benchmark``。

        每次运行中各 GPU 的带宽需大于 1600 GB/s 方为通过。
        """
        bandwidth_threshold = 1600.0
        repeat_times = 3
        bandwidth_pattern = re.compile(
            r"^\s*(\d+)\s+([0-9a-fA-F:.]+)\s+\d+\s+([\d.]+)\s+GB/s\s*$")

        def check_result(output: str, run: int, total: int) -> bool:
            bandwidths = {}
            for line in output.splitlines():
                match = bandwidth_pattern.match(line)
                if match:
                    board_id = match.group(1)
                    bdf = match.group(2)
                    bandwidth = float(match.group(3))
                    bandwidths[board_id] = (bdf, bandwidth)

            if not bandwidths:
                self.logger.error(
                    f"No HBM bandwidth result parsed ({run}/{total}).")
                return False

            for board_id, (bdf, bandwidth) in bandwidths.items():
                self.logger.info(
                    f"  Board {board_id} ({bdf}) HBM bandwidth: "
                    f"{bandwidth:.2f} GB/s ({run}/{total}).")

            failed = {
                board_id: bandwidth
                for board_id, (bdf, bandwidth) in bandwidths.items()
                if bandwidth <= bandwidth_threshold
            }
            if failed:
                failed_text = ", ".join(
                    f"{bid}={bw:.2f} GB/s" for bid, bw in failed.items()
                )
                self.logger.error(
                    f"HBM bandwidth below threshold "
                    f"({bandwidth_threshold:.2f} GB/s) on boards: "
                    f"{failed_text} "
                    f"({run}/{total}).")
                return False

            return True

        return self._run_repeated_mxvs_test(
            "MetaX GPU HBM bandwidth", "HBM benchmark", "memory benchmark",
            repeat_times, check_result)

    def check_ops(self) -> bool:
        """测试 MetaX GPU 算子性能，连续执行 3 次 ``mxvs ops``。

        每次运行中各 GPU 的算子性能需落在理想值 1% 偏差范围内方为通过。
        """
        repeat_times = 3
        tolerance = 0.01
        ideal_values = {
            "int8": 480.0,
            "bf16": 240.0,
            "fp16_matrix": 240.0,
            "fp32_vector": 15.0,
            "fp32_matrix": 30.0,
            "tf32": 120.0,
        }
        result_pattern = re.compile(
            r"^\s*(\d+)\s+([0-9a-fA-F:.]+)\s+(\S+)\s+([0-9]+(?:\.[0-9]+)?)\s*$")
        gpu_id_pattern = re.compile(r"^\s*GPU ID\s+(\d+)\s*$")

        def check_result(output: str, run: int, total: int) -> bool:
            gpu_ids = set()
            ops_results = {}
            for line in output.splitlines():
                gpu_match = gpu_id_pattern.match(line)
                if gpu_match:
                    gpu_ids.add(gpu_match.group(1))
                    continue

                match = result_pattern.match(line)
                if not match:
                    continue

                board_id, bdf, op_name, value = match.groups()
                if op_name not in ideal_values:
                    continue
                ops_results.setdefault(board_id, {})[op_name] = (
                    bdf, float(value))

            if not ops_results:
                self.logger.error(
                    f"No operator performance result parsed "
                    f"({run}/{total}).")
                return False

            missing_boards = sorted(gpu_ids - set(ops_results.keys()), key=int)
            if missing_boards:
                self.logger.error(
                    f"No operator performance result parsed for boards: "
                    f"{', '.join(missing_boards)} ({run}/{total}).")
                return False

            for board_id in sorted(ops_results.keys(), key=int):
                board_results = ops_results[board_id]
                missing_ops = [
                    op_name for op_name in ideal_values
                    if op_name not in board_results
                ]
                if missing_ops:
                    self.logger.error(
                        f"Operator performance result missing on board "
                        f"{board_id}: {', '.join(missing_ops)} "
                        f"({run}/{total}).")
                    return False

                for op_name, ideal_value in ideal_values.items():
                    bdf, actual_value = board_results[op_name]
                    deviation = abs(actual_value - ideal_value) / ideal_value
                    self.logger.info(
                        f"  Board {board_id} ({bdf}) {op_name} performance: "
                        f"{actual_value:.2f}, ideal: {ideal_value:.2f}, "
                        f"deviation: {deviation * 100:.2f}% "
                        f"({run}/{total}).")
                    if deviation >= tolerance:
                        self.logger.error(
                            f"Operator performance deviation exceeds "
                            f"{tolerance * 100:.2f}% on board {board_id} "
                            f"({bdf}): {op_name} actual {actual_value:.2f}, "
                            f"ideal {ideal_value:.2f}, deviation "
                            f"{deviation * 100:.2f}% ({run}/{total}).")
                        return False

            return True

        return self._run_repeated_mxvs_test(
            "MetaX GPU operator performance",
            "operator performance benchmark", "ops", repeat_times,
            check_result)
