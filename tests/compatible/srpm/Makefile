# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.gica's
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: yangyulong
# Create: 2024-04-22

.PHONY: install clean

all: ;

install:
	mkdir -p $(DEST)
	cp -a *.py $(DEST)
	cp -a config $(DEST)
	chmod a+x $(DEST)/*.py

clean:
	rm -rf $(DEST)
