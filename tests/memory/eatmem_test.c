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
#include <sys/time.h>
#include <fcntl.h>
#include <string.h>
#define __USE_GNU
#include <pthread.h>
#include <sched.h>

#define MEM_CHECK_MAGIC (0xFEE1DEAD)
unsigned long num_cpus = 1;
unsigned long num_threads = 2;
unsigned long memsize = 1024 * 1024 * 1024;
unsigned long thread_mem = 0;
unsigned done = 0;
unsigned mmap_done = 0;
unsigned init_thread = 0;
unsigned long test_time = 1200;
pthread_mutex_t thread_mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t run_mutex = PTHREAD_MUTEX_INITIALIZER;
char **mmap_zone = NULL;

void usage(void)
{
	printf("Usage: eatmem_test [-h] [-m size] [-t time]\n");
	printf("  -h: show this help\n");
	printf("  -m: memory size,unit MB. default: 1024MB\n");
	printf("  -t: test time,in seconds. default: 1200\n");
}


void *mem_eat(void *data)
{
	unsigned long pages, page_size, i;
	unsigned long *page_area;
	unsigned thread, page, offset;
	char *my_zone;
	unsigned thread_id;
	pthread_mutex_lock(&thread_mutex);
	thread_id = init_thread++;
	pthread_mutex_unlock(&thread_mutex);

	page_size = getpagesize();
	pages = thread_mem / page_size;
	my_zone = mmap(NULL, thread_mem, PROT_READ|PROT_WRITE, MAP_ANONYMOUS|MAP_PRIVATE, -1, 0);
	if (my_zone == MAP_FAILED) {
		fprintf(stderr, "mmap fail in thread %u\n", thread_id);
		exit(1);
	}
	for (i = 0; i < pages; i++) {
		page_area = (unsigned long *)&(my_zone[i * page_size]);
		page_area[0] = MEM_CHECK_MAGIC + i + thread_id;
	}
	mmap_zone[thread_id] = my_zone;
	pthread_mutex_lock(&thread_mutex);
	mmap_done++;
	pthread_mutex_unlock(&thread_mutex);
	printf("thread %u finish eat memory\n", thread_id);

	pthread_mutex_lock(&run_mutex);
	pthread_mutex_unlock(&run_mutex);
	while (!done) {
		thread = rand() % num_threads;
		page = rand() % pages;
		page_area = (unsigned long *)&(mmap_zone[thread][page * page_size]);
		if (page_area[0] != MEM_CHECK_MAGIC + page + thread) {
			fprintf(stderr, "thread %u read fail\n", thread_id);
			exit(1);
		}
		offset = (rand() % ((page_size / sizeof(unsigned long)) - 1)) + 1;
		page_area[offset] = rand();
	}
}

int main(int argc, char **argv)
{
	unsigned i = 0;
	unsigned long count = 0;
	cpu_set_t cpuset;
	pthread_t *threads;
	int ch = 0;
	while ((ch = getopt(argc, argv, "hm:t:")) != -1) {
		switch (ch) {
			case 'h':
				usage();
				return 0;
			case 'm':
				memsize = strtoul(optarg, NULL, 0);;
				if (!memsize) {
					fprintf(stderr, "bad memory size\n");
					return 1;
				}
				memsize <<= 20;
				break;
			case 't':
				test_time = atoi(optarg);
				if (!test_time) {
					fprintf(stderr, "bad test time\n");
					return 1;
				}
				break;
		}
	}
	printf("Memory size: %luMB\tTest time: %lus\n", memsize >> 20, test_time);

	num_cpus = sysconf(_SC_NPROCESSORS_CONF);
	if (num_threads < num_cpus * 2)
		num_threads = num_cpus * 2;

	thread_mem = memsize / num_threads;
	if (thread_mem < getpagesize())
		thread_mem = getpagesize();
	threads = (pthread_t *)malloc(num_threads * sizeof(pthread_t));
	mmap_zone = (char **)malloc(num_threads * sizeof(char *));
	pthread_mutex_lock(&run_mutex);
	printf("Start memory eating\n");
	for (i = 0; i < num_threads; i++) {
		if (pthread_create(&threads[i], NULL, mem_eat, NULL) != 0) {
			fprintf(stderr, "thread %u create fail\n", i);
			exit(1);
		}
		CPU_ZERO(&cpuset);
		CPU_SET(i%num_cpus, &cpuset);
		if (pthread_setaffinity_np(threads[i], sizeof(cpu_set_t), &cpuset) != 0) {
			fprintf(stderr, "thread %u setaffinity fail\n", i);
			exit(1);
		}
	}

	i = 0;
	while (mmap_done < num_threads) {
		sleep(1);
		i++;
		if (i >= test_time) {
			fprintf(stderr, "thread mmap not finished after %lu seconds\n", test_time);
			exit(1);
		}
	}
	pthread_mutex_unlock(&run_mutex);

	printf("Start memory rw testing\n");
	while (count < test_time) {
		sleep(2);
		count = count + 2;
		printf(".");
		fflush(stdout);
	}

	done = 1;
	for (i = 0; i < num_threads; i++)
		pthread_join(threads[i], NULL);

	printf("\neatmem_test complete\n");
	free(threads);
	return 0;
}
