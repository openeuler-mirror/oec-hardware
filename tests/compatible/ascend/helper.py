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

# Per-lane raw transfer rate (GT/s) and encoding efficiency per generation.
# PCIe 1.x/2.x use 8b/10b; PCIe 3.x-5.x use 128b/130b; PCIe 6.x+ use FLIT mode.
_PCIE_GEN_SPECS = {
    1: (2.5, 8 / 10),
    2: (5.0, 8 / 10),
    3: (8.0, 128 / 130),
    4: (16.0, 128 / 130),
    5: (32.0, 128 / 130),
    6: (64.0, 128 / 130),
    7: (128.0, 128 / 130),
}

# Transfer rate (GT/s) -> encoding efficiency.
_SPEED_TO_ENCODING = {rate: encoding for rate, encoding in _PCIE_GEN_SPECS.values()}


def pcie_theoretical_bandwidth(speed_gts, lanes):
    """Return unidirectional PCIe theoretical bandwidth in GB/s.

    Formula: transfer_rate(GT/s) × encoding_efficiency × lanes / 8.
    8 bits per byte converts GT/s to GB/s.
    """
    encoding = _SPEED_TO_ENCODING.get(float(speed_gts))
    if encoding is None:
        raise ValueError(f"Unsupported PCIe speed: {speed_gts} GT/s")
    if not isinstance(lanes, int) or lanes <= 0:
        raise ValueError(f"Invalid lane count: {lanes}")
    return float(speed_gts) * encoding * lanes / 8
