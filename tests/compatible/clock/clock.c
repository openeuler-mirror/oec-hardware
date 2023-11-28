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

#define _GNU_SOURCE 1

#include <linux/rtc.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <sys/time.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <errno.h>

int test_clock_direction()
{
	time_t starttime = 0;
	time_t stoptime = 0;
	int sleeptime = 60;
	int delta = 0;

	printf("clock direction test start\n");
	time(&starttime);
	sleep(sleeptime);
	time(&stoptime);

	delta = (int)stoptime - (int)starttime - sleeptime;
	if (delta != 0) {
		printf("clock direction test fail\n");
		return 1;
	} else {
		printf("clock direction test complete\n");
		return 0;
	}
}

int test_rtc_clock()
{
	int rtc, delta;
	struct tm rtc_tm1, rtc_tm2;
	int sleeptime = 120;

	printf("rtc_clock test start\n");
	if ((rtc = open("/dev/rtc", O_WRONLY)) < 0) {
		perror("could not open RTC device");
		return 1;
	}

	if (ioctl(rtc, RTC_RD_TIME, &rtc_tm1) < 0) {
		perror("could not get the RTC time");
		close(rtc);
		return 1;
	}
	sleep(sleeptime);
	if (ioctl(rtc, RTC_RD_TIME, &rtc_tm2) < 0) {
		perror("could not get the RTC time");
		close(rtc);
		return 1;
	}

	close(rtc);
	delta = (int)mktime(&rtc_tm2) - (int)mktime(&rtc_tm1) - sleeptime;
	if (delta != 0) {
		printf("rtc_clock test fail\n");
		return 1;
	} else {
		printf("rtc_clock test complete\n");
		return 0;
	}
}

int main()
{
	int ret = 0;
	ret += test_clock_direction();
	ret += test_rtc_clock();
	return ret;
}
