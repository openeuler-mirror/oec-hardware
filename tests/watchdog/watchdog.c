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

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <getopt.h>
#include <sys/ioctl.h>
#include <linux/watchdog.h>

#define DEFAULT_INTERVAL 1
#define MAX_INTERVAL 360

int fd;
const char stop = 'V';
static const char opts[] = "ths:g";

static void term(int sig)
{
	int ret = write(fd, &stop, 1);

	close(fd);
	if (ret < 0)
		printf("\nStopping watchdog failed (%d)...\n", errno);
	else
		printf("\nStopping watchdog ...\n");
	exit(0);
}

static void usage(char *progname)
{
	printf("Usage: %s [options]\n", progname);
	printf(" -t     Trigger watchdog\n");
	printf(" -h     Print the help message\n");
	printf(" -s T   Set watchdog timeout to T seconds\n");
	printf(" -g     Get watchdog timeout\n");
}

int main(int argc, char *argv[])
{
	int flags;
	int ret;
	int c;
	int count;

	setbuf(stdout, NULL);

	fd = open("/dev/watchdog", O_WRONLY);
	if (fd < 0) {
		printf("Watchdog device open failed %s\n", strerror(errno));
		exit(-1);
	}

	while ((c = getopt(argc, argv, opts)) != -1) {
		switch (c) {
			case 't':
				goto trigger;
			case 's':
				flags = strtoul(optarg, NULL, 0);
				ret = ioctl(fd, WDIOC_SETTIMEOUT, &flags);
				if (!ret)
					printf("Watchdog timeout set to %d seconds.\n", flags);
				else
					printf("Set watchdog timeout error '%s'\n", strerror(errno));
				goto end;
			case 'g':
				ret = ioctl(fd, WDIOC_GETTIMEOUT, &flags);
				if (!ret)
					printf("Watchdog timeout is %d seconds.\n", flags);
				else
					printf("Get watchdog timeout error '%s'\n", strerror(errno));
				goto end;
			default:
				break;
		}
	}
	usage(argv[0]);
	goto end;

trigger:
	printf("Start to trigger Watchdog!\n");
	signal(SIGINT, term);

	count = 0;
	while (count++ < MAX_INTERVAL) {
		printf(".");
		sleep(DEFAULT_INTERVAL);
	}
	printf("Fail to trigger Watchdog!\n");

end:
	ret = write(fd, &stop, 1);
	if (ret < 0)
		printf("Stopping watchdog ticks failed (%d)...\n", errno);
	close(fd);
	return 0;
}
