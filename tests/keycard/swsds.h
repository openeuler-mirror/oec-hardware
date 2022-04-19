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

#ifndef _SW_SDS_H_
#define _SW_SDS_H_ 1

#ifdef __cplusplus
extern "C"
{
#endif

	/*数据类型定义*/
	typedef char SGD_CHAR;
	typedef char SGD_INT8;
	typedef short SGD_INT16;
	typedef int SGD_INT32;
	typedef long long SGD_INT64;
	typedef unsigned char SGD_UCHAR;
	typedef unsigned char SGD_UINT8;
	typedef unsigned short SGD_UINT16;
	typedef unsigned int SGD_UINT32;
	typedef unsigned long long SGD_UINT64;
	typedef unsigned int SGD_RV;
	typedef void *SGD_OBJ;
	typedef int SGD_BOOL;
	typedef void *SGD_HANDLE;

	typedef struct DeviceInfo_st
	{
		unsigned char IssuerName[40];
		unsigned char DeviceName[16];
		unsigned char DeviceSerial[16];
		unsigned int DeviceVersion;
		unsigned int StandardVersion;
		unsigned int AsymAlgAbility[2];
		unsigned int SymAlgAbility;
		unsigned int HashAlgAbility;
		unsigned int BufferSize;
	} DEVICEINFO;

#define RSAref_MAX_BITS 2048
#define RSAref_MAX_LEN ((RSAref_MAX_BITS + 7) / 8)
#define RSAref_MAX_PBITS ((RSAref_MAX_BITS + 1) / 2)
#define RSAref_MAX_PLEN ((RSAref_MAX_PBITS + 7) / 8)

	typedef struct RSArefPublicKey_st
	{
		unsigned int bits;
		unsigned char m[RSAref_MAX_LEN];
		unsigned char e[RSAref_MAX_LEN];
	} RSArefPublicKey;

	typedef struct RSArefPrivateKey_st
	{
		unsigned int bits;
		unsigned char m[RSAref_MAX_LEN];
		unsigned char e[RSAref_MAX_LEN];
		unsigned char d[RSAref_MAX_LEN];
		unsigned char prime[2][RSAref_MAX_PLEN];
		unsigned char pexp[2][RSAref_MAX_PLEN];
		unsigned char coef[RSAref_MAX_PLEN];
	} RSArefPrivateKey;

/*ECC密钥*/
#define ECCref_MAX_BITS 256
#define ECCref_MAX_LEN ((ECCref_MAX_BITS + 7) / 8)
#define ECCref_MAX_CIPHER_LEN 136

	typedef struct ECCrefPublicKey_st
	{
		unsigned int bits;
		unsigned char x[ECCref_MAX_LEN];
		unsigned char y[ECCref_MAX_LEN];
	} ECCrefPublicKey;

	typedef struct ECCrefPrivateKey_st
	{
		unsigned int bits;
		unsigned char D[ECCref_MAX_LEN];
	} ECCrefPrivateKey;

	typedef struct ECCCipher_st
	{
		unsigned int clength;
		unsigned char x[ECCref_MAX_LEN];
		unsigned char y[ECCref_MAX_LEN];
		unsigned char C[ECCref_MAX_CIPHER_LEN];
		unsigned char M[ECCref_MAX_LEN];
	} ECCCipher;

	typedef struct ECCSignature_st
	{
		unsigned char r[ECCref_MAX_LEN];
		unsigned char s[ECCref_MAX_LEN];
	} ECCSignature;

/*算法标识*/
#define SGD_SM1_ECB 0x00000101
#define SGD_SM1_CBC 0x00000102
#define SGD_SM1_MAC 0x00000110

#define SGD_SSF33_ECB 0x00000201
#define SGD_SSF33_CBC 0x00000202
#define SGD_SSF33_MAC 0x00000210

#define SGD_AES_ECB 0x00000401
#define SGD_3DES_ECB 0x00000801

#define SGD_SM4_ECB 0x00002001
#define SGD_SM4_CBC 0x00002002
#define SGD_SM4_MAC 0x00002010
#define SGD_SM4_XTS 0x00002040

#define SGD_DES_ECB 0x00004001

#define SGD_SM7_ECB 0x00008001

#define SGD_RSA_SIGN 0x00010100
#define SGD_SM2_1 0x00020100
#define SGD_SM2_2 0x00020200
#define SGD_SM2_3 0x00020400

#define SGD_SM3 0x00000001
#define SGD_SHA1 0x00000002
#define SGD_SHA256 0x00000004
#define SGD_SHA512 0x00000008
#define SGD_SHA384 0x00000010
#define SGD_SHA224 0x00000020
#define SGD_MD5 0x00000080

#define SGD_SYMM_ALG_MASK 0xFFFFFF00
#define SGD_SYMM_ALG_MODE_MASK 0x000000FF

/*标准错误码定义*/
#define SDR_OK 0x0 /*成功*/
#define SDR_BASE 0x01000000

	/*设备管理类函数*/
	SGD_RV SDF_OpenDevice(SGD_HANDLE *phDeviceHandle);
	SGD_RV SDF_CloseDevice(SGD_HANDLE hDeviceHandle);
	SGD_RV SDF_OpenSession(SGD_HANDLE hDeviceHandle, SGD_HANDLE *phSessionHandle);
	SGD_RV SDF_CloseSession(SGD_HANDLE hSessionHandle);
	SGD_RV SDF_GetDeviceInfo(SGD_HANDLE hSessionHandle, DEVICEINFO *pstDeviceInfo);
	SGD_RV SDF_GenerateRandom(SGD_HANDLE hSessionHandle, SGD_UINT32 uiLength, SGD_UCHAR *pucRandom);
	SGD_RV SDF_GetFirmwareVersion(SGD_HANDLE hSessionHandle, SGD_UCHAR *sFirmware, SGD_UINT32 *ulFirmwareLen);
	SGD_RV SDF_GetLibraryVersion(SGD_HANDLE hSessionHandle, SGD_UCHAR *sLibraryVersion, SGD_UINT32 *ulLibraryVersionLen);

	/*密钥管理类函数*/
	SGD_RV SDF_GenerateKeyPair_RSA(SGD_HANDLE hSessionHandle, SGD_UINT32 uiKeyBits, RSArefPublicKey *pucPublicKey, RSArefPrivateKey *pucPrivateKey);
	SGD_RV SDF_ImportKey(SGD_HANDLE hSessionHandle, SGD_UCHAR *pucKey, SGD_UINT32 uiKeyLength, SGD_HANDLE *phKeyHandle);
	SGD_RV SDF_DestroyKey(SGD_HANDLE hSessionHandle, SGD_HANDLE hKeyHandle);

	SGD_RV SDF_GenerateKeyPair_ECC(SGD_HANDLE hSessionHandle, SGD_UINT32 uiAlgID, SGD_UINT32 uiKeyBits, ECCrefPublicKey *pucPublicKey, ECCrefPrivateKey *pucPrivateKey);

	/*非对称密码运算函数*/
	SGD_RV SDF_ExternalPublicKeyOperation_RSA(SGD_HANDLE hSessionHandle, RSArefPublicKey *pucPublicKey, SGD_UCHAR *pucDataInput, SGD_UINT32 uiInputLength, SGD_UCHAR *pucDataOutput,
											  SGD_UINT32 *puiOutputLength);
	SGD_RV SDF_ExternalPrivateKeyOperation_RSA(SGD_HANDLE hSessionHandle, RSArefPrivateKey *pucPrivateKey, SGD_UCHAR *pucDataInput, SGD_UINT32 uiInputLength, SGD_UCHAR *pucDataOutput,
											   SGD_UINT32 *puiOutputLength);

	SGD_RV SDF_ExternalSign_ECC(SGD_HANDLE hSessionHandle, SGD_UINT32 uiAlgID, ECCrefPrivateKey *pucPrivateKey, SGD_UCHAR *pucData, SGD_UINT32 uiDataLength, ECCSignature *pucSignature);
	SGD_RV SDF_ExternalVerify_ECC(SGD_HANDLE hSessionHandle, SGD_UINT32 uiAlgID, ECCrefPublicKey *pucPublicKey, SGD_UCHAR *pucDataInput, SGD_UINT32 uiInputLength, ECCSignature *pucSignature);
	SGD_RV SDF_ExternalEncrypt_ECC(SGD_HANDLE hSessionHandle, SGD_UINT32 uiAlgID, ECCrefPublicKey *pucPublicKey, SGD_UCHAR *pucData, SGD_UINT32 uiDataLength, ECCCipher *pucEncData);
	SGD_RV SDF_ExternalDecrypt_ECC(SGD_HANDLE hSessionHandle, SGD_UINT32 uiAlgID, ECCrefPrivateKey *pucPrivateKey, ECCCipher *pucEncData, SGD_UCHAR *pucData, SGD_UINT32 *puiDataLength);

	/*对称密码运算函数*/
	SGD_RV SDF_Encrypt(SGD_HANDLE hSessionHandle, SGD_HANDLE hKeyHandle, SGD_UINT32 uiAlgID, SGD_UCHAR *pucIV, SGD_UCHAR *pucData, SGD_UINT32 uiDataLength, SGD_UCHAR *pucEncData,
					   SGD_UINT32 *puiEncDataLength);
	SGD_RV SDF_Decrypt(SGD_HANDLE hSessionHandle, SGD_HANDLE hKeyHandle, SGD_UINT32 uiAlgID, SGD_UCHAR *pucIV, SGD_UCHAR *pucEncData, SGD_UINT32 uiEncDataLength, SGD_UCHAR *pucData,
					   SGD_UINT32 *puiDataLength);
	SGD_RV SDF_CalculateMAC(SGD_HANDLE hSessionHandle, SGD_HANDLE hKeyHandle, SGD_UINT32 uiAlgID, SGD_UCHAR *pucIV, SGD_UCHAR *pucData, SGD_UINT32 uiDataLength, SGD_UCHAR *pucMAC,
							SGD_UINT32 *puiMACLength);

	SGD_RV SDF_Encrypt_Ex(SGD_HANDLE hSessionHandle, SGD_HANDLE hKeyHandle_1, SGD_HANDLE hKeyHandle_2, SGD_UINT32 uiAlgID, SGD_UCHAR *pucIV, SGD_UCHAR *pucData, SGD_UINT32 uiDataLength,
						  SGD_UCHAR *pucEncData, SGD_UINT32 *puiEncDataLength, SGD_UINT32 uiDataUnitLength);
	SGD_RV SDF_Decrypt_Ex(SGD_HANDLE hSessionHandle, SGD_HANDLE hKeyHandle_1, SGD_HANDLE hKeyHandle_2, SGD_UINT32 uiAlgID, SGD_UCHAR *pucIV, SGD_UCHAR *pucEncData, SGD_UINT32 uiEncDataLength,
						  SGD_UCHAR *pucData, SGD_UINT32 *puiDataLength, SGD_UINT32 uiDataUnitLength);

	/*杂凑运算函数*/
	SGD_RV SDF_HashInit(SGD_HANDLE hSessionHandle, SGD_UINT32 uiAlgID, ECCrefPublicKey *pucPublicKey, SGD_UCHAR *pucID, SGD_UINT32 uiIDLength);
	SGD_RV SDF_HashUpdate(SGD_HANDLE hSessionHandle, SGD_UCHAR *pucData, SGD_UINT32 uiDataLength);
	SGD_RV SDF_HashFinal(SGD_HANDLE hSessionHandle, SGD_UCHAR *pucHash, SGD_UINT32 *puiHashLength);
	SGD_RV SDF_HashInit_ECC(SGD_HANDLE hSessionHandle, SGD_UINT32 uiAlgID, SGD_UCHAR *pucParamID);

	/*用户文件操作函数*/
	SGD_RV SDF_CreateFile(SGD_HANDLE hSessionHandle, SGD_UCHAR *pucFileName, SGD_UINT32 uiNameLen, SGD_UINT32 uiFileSize);
	SGD_RV SDF_ReadFile(SGD_HANDLE hSessionHandle, SGD_UCHAR *pucFileName, SGD_UINT32 uiNameLen, SGD_UINT32 uiOffset, SGD_UINT32 *puiReadLength, SGD_UCHAR *pucBuffer);
	SGD_RV SDF_WriteFile(SGD_HANDLE hSessionHandle, SGD_UCHAR *pucFileName, SGD_UINT32 uiNameLen, SGD_UINT32 uiOffset, SGD_UINT32 uiWriteLength, SGD_UCHAR *pucBuffer);
	SGD_RV SDF_DeleteFile(SGD_HANDLE hSessionHandle, SGD_UCHAR *pucFileName, SGD_UINT32 uiNameLen);

#ifdef __cplusplus
}
#endif

#endif /*#ifndef _SW_SDS_H_*/