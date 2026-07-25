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

from ._bandwidth import MetaXBandwidthTest
from ._check import MetaXCheck
from ._common import (
    C500_BIOS_PATH,
    METAX_DRIVER_NAME,
    MXVS_PATH,
    MetaXCommon,
)
from ._mccl import MetaXMCCLTest
from ._system_prepare import MetaXSystemPrepare
from ._warm_reset import MetaXWarmResetTest

__all__ = [
    "C500_BIOS_PATH",
    "METAX_DRIVER_NAME",
    "MXVS_PATH",
    "MetaXBandwidthTest",
    "MetaXCheck",
    "MetaXCommon",
    "MetaXMCCLTest",
    "MetaXSystemPrepare",
    "MetaXWarmResetTest",
]
