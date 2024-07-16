# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2024 Intel Corporation
# @Author   yi.sun@intel.com

.PHONY: install clean

all: ;

install:
	mkdir -p $(DEST)
	cp -a *.py *.sh $(DEST)
	chmod a+x $(DEST)/*.py $(DEST)/*.sh

clean:
	rm -rf $(DEST)
