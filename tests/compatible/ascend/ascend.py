#!/usr/bin/env python3

# Copyright (c) 2020-2026 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @meitingli
# Create: 2022-10-15
# Desc: Ascend NPU unified test. Runs once no matter how many cards exist.

import argparse
import json
import os
import re
import shlex
from typing import TYPE_CHECKING, ClassVar

from map import NPU_ARCH_MAP, THEORETICAL_SPECS

from hwcompatible.command import Command
from hwcompatible.constants import ASCEND_PCI_IDS
from hwcompatible.test import Test

if TYPE_CHECKING:
    from hwcompatible.log import Logger


# Environment setup commands required to access CANN / ascend-dmi toolchain.
_ASCEND_ENV_SETUP = (
    "source /usr/local/Ascend/cann/set_env.sh && "
    "source /usr/local/Ascend/toolbox/set_env.sh"
)


class _AscendCommandRunner:
    _ASCEND_ENV_SETUP = _ASCEND_ENV_SETUP

    def __init__(self, command: Command):
        self.command: Command = command

    def run_cmd(
        self,
        command: str,
        ignore_errors: bool = False,
        terminal_print: bool = False,
        timeout=None,
    ):
        # Run a command with the Ascend CANN/toolbox environment sourced.
        command_with_env = f"{self._ASCEND_ENV_SETUP} && {command}"
        return self.command.run_cmd(
            f"bash -c {shlex.quote(command_with_env)}",
            ignore_errors=ignore_errors,
            log_print=True,
            terminal_print=terminal_print,
            timeout=timeout,
        )


class AscendVersion(_AscendCommandRunner):
    def __init__(self, command, logger=None):
        super().__init__(command)
        self.logger: Logger = logger or command.logger

    @staticmethod
    def _find_status_items(value, path="root"):
        status_items = []
        if isinstance(value, dict):
            if "status" in value:
                status_items.append((path, value))

            for key, item in value.items():
                status_items.extend(
                    AscendVersion._find_status_items(item, f"{path}.{key}")
                )
        elif isinstance(value, list):
            for index, item in enumerate(value):
                status_items.extend(
                    AscendVersion._find_status_items(
                        item, f"{path}[{index}]"
                    )
                )
        return status_items

    def version_check(self):
        self.logger.info("Check Ascend version compatibility.")
        output, error, status = self.run_cmd(
            "ascend-dmi -c --fmt json", ignore_errors=True
        )
        if status != 0:
            details = output.strip() or error.strip() or "No output"
            self.logger.error(
                "Ascend version check command failed:\n"
                f"{details}"
            )
            return False

        compatibility_result = json.loads(output)

        status_items = self._find_status_items(compatibility_result)
        if not status_items:
            self.logger.error(
                "Ascend version check returned no status items:\n"
                f"{output.strip() or 'No output'}"
            )
            return False

        failed_items = [
            item for item in status_items if item[1]["status"] != "OK"
        ]
        if not failed_items:
            self.logger.info("Ascend version compatibility check succeed.")
            return True

        details = "\n".join(
            f"{path}: {json.dumps(item, ensure_ascii=False)}"
            for path, item in failed_items
        )
        self.logger.error(
            "Ascend version check non-OK items:\n"
            f"{details}"
        )
        return False


class AscendHealthCheck(_AscendCommandRunner):
    _CANN_INSTALL_PATH = "/usr/local/Ascend"

    def __init__(self, command, device_id=0, logger=None):
        super().__init__(command)
        self.device_id = device_id
        self.logger: Logger = logger or command.logger

    def _parse_diagnose_result(self, output, item):
        # ascend-dmi -dg prints "<section>:\n    <item>:\n        <status>".
        match = re.search(
            rf"(?m)^[ \t]*{re.escape(item)}[ \t]*:[ \t]*\n[ \t]+(\S+)",
            output,
        )
        return match.group(1) if match else None

    def _run_diagnose(self, item, extra_args, expected):
        cmd = f"ascend-dmi -dg {extra_args} -d {self.device_id}"
        output, error, status = self.run_cmd(cmd, ignore_errors=True)
        if status != 0:
            self.logger.error(
                f"Ascend health check '{item}' of device {self.device_id} "
                f"command failed:\n"
                f"{output.strip() or error.strip() or 'No output'}"
            )
            return False

        result = self._parse_diagnose_result(output, item)
        if result is None:
            self.logger.error(
                f"Ascend health check '{item}' of device {self.device_id} "
                f"returned no result:\n"
                f"{output.strip() or 'No output'}"
            )
            return False

        if result != expected:
            self.logger.error(
                f"Ascend health check '{item}' of device {self.device_id} "
                f"got '{result}', expected '{expected}'"
            )
            return False

        self.logger.info(
            f"Ascend health check '{item}' of device {self.device_id}: "
            f"{result}",
        )
        return True

    def check_cann_compatibility(self):
        return self._run_diagnose(
            "cann", f"-i cann -p {self._CANN_INSTALL_PATH}", "PASS"
        )

    def check_device(self):
        return self._run_diagnose("device", "-i device", "HEALTH")

    def check_driver(self):
        return self._run_diagnose("driver", "-i driver", "HEALTH")

    def check_hbm(self):
        return self._run_diagnose("hbm", "-i hbm", "PASS")

    def health_check(self):
        self.logger.info(
            f"Check Ascend device {self.device_id} health.")
        if not all([
            self.check_cann_compatibility(),
            self.check_device(),
            self.check_driver(),
            self.check_hbm(),
        ]):
            return False

        self.logger.info(
            f"Ascend device {self.device_id} health check succeed.")
        return True


class AscendTransportCheck(_AscendCommandRunner):
    _EXECUTE_TIMES = 100
    _KB = 1024
    _MB = 1024 * 1024
    _TRANSFER_SIZES = (512 * _KB, 2 * _MB, 512 * _MB)
    _DIRECTIONS = ("h2d", "d2h")
    # Per-size deviation tolerance: 512K < 30%, 2M < 20%, 512M < 10%.
    _SIZE_TOLERANCES: ClassVar[dict] = {
        512 * _KB: 0.30,
        2 * _MB: 0.20,
        512 * _MB: 0.10,
    }

    def __init__(self, command, device_id=0, pcie_speed=None,
                 pcie_lanes=None, logger=None):
        super().__init__(command)
        self.device_id = device_id
        self.pcie_speed = pcie_speed
        self.pcie_lanes = pcie_lanes
        self.logger: Logger = logger or command.logger

    @staticmethod
    def _parse_bandwidth(value_str):
        match = re.search(
            r"([\d.]+)\s*GB/s", value_str)
        return float(match.group(1)) if match else None

    def _run_bandwidth_test(self, direction, size):
        self.logger.info(
            f"Run Ascend transport check '{direction}' size {size} "
            f"on device {self.device_id}.")
        cmd = (
            f"ascend-dmi --bw -t {direction} -d {self.device_id} "
            f"--et {self._EXECUTE_TIMES} -s {size} -q --fmt json"
        )
        output, error, status = self.run_cmd(cmd, ignore_errors=True)
        if status != 0:
            self.logger.error(
                f"Ascend transport check '{direction}' size {size} of "
                f"device {self.device_id} command failed:\n"
                f"{output.strip() or error.strip() or 'No output'}"
            )
            return False

        result = json.loads(output)

        bandwidths = result.get("bandwidths")
        if not isinstance(bandwidths, list) or not bandwidths:
            self.logger.error(
                f"Ascend transport check '{direction}' size {size} of "
                f"device {self.device_id} returned no bandwidths:\n"
                f"{output.strip() or 'No output'}"
            )
            return False

        entry = bandwidths[0]
        results = entry.get("results")
        if not isinstance(results, list) or not results:
            self.logger.error(
                f"Ascend transport check '{direction}' size {size} of "
                f"device {self.device_id} returned no results:\n"
                f"{output.strip() or 'No output'}"
            )
            return False

        bw_str = results[0].get("bandwidth", "")
        bandwidth = self._parse_bandwidth(bw_str)
        if bandwidth is None:
            self.logger.error(
                f"Ascend transport check '{direction}' size {size} of "
                f"device {self.device_id} returned unparseable bandwidth "
                f"'{bw_str}':\n"
                f"{output.strip() or 'No output'}"
            )
            return False

        elapsed = results[0].get("elapsed_time", "unknown")
        if self.pcie_speed is None or self.pcie_lanes is None:
            self.logger.error(
                f"Ascend transport check '{direction}' size {size} of "
                f"device {self.device_id}: PCIe speed/lanes not "
                f"provided")
            return False
        from helper import pcie_theoretical_bandwidth
        theoretical = pcie_theoretical_bandwidth(
            self.pcie_speed, self.pcie_lanes)
        tolerance = self._SIZE_TOLERANCES.get(size, 0.30)
        diff = (theoretical - bandwidth) / theoretical
        if diff > tolerance:
            self.logger.error(
                f"Ascend transport check '{direction}' size {size} of "
                f"device {self.device_id}: {bandwidth:.2f} GB/s deviates "
                f"from theoretical {theoretical:.2f} GB/s by {diff:.1%} "
                f"(exceeds {tolerance:.0%} tolerance)"
            )
            return False

        self.logger.info(
            f"Ascend transport check '{direction}' size {size} of "
            f"device {self.device_id}: {bandwidth:.2f} GB/s "
            f"(theoretical {theoretical:.2f}, diff {diff:.1%}, "
            f"elapsed {elapsed})",
            terminal_print=False,
        )
        return True

    def transport_check(self):
        self.logger.info(
            f"Check Ascend device {self.device_id} PCIe transport "
            f"bandwidth.")
        for direction in self._DIRECTIONS:
            for size in self._TRANSFER_SIZES:
                if not self._run_bandwidth_test(direction, size):
                    return False

        self.logger.info(
            f"Ascend device {self.device_id} transport check succeed.")
        return True


class AscendComputingCheck(_AscendCommandRunner):
    _EXECUTE_TIMES = 60
    _DATA_TYPES = ("fp16", "bf16", "fp32", "hf32", "int8")
    _TOLERANCE = 0.05

    def __init__(self, command, device_id=0, chip=None, logger=None):
        super().__init__(command)
        self.device_id = device_id
        self.chip = chip
        self.logger: Logger = logger or command.logger

    def _theoretical_value(self, dtype):
        if not self.chip:
            return None
        for prefix, specs in THEORETICAL_SPECS.items():
            if self.chip.startswith(prefix):
                return specs.get(dtype)
        return None

    def _result_key(self, dtype):
        prefix = "tops" if dtype == "int8" else "tflops"
        return f"{prefix}_{dtype}"

    def _run_computing_test(self, dtype):
        self.logger.info(
            f"Run Ascend computing check '{dtype}' on device "
            f"{self.device_id}.")
        cmd = (
            f"ascend-dmi -f -q -d {self.device_id} -t {dtype} "
            f"--et {self._EXECUTE_TIMES} --fmt json"
        )
        output, error, status = self.run_cmd(cmd, ignore_errors=True)
        if status != 0:
            self.logger.error(
                f"Ascend computing check '{dtype}' of device "
                f"{self.device_id} command failed:\n"
                f"{output.strip() or error.strip() or 'No output'}"
            )
            return False

        result = json.loads(output)

        computing_power = result.get("computing_power")
        if not isinstance(computing_power, dict):
            self.logger.error(
                f"Ascend computing check '{dtype}' of device "
                f"{self.device_id} returned no computing_power:\n"
                f"{output.strip() or 'No output'}"
            )
            return False

        key = self._result_key(dtype)
        value = computing_power.get(key)
        if value is None:
            self.logger.error(
                f"Ascend computing check '{dtype}' of device "
                f"{self.device_id} returned no '{key}' result:\n"
                f"{output.strip() or 'No output'}"
            )
            return False

        power = computing_power.get("power", "unknown")
        unit = "TOPS" if dtype == "int8" else "TFLOPS"
        theoretical = self._theoretical_value(dtype)
        if theoretical is None:
            self.logger.warning(
                f"Ascend computing check '{dtype}' of device "
                f"{self.device_id}: {value:.2f} {unit}, power {power} "
                f"(no theoretical spec for chip "
                f"'{self.chip or 'unknown'}', skipping comparison)",
            )
            return True

        diff = abs(value - theoretical) / theoretical
        if diff > self._TOLERANCE:
            self.logger.error(
                f"Ascend computing check '{dtype}' of device "
                f"{self.device_id}: {value:.2f} {unit} deviates from "
                f"theoretical {theoretical:.0f} {unit} by {diff:.1%} "
                f"(exceeds {self._TOLERANCE:.0%} tolerance)"
            )
            return False

        self.logger.info(
            f"Ascend computing check '{dtype}' of device "
            f"{self.device_id}: {value:.2f} {unit} (theoretical "
            f"{theoretical:.0f}, diff {diff:.1%}), power {power}",
            terminal_print=False,
        )
        return True

    def computing_check(self):
        self.logger.info(
            f"Check Ascend device {self.device_id} computing power.")
        if not all(
            self._run_computing_test(dtype) for dtype in self._DATA_TYPES
        ):
            return False

        self.logger.info(
            f"Ascend device {self.device_id} computing check succeed.")
        return True


class AscendCompileTest(_AscendCommandRunner):
    _SOURCE = "vector_add.asc"
    _OUTPUT_BIN = "vector_add"
    _SUCCESS_PATTERN = re.compile(
        r"\[Success\]\s*Case accuracy is verification passed"
    )
    _TMP_DIR_PREFIX = "ascend_compile_"

    def __init__(self, command, chip, logger=None):
        super().__init__(command)
        self.chip = chip
        self.logger: Logger = logger or command.logger

    def _prepare_workdir(self):
        import tempfile
        workdir = tempfile.mkdtemp(prefix=self._TMP_DIR_PREFIX, dir="/tmp")
        source = os.path.join(os.path.dirname(__file__), self._SOURCE)
        dest_source = os.path.join(workdir, self._SOURCE)
        cp_cmd = f"cp {shlex.quote(source)} {shlex.quote(dest_source)}"
        _, _, status = self.run_cmd(cp_cmd, ignore_errors=True)
        if status != 0:
            self.logger.error(
                "Ascend compile test: failed to copy source to "
                f"{workdir}")
            return None, None
        return workdir, dest_source

    def _cleanup(self, workdir):
        rm_cmd = f"rm -rf {shlex.quote(workdir)}"
        _, _, _ = self.run_cmd(rm_cmd, ignore_errors=True)

    def compile_test(self):
        self.logger.info("Run Ascend compile test.")
        arch = NPU_ARCH_MAP.get(self.chip)
        if arch is None:
            self.logger.error(
                "Ascend compile test: no npu-arch mapping for chip "
                f"'{self.chip}'")
            return False

        workdir, dest_source = self._prepare_workdir()
        if workdir is None or dest_source is None:
            return False

        dest_bin = os.path.join(workdir, self._OUTPUT_BIN)
        compile_cmd = (
            f"bisheng {shlex.quote(dest_source)} --npu-arch={arch} "
            f"-o {shlex.quote(dest_bin)}"
        )
        output, error, status = self.run_cmd(
            compile_cmd, ignore_errors=True)
        if status != 0:
            self.logger.error(
                "Ascend compile test: bisheng compilation failed:\n"
                f"{output.strip() or error.strip() or 'No output'}")
            self._cleanup(workdir)
            return False

        self.logger.info(
            f"Ascend compile test: bisheng compilation succeeded "
            f"(arch {arch})")

        output, error, status = self.run_cmd(
            f"cd {shlex.quote(workdir)} && ./{self._OUTPUT_BIN}",
            ignore_errors=True)
        if status != 0:
            self.logger.error(
                "Ascend compile test: running compiled binary failed:\n"
                f"{output.strip() or error.strip() or 'No output'}")
            self._cleanup(workdir)
            return False

        if not self._SUCCESS_PATTERN.search(output):
            self.logger.error(
                "Ascend compile test: verification marker not found:\n"
                f"{output.strip() or 'No output'}")
            self._cleanup(workdir)
            return False

        self.logger.info(
            "Ascend compile test: accuracy verification passed")
        self._cleanup(workdir)
        return True


class AscendTest(Test):
    # Unified Ascend NPU test: scheduled once with an empty device, enumerates
    # all davinci cards internally so N cards do not produce N runs.
    def __init__(self):
        Test.__init__(self)
        self.pri = 0
        self.requirements = []
        self.soc_name = None

    def setup(self, args=None):
        self.args = args or argparse.Namespace()
        logger = getattr(self.args, "test_logger", None)
        if logger is None:
            raise RuntimeError("test_logger is required for Ascend test")
        self.logger: Logger = logger
        self.command: Command = Command(logger)

    def collect_devices(self):
        # Enumerate Ascend NPU devices by PCI vendor:device ID.
        output, _, _ = self.command.run_cmd(
            "lspci -nnk", ignore_errors=True, log_print=False)
        bdf_pattern = re.compile(
            r"^([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F])\s")
        devices = []
        for line in output.splitlines():
            match = bdf_pattern.match(line)
            if match and any(pci_id in line.lower() for pci_id in ASCEND_PCI_IDS):
                devices.append(match.group(1))
        return devices

    def show_driver_info(self, devices):
        for pci in devices:
            self.logger.info(f"Ascend device {pci}:", terminal_print=False)
            self.command.run_cmd(
                f"lspci -vs {pci}", ignore_errors=True)

    def get_pcie_link_info(self, pci):
        # Query negotiated PCIe link speed/lanes via lspci LnkSta.
        output, _, status = self.command.run_cmd(
            f"lspci -vvs {pci}", ignore_errors=True, log_print=False)
        if status != 0:
            self.logger.error(
                f"Ascend device {pci}: lspci failed:\n"
                f"{output.strip() or 'No output'}")
            return None, None
        match = re.search(
            r"(?m)^\s*LnkSta:.*Speed\s+([\d.]+)\s*GT/s.*Width\s+x(\d+)",
            output)
        if not match:
            self.logger.error(
                f"Ascend device {pci}: no LnkSta parsed from lspci:\n"
                f"{output.strip() or 'No output'}")
            return None, None
        speed = float(match.group(1))
        lanes = int(match.group(2))
        self.logger.info(
            f"Ascend device {pci}: PCIe Speed {speed} GT/s x{lanes}.")
        return speed, lanes

    def check_cann(self):
        # Verify the CANN runtime is importable and reports a SoC name.
        self.logger.info("Check CANN environment.")
        cmd = (
            """bash -c 'source /usr/local/Ascend/cann/set_env.sh && """
            """python3 -c "import acl;print(acl.get_soc_name())"'"""
        )
        output, _, status = self.command.run_cmd(cmd, ignore_errors=True)
        soc_name = output.strip()
        if status != 0 or not soc_name:
            self.logger.error(
                f"CANN environment check failed, please check the environment: "
                f"{soc_name or 'No output'}")
            return False

        self.soc_name = soc_name
        self.logger.info(
            f"CANN environment check succeed, SoC name: {soc_name}.")
        return True

    def check_ascend_toolbox(self):
        # Verify the Ascend toolbox (ascend-dmi) is installed.
        self.logger.info("Check Ascend toolbox.")
        cmd = (
            "bash -c 'source /usr/local/Ascend/cann/set_env.sh && "
            "source /usr/local/Ascend/toolbox/set_env.sh && ascend-dmi -v'"
        )
        output, _, status = self.command.run_cmd(cmd, ignore_errors=True)
        version_info = output.strip()
        if status != 0:
            self.logger.error(
                "Ascend toolbox check failed, please check the installation: "
                f"{version_info or 'No output'}")
            return False

        self.logger.info(f"Ascend toolbox check succeed: {version_info}.")
        return True

    def test(self):
        self.logger.info("Start Ascend NPU test.")
        devices = self.collect_devices()
        if not devices:
            self.logger.error("No Ascend NPU device found.")
            return False
        self.logger.info(
            f"Found {len(devices)} Ascend NPU device(s): "
            f"{', '.join(devices)}.")
        self.show_driver_info(devices)

        version = AscendVersion(self.command, logger=self.logger)

        results = [
            self.check_cann(),
            self.check_ascend_toolbox(),
            version.version_check(),
        ]
        for index in range(len(devices)):
            health = AscendHealthCheck(
                self.command, index, logger=self.logger)
            results.append(health.health_check())
            speed, lanes = self.get_pcie_link_info(devices[index])
            transport = AscendTransportCheck(
                self.command, index, pcie_speed=speed, pcie_lanes=lanes,
                logger=self.logger)
            results.append(transport.transport_check())
            computing = AscendComputingCheck(
                self.command, index, chip=getattr(self, "soc_name", None),
                logger=self.logger)
            results.append(computing.computing_check())
        compile_test = AscendCompileTest(
            self.command, chip=getattr(self, "soc_name", None),
            logger=self.logger)
        results.append(compile_test.compile_test())
        if not all(results):
            return False

        self.logger.info("Ascend NPU test completed successfully.")
        return True
