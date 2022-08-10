# Copyright (c) 2020-2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01

.PHONY: install clean

all: ;

install:
	mkdir -p $(DESTDIR)/usr/bin
	cp oech $(DESTDIR)/usr/bin
	chmod u+x $(DESTDIR)/usr/bin/oech
	cp oech-server $(DESTDIR)/usr/bin
	chmod u+x $(DESTDIR)/usr/bin/oech-server
	mkdir -p $(DESTDIR)/usr/share/oech/lib
	cp kernelrelease.json $(DESTDIR)/usr/share/oech/
	cp oech_logrotate.sh $(DESTDIR)/usr/share/oech/lib/
	mkdir -p $(DESTDIR)/usr/lib/systemd/system/
	cp *.service $(DESTDIR)/usr/lib/systemd/system/

clean:
	rm -rf $(DESTDIR)/usr/bin/oech

