#!/usr/bin/env python
# coding: utf-8

# Copyright (c) 2020 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01

"""call test_case"""

import decimal
import time


def cal():
    """call test_case"""
    decimal.getcontext().prec = 1000
    one = decimal.Decimal(1)
    for i in range(1000):
        # j = (i * one).sqrt()
        (i * one).sqrt()


if __name__ == '__main__':
    time_start = time.time()
    while 1:
        cal()
        time_delta = time.time() - time_start
        if time_delta >= 2:
            print(time_delta)
            break
