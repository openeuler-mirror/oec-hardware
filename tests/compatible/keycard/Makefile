# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @meitingli
# Create: 2022-04-11

CC=gcc
CFLAGS=-Wall -D_LOG_TRACE_ -fPIC -I.
LIBS = -L . -lswsds -lpthread
OBJS=./TestSDS.o FunctionTest.o Util.o
APPS=TestSDS
ARCH := $(shell uname -m)
SO=libswsds_$(ARCH).so

all: $(APPS)

install:
	mkdir -p $(DEST)
	cp $(SO) $(DEST)/libswsds.so
	$(CC) -O2 -fPIC -Wl,--hash-style=sysv -o $(APPS) $(OBJS) $(LIBS) 
	cp -a *.py $(DEST)
	cp $(APPS) $(DEST)
	chmod a+x $(DEST)/*.py

%.o:%.c
	$(CC) -O2 -c $(CFLAGS)  $< -o $@

$(APPS):$(OBJS)
	cp $(SO) libswsds.so
	$(CC) -O2 -fPIC -Wl,--hash-style=sysv -o $(APPS) $(OBJS) $(LIBS) 
	
clean:
	rm  -f *.o $(APPS) libswsds.so

cleanall:
	rm  -f *.o $(APPS) libswsds.so
