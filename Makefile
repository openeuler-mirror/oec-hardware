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

NAME := oec-hardware
VERSION_PY := hwcert/version.py

.PHONY: all clean install

SUBDIRS := hwcert tests server scripts

all: $(VERSION_PY)
	for i in $(SUBDIRS); do $(MAKE) -C $$i DESTDIR=$(DESTDIR); done

$(VERSION_PY):
	@echo "# $(VERSION_PY) is automatically-generated" > $(VERSION_PY)
	@echo "version = '$(VERSION_RELEASE)'" >> $(VERSION_PY)
	@echo "name = '$(NAME)'" >> $(VERSION_PY)

install:
	mkdir -p $(DESTDIR)/usr/share/oech
	mkdir -p $(DESTDIR)/var/oech
	for i in $(SUBDIRS); do $(MAKE) -C $$i DESTDIR=$(DESTDIR) install; done

clean:
	for i in $(SUBDIRS); do $(MAKE) -C $$i DESTDIR=$(DESTDIR) clean; done
	rm -f $(VERSION_PY)
