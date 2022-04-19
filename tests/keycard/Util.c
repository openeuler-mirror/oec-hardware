/**
* Copyright (c) 2022 Huawei Technologies Co., Ltd.
* oec-hardware is licensed under the Mulan PSL v2.
* You can use this software according to the terms and conditions of the Mulan PSL v2.
* You may obtain a copy of Mulan PSL v2 at:
*     http://license.coscl.org.cn/MulanPSL2
* THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
* PURPOSE.
* See the Mulan PSL v2 for more details.
* Author: @sansec/@meitingli
* Create: 2022-04-11
**/
#include "TestSDS.h"

int PrintData(char *itemName, unsigned char *sourceData, unsigned int dataLength, unsigned int rowCount)
{
	int i, j;

	if ((sourceData == NULL) || (rowCount == 0) || (dataLength == 0))
		return -1;

	if (itemName != NULL)
		printf("%s[%d]:\n", itemName, dataLength);

	for (i = 0; i < (int)(dataLength / rowCount); i++)
	{
		printf("%08x  ", i * rowCount);

		for (j = 0; j < (int)rowCount; j++)
		{
			printf("%02x ", *(sourceData + i * rowCount + j));
		}

		printf("\n");
	}

	if (!(dataLength % rowCount))
		return 0;

	printf("%08x  ", (dataLength / rowCount) * rowCount);

	for (j = 0; j < (int)(dataLength % rowCount); j++)
	{
		printf("%02x ", *(sourceData + (dataLength / rowCount) * rowCount + j));
	}

	printf("\n");

	return 0;
}

unsigned int FileWrite(char *filename, char *mode, unsigned char *buffer, size_t size)
{
	FILE *fp;
	unsigned int rw, rwed;

	if ((fp = fopen(filename, mode)) == NULL)
	{
		return 0;
	}

	rwed = 0;

	while (size > rwed)
	{
		if ((rw = (unsigned int)fwrite(buffer + rwed, 1, size - rwed, fp)) <= 0)
		{
			break;
		}

		rwed += rw;
	}

	fclose(fp);

	return rwed;
}

#ifndef WIN32
int getch_unix(void)
{
	struct termios oldt, newt;
	int ch;

	tcgetattr(0, &oldt);

	newt = oldt;

	newt.c_lflag &= ~(ICANON | ECHO);

	tcsetattr(0, TCSANOW, &newt);

	ch = getchar();

	tcsetattr(0, TCSANOW, &oldt);

	return ch;
}
#endif

void GetAnyKey()
{
	int ch;

	ch = GETCH();

	return;
}
