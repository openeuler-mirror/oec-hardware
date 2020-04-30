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

all: eatmem_test hugetlb_test

eatmem_test: eatmem_test.c
	$(CC) $(CFLAGS) -lpthread $< -o $@

hugetlb_test: hugetlb_test.c
	$(CC) $(CFLAGS) $< -o $@

install:
	mkdir -p $(DEST)
	cp -a eatmem_test hugetlb_test *.py $(DEST)
	chmod a+x $(DEST)/*.py

clean:
	rm -rf $(DEST)
	rm -rf eatmem_test hugetlb_test

