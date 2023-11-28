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

SGD_HANDLE hDeviceHandle;
unsigned int g_nTestRepeat;

int main(int argc, char *argv[])
{
	int rv;
	int nSel;

	//Connect to device
	rv = SDF_OpenDevice(&hDeviceHandle);
	if (rv != SDR_OK)
	{
		printf("Open device failed, the error code is [0x%08x]\n", rv);
		return 1;
	}
	scanf("%d", &nSel);
	rv = FunctionTest(nSel, 1);
	SDF_CloseDevice(hDeviceHandle);

	return rv;
}