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
import shlex
from typing import TYPE_CHECKING, Optional

from hwcompatible.command import Command

if TYPE_CHECKING:
    from hwcompatible.log import Logger


class MetaXMCCLTest():
    def __init__(self, logger: "Logger", command: Command):
        self.logger: "Logger" = logger
        self.command: Command = command

    def _parse_mccl_output(
            self, output: str,
            expected_benches: list[str]) -> Optional[dict[tuple[str, int, str], dict[str, float]]]:
        bench_pattern = re.compile(r"^The test is\s+(\S+),")
        oob_pattern = re.compile(r"^#\s*Out of bounds values\s*:\s*(.+)$")
        expected_bench_set = set(expected_benches)
        current_bench = None
        ok_oob_benches = set()
        results = {}

        for line in output.splitlines():
            stripped_line = line.strip()
            bench_match = bench_pattern.match(stripped_line)
            if bench_match:
                current_bench = bench_match.group(1)
                continue

            if current_bench not in expected_bench_set:
                continue

            oob_match = oob_pattern.match(stripped_line)
            if oob_match:
                oob_result = oob_match.group(1).strip()
                if oob_result.endswith("OK"):
                    ok_oob_benches.add(current_bench)
                else:
                    self.logger.error(
                        f"MCCL out-of-bounds check failed for {current_bench}: "
                        f"{oob_result}.")
                    return None
                continue

            parts = stripped_line.split()
            if len(parts) < 12 or not parts[0].isdigit():
                continue

            try:
                size = int(parts[0])
                out_of_place_time = float(parts[-8])
                out_of_place_algbw = float(parts[-7])
                out_of_place_busbw = float(parts[-6])
                in_place_time = float(parts[-4])
                in_place_algbw = float(parts[-3])
                in_place_busbw = float(parts[-2])
            except ValueError:
                continue

            results[(current_bench, size, "out-of-place")] = {
                "time": out_of_place_time,
                "algbw": out_of_place_algbw,
                "busbw": out_of_place_busbw,
            }
            results[(current_bench, size, "in-place")] = {
                "time": in_place_time,
                "algbw": in_place_algbw,
                "busbw": in_place_busbw,
            }

        missing_oob_benches = [
            bench for bench in expected_benches
            if bench not in ok_oob_benches
        ]
        if missing_oob_benches:
            self.logger.error(
                f"MCCL out-of-bounds OK result missing for benchmarks: "
                f"{', '.join(missing_oob_benches)}.")
            return None

        missing_result_benches = [
            bench for bench in expected_benches
            if not any(key[0] == bench for key in results)
        ]
        if missing_result_benches:
            self.logger.error(
                f"MCCL performance result missing for benchmarks: "
                f"{', '.join(missing_result_benches)}.")
            return None

        return results

    def _check_mccl_stability(
            self,
            run_results: list[dict[tuple[str, int, str], dict[str, float]]]) -> bool:
        thresholds = {
            "time": 0.20,
            "algbw": 0.02,
            "busbw": 0.02,
        }
        metric_names = {
            "time": "time",
            "algbw": "algorithm bandwidth",
            "busbw": "bus bandwidth",
        }
        expected_keys = set(run_results[0])

        for run_index, result in enumerate(run_results, start=1):
            missing_keys = expected_keys - set(result)
            extra_keys = set(result) - expected_keys
            if missing_keys or extra_keys:
                self.logger.error(
                    f"MCCL result keys mismatch on run {run_index}: "
                    f"missing {len(missing_keys)}, extra {len(extra_keys)}.")
                return False

        for bench, size, mode in sorted(expected_keys):
            for metric, threshold in thresholds.items():
                metric_name = metric_names.get(metric, metric)
                values = [
                    result[(bench, size, mode)][metric]
                    for result in run_results
                ]
                average = sum(values) / len(values)
                if average == 0:
                    if any(value != 0 for value in values):
                        self.logger.error(
                            f"MCCL {metric_name} unstable for {bench} "
                            f"size {size} {mode}: values "
                            f"{', '.join(f'{value:.4f}' for value in values)}, "
                            f"average {average:.4f}.")
                        return False
                    continue

                max_deviation = max(
                    abs(value - average) / average for value in values)
                if max_deviation > threshold:
                    self.logger.error(
                        f"MCCL {metric_name} fluctuation exceeds "
                        f"{threshold * 100:.2f}% for {bench} size {size} "
                        f"{mode}: values "
                        f"{', '.join(f'{value:.4f}' for value in values)}, "
                        f"average {average:.4f}, max deviation "
                        f"{max_deviation * 100:.2f}%.")
                    return False

        return True

    def mccl_test(self, gpu_id: str) -> bool:
        """在单张 GPU 上运行 3 次 MetaX MCCL 性能基准测试。

        固定 GPU_NUM=1 并通过 CUDA_VISIBLE_DEVICES 限定到 oech 选中的设备。
        """
        repeat_times = 3
        bench_names = [
            "all_reduce_perf",
            "all_gather_perf",
            "alltoall_perf",
            "broadcast_perf",
            "gather_perf",
            "reduce_perf",
            "reduce_scatter_perf",
            "scatter_perf",
            "sendrecv_perf",
        ]
        mccl_cmd = (
            "export MACA_PATH=/opt/maca; "
            "export LD_LIBRARY_PATH=${MACA_PATH}/lib:${MACA_PATH}/ompi/lib; "
            "export FORCE_ACTIVE_WAIT=2; "
            f"export CUDA_VISIBLE_DEVICES={gpu_id}; "
            "GPU_NUM=1; "
            "TEST_DIR=${MACA_PATH}/samples/mccl_tests/perf/mccl_perf; "
            f"BENCH_NAMES='{' '.join(bench_names)}'; "
            "MPI_PROCESS_NUM=${GPU_NUM}; "
            "MPI_RUN_OPT='--allow-run-as-root -mca pml ^ucx -mca osc ^ucx "
            "-mca btl ^openib'; "
            "for BENCH in ${BENCH_NAMES}; do "
            "echo -n \"The test is ${BENCH}, the maca version is \" && "
            "realpath ${MACA_PATH}; "
            "${MACA_PATH}/ompi/bin/mpirun -np ${MPI_PROCESS_NUM} "
            "${MPI_RUN_OPT} ${TEST_DIR}/${BENCH} -b 1K -e 1G "
            "-d bfloat16 -f 2 -g 1 -n 10; "
            "done"
        )

        self.logger.info(
            f"Run MetaX MCCL performance test on GPU {gpu_id} (GPU_NUM=1).")
        run_results = []
        for run in range(1, repeat_times + 1):
            self.logger.info(
                f"Run MCCL performance test ({run}/{repeat_times}).")
            cmd = self.command.run_cmd(
                f"bash -c {shlex.quote(mccl_cmd)}",
                ignore_errors=True)
            if cmd[2] != 0:
                self.logger.error(
                    f"Run MCCL performance test failed "
                    f"({run}/{repeat_times}).")
                return False

            output = cmd[0]
            if len(cmd) > 1 and cmd[1]:
                output = f"{output}\n{cmd[1]}"
            parsed_result = self._parse_mccl_output(output, bench_names)
            if parsed_result is None:
                self.logger.error(
                    f"Parse MCCL performance test result failed "
                    f"({run}/{repeat_times}).")
                return False
            run_results.append(parsed_result)

        if not self._check_mccl_stability(run_results):
            return False

        self.logger.info("MetaX MCCL performance test succeed.")
        return True
