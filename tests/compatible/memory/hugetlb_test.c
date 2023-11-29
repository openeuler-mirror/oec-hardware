/*
 * Copyright (c) 2020 Huawei Technologies Co., Ltd.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of version 2 of the GNU General Public
 * License as published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
 * 02110-1301, USA
 */

#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>

#define LENGTH (1024UL*1024*1024)
#define RANGE 128
#define FLAGS (MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB)

static void write_test(char *addr)
{
	unsigned long i;
	printf("Writing...\n");
	for (i = 0; i < LENGTH; i++)
		*(addr + i) = i % RANGE;
}

static int read_test(char *addr)
{
	unsigned long i;
	printf("Reading...\n");
	for (i = 0; i < LENGTH; i++) {
		if (*(addr + i) != (i % RANGE)) {
			printf("Mismatch at %lu\n", i);
			return 1;
		}
	}
	return 0;
}

int main(int argc, char **argv)
{
	void *addr;
	int ret;
	size_t length = LENGTH;

	printf("Mapping %lu Mbytes\n", (unsigned long)length >> 20);
	addr = mmap(NULL, length, PROT_READ | PROT_WRITE, FLAGS, -1, 0);
	if (addr == MAP_FAILED) {
		perror("mmap");
		exit(1);
	}

	write_test(addr);
	ret = read_test(addr);

	printf("Unmapping %lu Mbytes\n", (unsigned long)length >> 20);
	if (munmap(addr, LENGTH)) {
		perror("munmap");
		exit(1);
	}

	return ret;
}
