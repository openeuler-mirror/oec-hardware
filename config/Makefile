# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2022-06-08

.PHONY: install clean

HWCERT_CLASS_LIB := /usr/share/oech/lib

all: ;

install:
	mkdir -p $(DESTDIR)$(HWCERT_CLASS_LIB)/config
	cp version.config $(DESTDIR)$(HWCERT_CLASS_LIB)/config/
	cp pci.ids $(DESTDIR)$(HWCERT_CLASS_LIB)/config/
	cp test_config.yaml $(DESTDIR)$(HWCERT_CLASS_LIB)/config/

clean:
	rm -rf $(DESTDIR)$(HWCERT_CLASS_LIB)/config

