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

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <ctype.h>

#ifdef WIN32
#include <process.h>
#include <windows.h>
#include <io.h>
#include <conio.h>
#else
#include <pthread.h>
#include <unistd.h>
#include <sys/time.h>
#include <termios.h>
#endif

#include "swsds.h"

#ifdef WIN32
#define PUTCH(ch) _putch(ch)
#define GETCH() _getch()
#define GETANYKEY() _getch()
#define SLEEP(msec) Sleep(msec)
#define THREAD_EXIT() _endthread()
#define GETCURRENTTHREADID GetCurrentThreadId
#else
#define PUTCH(ch) putchar(ch)
#define GETCH() getch_unix()
#define GETANYKEY() getch_unix()
#define SLEEP(msec) usleep(msec * 1000)
#define THREAD_EXIT() pthread_exit(NULL)
#define GETCURRENTTHREADID (int)pthread_self
#endif

#define OPT_EXIT -1
#define OPT_RETURN -2
#define OPT_PREVIOUS -3
#define OPT_NEXT -4
#define OPT_YES -5
#define OPT_CANCEL -6

#define TESTSDS_VERSION "v3.3"   //版本控制信息
#define _NOT_TEST_KEK_ 1         //压力测试时不测试KEK功能
#define _NOT_USE_RANDOME_TEST_ 1 //性能测试时使用随机数据测试
#define MAX_SYMM_DATA_LENGTH 131072

extern SGD_HANDLE hDeviceHandle;
extern unsigned int g_nTestRepeat;

//功能测试函数声明
int BasicFuncTest(int nDefaultSelect);
int CreateFileTest(SGD_HANDLE hSessionHandle);
int ECCStdDataVerifyTest(SGD_HANDLE hSessionHandle);
int ECCStdDataDecTest(SGD_HANDLE hSessionHandle);
int ECCFuncTest(int nDefaultSelect);
int ExtECCOptTest(SGD_HANDLE hSessionHandle);
int ExtECCSignTest(SGD_HANDLE hSessionHandle);
int ExtRSAOptTest(SGD_HANDLE hSessionHandle);
int FileFuncTest(int nDefaultSelect);
int FunctionTest(int nSel, int nDefaultSelect);
int GenECCKeyPairTest(SGD_HANDLE hSessionHandle);
int GenRandomTest(SGD_HANDLE hSessionHandle);
int GenRSAKeyPairTest(SGD_HANDLE hSessionHandle);
int GetDeviceInfoTest(SGD_HANDLE hSessionHandle);
int HashFuncTest(int nDefaultSelect);
int HashTest(SGD_HANDLE hSessionHandle);
int HashCorrectnessTest(SGD_HANDLE hSessionHandle);
int RSAFuncTest(int nDefaultSelect);
int SymmCorrectnessTest(SGD_HANDLE hSessionHandle);
int SymmCalculateMACTest(SGD_HANDLE hSessionHandle);
int SymmFuncTest(int nDefaultSelect);

//辅助函数声明
#ifndef WIN32
int getch_unix(void);
#endif

void GetAnyKey();
int PrintData(char *itemName, unsigned char *sourceData, unsigned int dataLength, unsigned int rowCount);
unsigned int FileWrite(char *filename, char *mode, unsigned char *buffer, size_t size);