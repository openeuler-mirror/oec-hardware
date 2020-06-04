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


.PHONY: all clean install

HWCERT_TEST_LIB := $(DESTDIR)/usr/share/oech/lib/tests/
SUBDIRS := $(shell ls | grep -v Makefile)

all:
	for i in $(SUBDIRS); do $(MAKE) -C $$i; done

clean:
	for i in $(SUBDIRS); do $(MAKE) -C $$i DEST=$(HWCERT_TEST_LIB)/$$i clean; done
	rm -rf $(HWCERT_TEST_LIB)

install:
	mkdir -p $(HWCERT_TEST_LIB)
	for i in $(SUBDIRS); do $(MAKE) -C $$i DEST=$(HWCERT_TEST_LIB)/$$i install; done
