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

.PHONY: all install clean

all: clock

CFLAGS+=-Wall
CFLAGS+=-DCPU_ALLOC
# sched_setaffinity has no size_t argument on older systems.
ifeq ($(shell grep 'sched_setaffinity.*size_t' /usr/include/sched.h),)
CFLAGS+=-DOLD_SCHED_SETAFFINITY
endif

clock: clock.c
	$(CC) $(CFLAGS) -lrt $< -o $@

install:
	mkdir -p $(DEST)
	cp -a clock *.py $(DEST)
	chmod a+x $(DEST)/*.py

clean:
	rm -rf $(DEST)
	rm -rf clock

