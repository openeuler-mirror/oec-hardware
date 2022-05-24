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

int FunctionTest(int nSel, int nDefaultSelect)
{
	int result;
	int recode = 0;

	if (nSel == 1)
	{
		printf("   1|基本函数测试\n");
		printf("    |    获取设备信息、随机数功能测试及分析。\n");
		printf("\n");
		result = BasicFuncTest(1);
		if (result == 1)
		{
			recode = 1;
		}
	}

	if (nSel == 2)
	{
		printf("   2|RSA非对称密码运算函数测试\n");
		printf("    |    RSA密钥对产生，内部和外部密钥运算，数字信封转换测试。\n");
		printf("\n");
		result = RSAFuncTest(1);
		if (result == 1)
		{
			recode = 1;
		}
	}

	if (nSel == 3)
	{
		printf("   3|ECC非对称密码运算函数测试\n");
		printf("    |    ECC密钥对产生，内部和外部密钥运算，密钥交换协议测试\n");
		printf("\n");
		result = ECCFuncTest(1);
		if (result == 1)
		{
			recode = 1;
		}
	}

	if (nSel == 4)
	{
		printf("   4|对称密码运算函数测试\n");
		printf("    |    对称密钥管理，对称算法加、解密，产生MAC值测试。\n");
		printf("\n");
		result = SymmFuncTest(1);
		if (result == 1)
		{
			recode = 1;
		}
	}

	if (nSel == 5)
	{
		printf("   5|杂凑运算函数测试\n");
		printf("    |    杂凑运算功能测试。\n");
		printf("\n");
		result = HashFuncTest(1);
		if (result == 1)
		{
			recode = 1;
		}
	}

	if (nSel == 6)
	{
		printf("   6|用户文件操作函数测试\n");
		printf("    |    创建、删除用户文件，用户文件读写功能测试。\n");
		printf("\n");
		result = FileFuncTest(1);
		if (result == 1)
		{
			recode = 1;
		}
	}

	return recode;
}

int BasicFuncTest(int nDefaultSelect)
{
	int rv;
	int nSel;
	int recode = 0;

	SGD_HANDLE hSessionHandle;

	if ((nDefaultSelect < 1) || (nDefaultSelect > 2))
		nSel = 1;
	else
		nSel = nDefaultSelect;

	//创建会话句柄
	rv = SDF_OpenSession(hDeviceHandle, &hSessionHandle);
	if (rv != SDR_OK)
	{
		printf("打开会话句柄错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	printf("   1|获取设备信息测试\n");
	printf("    |    获取设备出厂信息、维护信息、能力字段等信息，并打印。\n");
	printf("\n");
	nSel = GetDeviceInfoTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}
	printf("   2|随机数测试\n");
	printf("    |    产生随机数并对随机数质量进行分析。\n");
	printf("\n");
	nSel = GenRandomTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	printf("\n");
	SDF_CloseSession(hSessionHandle);
	return recode;
}

int GetDeviceInfoTest(SGD_HANDLE hSessionHandle)
{
	int rv;
	unsigned char sFirmwareVersion[32] = {0};
	unsigned int uiFirmwareVersionLen = 32;
	unsigned char sLibraryVersion[16] = {0};
	unsigned int uiLibraryVersionLen = 16;

	unsigned char CertiedModel[32] = { 0 };
	unsigned int  CertiedModelLen = 32;
	
	DEVICEINFO stDeviceInfo;
	//获取设备信息
	rv = SDF_GetDeviceInfo(hSessionHandle, &stDeviceInfo);
	if (rv != SDR_OK)
	{
		printf("获取设备信息错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("获取设备信息成功。\n");
	printf("\n");
	printf("    |     项目      |   返回值  \n");
	printf("   _|_______________|______________________________________________________\n");
	printf("   1|   生产厂商    | %s\n", stDeviceInfo.IssuerName);
	printf("   2|   设备型号    | %s\n", stDeviceInfo.DeviceName);
	printf("   3|  设备序列号   | %s\n", stDeviceInfo.DeviceSerial);
	printf("   4|   设备版本    | v%08x\n", stDeviceInfo.DeviceVersion);
	printf("   5| 支持标准版本  | v%d\n", stDeviceInfo.StandardVersion);
	printf("   6| 支持公钥算法  | %08x | %08x\n", stDeviceInfo.AsymAlgAbility[0], stDeviceInfo.AsymAlgAbility[1]);
	printf("   7| 支持对称算法  | %08x\n", stDeviceInfo.SymAlgAbility);
	printf("   8| 支持杂凑算法  | %08x\n", stDeviceInfo.HashAlgAbility);
	printf("   9| 用户存储空间  | %dKB\n", stDeviceInfo.BufferSize >> 10);
	printf("\n");

	//获取固件版本
	rv = SDF_GetFirmwareVersion(hSessionHandle, sFirmwareVersion, &uiFirmwareVersionLen);
	if (rv != SDR_OK)
	{
		printf("获取设备固件版本信息错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("设备固件版本：%s\n", sFirmwareVersion);

	//获取软件库版本
	rv = SDF_GetLibraryVersion(hSessionHandle, sLibraryVersion, &uiLibraryVersionLen);
	if (rv != SDR_OK)
	{
		printf("获取软件库版本错误， 错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("设备软件版本：%s\n", sLibraryVersion);

	//获取认证型号
	CertiedModelLen = sizeof(CertiedModel);
	rv = SDF_ReadFile(hSessionHandle, "CertiedModelFile", strlen("CertiedModelFile"), 0, &CertiedModelLen, CertiedModel);
	if (rv != SDR_OK)
	{
		printf("获取认证型号错误， 错误码[0x%08x]\n", rv);
	}
	else
	{
		printf("设备认证型号：%s\n", CertiedModel);
	}

	printf("\n");
	return 0;
}

int GenRandomTest(SGD_HANDLE hSessionHandle)
{
	unsigned int rv;
	int randLen = 16;
	unsigned char pbOutBuffer[16384];
	rv = SDF_GenerateRandom(hSessionHandle, randLen, pbOutBuffer);
	if (rv != SDR_OK)
	{
		printf("产生随机数错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	PrintData("随机数", pbOutBuffer, randLen, 16);
	printf("\n");
	return 0;
}

int RSAFuncTest(int nDefaultSelect)
{
	int nSel, rv;
	int recode = 0;
	SGD_HANDLE hSessionHandle;
	//创建会话句柄
	rv = SDF_OpenSession(hDeviceHandle, &hSessionHandle);
	if (rv != SDR_OK)
	{
		printf("打开会话句柄错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	printf("   1|产生RSA密钥对测试\n");
	printf("    |    产生可导出的RSA密钥对，并打印。\n");
	printf("\n");
	nSel = GenRSAKeyPairTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	printf("   2|外部RSA密钥运算测试\n");
	printf("    |    产生RSA密钥对进行运算。\n");
	printf("\n");
	nSel = ExtRSAOptTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	SDF_CloseSession(hSessionHandle);
	return recode;
}

int GenRSAKeyPairTest(SGD_HANDLE hSessionHandle)
{
	unsigned int rv;
	unsigned int pukLen, prkLen;
	RSArefPublicKey pubKey;
	RSArefPrivateKey priKey;

	printf("产生可导出的RSA公私钥对,密钥模长1024。\n");
	printf("\n");
	printf("产生可导出的RSA公私钥对,密钥模长2048。\n");
	printf("\n");

	rv = SDF_GenerateKeyPair_RSA(hSessionHandle, 1024, &pubKey, &priKey);
	if (rv != SDR_OK)
	{
		printf("产生RSA密钥对模长1024错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("产生RSA密钥对模长1024成功，并写入 data/prikey.0, data/pubkey.0\n");
	pukLen = sizeof(RSArefPublicKey);
	prkLen = sizeof(RSArefPrivateKey);
	PrintData("PUBLICKEY", (unsigned char *)&pubKey, pukLen, 16);
	PrintData("PRIVATEKEY", (unsigned char *)&priKey, prkLen, 16);
	FileWrite("data/prikey.0", "wb+", (unsigned char *)&priKey, prkLen);
	FileWrite("data/pubkey.0", "wb+", (unsigned char *)&pubKey, pukLen);
	printf("\n");

	rv = SDF_GenerateKeyPair_RSA(hSessionHandle, 2048, &pubKey, &priKey);
	if (rv != SDR_OK)
	{
		printf("产生RSA密钥对模长2048错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("产生RSA密钥对模长2048成功，并写入 data/prikey.0, data/pubkey.0\n");
	pukLen = sizeof(RSArefPublicKey);
	prkLen = sizeof(RSArefPrivateKey);
	PrintData("PUBLICKEY", (unsigned char *)&pubKey, pukLen, 16);
	PrintData("PRIVATEKEY", (unsigned char *)&priKey, prkLen, 16);
	FileWrite("data/prikey.0", "wb+", (unsigned char *)&priKey, prkLen);
	FileWrite("data/pubkey.0", "wb+", (unsigned char *)&pubKey, pukLen);
	printf("\n");
	return 0;
}

int ExtRSAOptTest(SGD_HANDLE hSessionHandle)
{
	unsigned int rv;
	RSArefPublicKey pubKey;
	RSArefPrivateKey priKey;
	unsigned char inData[512], outData[512], tmpData[512];
	unsigned int tmpLen;
	int recode = 0;

	printf("外部RSA密钥运算测试:\n");
	printf("--------------------\n");
	printf("\n");

	rv = SDF_GenerateKeyPair_RSA(hSessionHandle, 1024, &pubKey, &priKey);
	if (rv != SDR_OK)
	{
		printf("产生RSA密钥对模长1024错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	inData[0] = 0;
	rv = SDF_GenerateRandom(hSessionHandle, priKey.bits / 8 - 1, &inData[1]);
	if (rv != SDR_OK)
	{
		printf("产生随机加密数据错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("从产生随机加密数据成功。\n");
	PrintData("随机加密数据", inData, priKey.bits / 8, 16);

	rv = SDF_ExternalPrivateKeyOperation_RSA(hSessionHandle, &priKey, inData, priKey.bits / 8, tmpData, &tmpLen);
	if (rv != SDR_OK)
	{
		printf("私钥运算错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("私钥运算成功。\n");
	PrintData("私钥运算结果", tmpData, tmpLen, 16);

	rv = SDF_ExternalPublicKeyOperation_RSA(hSessionHandle, &pubKey, tmpData, tmpLen, outData, &tmpLen);
	if (rv != SDR_OK)
	{
		printf("公钥运算错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("公钥运算成功。\n");
	PrintData("公钥运算结果", outData, tmpLen, 16);

	if ((priKey.bits / 8 == tmpLen) && (memcmp(inData, outData, priKey.bits / 8) == 0))
	{
		printf("结果比较成功。\n");
	}
	else
	{
		printf("结果比较失败。\n");
		recode = 1;
	}
	return recode;
}

int ECCFuncTest(int nDefaultSelect)
{
	int rv;
	int nSel;
	SGD_HANDLE hSessionHandle;
	int recode = 0;
	//创建会话句柄
	rv = SDF_OpenSession(hDeviceHandle, &hSessionHandle);
	if (rv != SDR_OK)
	{
		printf("打开会话句柄错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	if ((nDefaultSelect < 1) || (nDefaultSelect > 10))
		nSel = 1;
	else
		nSel = nDefaultSelect;

	printf("    1|产生ECC密钥对测试\n");
	printf("     |    产生可导出的ECC密钥对，并打印。\n");
	printf("\n");
	nSel = GenECCKeyPairTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	printf("    2|外部ECC密钥加解密运算测试\n");
	printf("     |    使用“1 产生ECC密钥对测试”产生ECC密钥对进行加解密运算。\n");
	printf("\n");
	nSel = ExtECCOptTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	printf("    3|外部ECC密钥签名验证运算测试\n");
	printf("     |    使用“1 产生ECC密钥对测试”产生ECC密钥对进行签名验证运算。\n");
	printf("\n");
	nSel = ExtECCSignTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	printf("    4|ECC标准数据验证测试\n");
	printf("     |    使用ECC标准数据进行验证运算，并测试结果。\n");
	printf("\n");
	nSel = ECCStdDataVerifyTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	printf("   5|ECC标准数据解密测试\n");
	printf("     |    使用ECC标准数据解密运算，并测试结果。\n");
	printf("\n");
	nSel = ECCStdDataDecTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	SDF_CloseSession(hSessionHandle);
	return recode;
}

int GenECCKeyPairTest(SGD_HANDLE hSessionHandle)
{
	int rv;
	ECCrefPublicKey pubKey;
	ECCrefPrivateKey priKey;
	int pukLen, prkLen;

	int keyLen = 256;
	printf("产生ECC密钥对测试:\n");
	printf("------------------\n");
	printf("\n");

	rv = SDF_GenerateKeyPair_ECC(hSessionHandle, SGD_SM2_3, keyLen, &pubKey, &priKey);
	if (rv != SDR_OK)
	{
		printf("产生ECC密钥对错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	printf("产生ECC密钥对成功，并写入 data/prikey_ecc.0, data/pubkey_ecc.0\n");
	pukLen = sizeof(ECCrefPublicKey);
	prkLen = sizeof(ECCrefPrivateKey);
	PrintData("PUBLICKEY", (unsigned char *)&pubKey, pukLen, 16);
	PrintData("PRIVATEKEY", (unsigned char *)&priKey, prkLen, 16);
	FileWrite("data/prikey_ecc.0", "wb+", (unsigned char *)&priKey, prkLen);
	FileWrite("data/pubkey_ecc.0", "wb+", (unsigned char *)&pubKey, pukLen);

	return 0;
}

int ExtECCOptTest(SGD_HANDLE hSessionHandle)
{
	int rv;
	ECCrefPublicKey pubKey;
	ECCrefPrivateKey priKey;
	unsigned char inData[512], outData[512], tmpData[512];
	unsigned int outDataLen;
	unsigned int inPlainLen;
	int keyLen = 256;

	printf("外部ECC密钥加解密运算测试:\n");
	printf("--------------------\n");
	printf("\n");

	SDF_GenerateKeyPair_ECC(hSessionHandle, SGD_SM2_3, keyLen, &pubKey, &priKey);

	//通过生成随机数从而设定明文数据长度
	rv = SDF_GenerateRandom(hSessionHandle, 1, &inData[0]);
	if (rv != SDR_OK)
	{
		printf("产生随机数错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	inPlainLen = (inData[0] % ECCref_MAX_CIPHER_LEN) + 1;
	memset(inData, 0, sizeof(inData));
	rv = SDF_GenerateRandom(hSessionHandle, inPlainLen, &inData[0]);
	if (rv != SDR_OK)
	{
		printf("产生随机加密数据错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("产生随机加密数据成功。\n");
	PrintData("随机加密数据", inData, inPlainLen, 16);
	memset(tmpData, 0, sizeof(tmpData));
	rv = SDF_ExternalEncrypt_ECC(hSessionHandle, SGD_SM2_3, &pubKey, inData, inPlainLen, (ECCCipher *)tmpData);
	if (rv != SDR_OK)
	{
		printf("公钥钥运算错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("公钥运算成功。\n");
	memset(outData, 0, sizeof(outData));
	outDataLen = sizeof(outData);

	rv = SDF_ExternalDecrypt_ECC(hSessionHandle, SGD_SM2_3, &priKey, (ECCCipher *)tmpData, outData, &outDataLen);
	if (rv != SDR_OK)
	{
		printf("私钥运算错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("私钥运算成功。\n");
	PrintData("私钥运算结果", outData, outDataLen, 16);

	if ((inPlainLen != outDataLen) || (memcmp(inData, outData, outDataLen) != 0))
	{
		printf("结果比较失败。\n");
		return 1;
	}
	printf("结果比较成功。\n");
	return 0;
}

int ExtECCSignTest(SGD_HANDLE hSessionHandle)
{
	int rv;
	ECCrefPublicKey pubKey;
	ECCrefPrivateKey priKey;
	unsigned char inData[512], tmpData[512];
	int keyLen = 256;

	printf("外部ECC密钥签名验证运算测试:\n");
	printf("--------------------\n");
	printf("\n");
	SDF_GenerateKeyPair_ECC(hSessionHandle, SGD_SM2_3, keyLen, &pubKey, &priKey);
	memset(inData, 0, sizeof(inData));
	rv = SDF_GenerateRandom(hSessionHandle, priKey.bits / 8 - 1, &inData[1]);
	if (rv != SDR_OK)
	{
		printf("产生随机签名数据错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("产生随机签名数据成功。\n");
	PrintData("随机签名数据", inData, priKey.bits / 8, 16);

	memset(tmpData, 0, sizeof(tmpData));
	rv = SDF_ExternalSign_ECC(hSessionHandle, SGD_SM2_1, &priKey, inData, priKey.bits / 8, (ECCSignature *)tmpData);
	if (rv != SDR_OK)
	{
		printf("签名运算错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("签名运算成功。\n");
	PrintData("私钥签名运算结果", tmpData, sizeof(ECCSignature), 16);

	rv = SDF_ExternalVerify_ECC(hSessionHandle, SGD_SM2_1, &pubKey, inData, priKey.bits / 8, (ECCSignature *)tmpData);
	if (rv != SDR_OK)
	{
		printf("验证签名运算错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("验证签名运算成功。\n");
	return 0;
}

//ECC标准数据验证测试
int ECCStdDataVerifyTest(SGD_HANDLE hSessionHandle)
{
	unsigned int rv;

	unsigned char xa[32] = {0x5C, 0xA4, 0xE4, 0x40, 0xC5, 0x08, 0xC4, 0x5F, 0xE7, 0xD7, 0x58, 0xAB, 0x10, 0xC4, 0x5D, 0x82, 0x37, 0xC4, 0xF9, 0x55, 0x9F, 0x7D, 0x46, 0x61, 0x85, 0xF2, 0x95, 0x39, 0x9F, 0x0A, 0xA3, 0x7D};
	unsigned char ya[32] = {0x59, 0xAD, 0x8A, 0x3C, 0xD1, 0x79, 0x03, 0x28, 0x76, 0x81, 0xBF, 0x9D, 0x21, 0xDA, 0x2E, 0xB3, 0x16, 0xA0, 0xCE, 0x8F, 0xD4, 0x1C, 0x89, 0xCE, 0x1E, 0x2B, 0x3F, 0x1B, 0x8E, 0x04, 0x1A, 0xBA};

	//标准数据
	unsigned char e[32] = {0x38, 0x54, 0xC4, 0x63, 0xFA, 0x3F, 0x73, 0x78, 0x36, 0x21, 0xB1, 0xCE, 0x4E, 0xF8, 0x3F, 0x7C, 0x78, 0x04, 0x8A, 0xAC, 0x79, 0xB2, 0x21, 0xFC, 0xDD, 0x29, 0x08, 0x66, 0xCC, 0x13, 0x11, 0x74};

	//标准签名数据
	unsigned char r[32] = {0x6E, 0x5D, 0xB4, 0x9D, 0xBD, 0x09, 0x92, 0xB9, 0x70, 0x40, 0x08, 0x0A, 0x96, 0x00, 0x3C, 0x72, 0x1C, 0xDB, 0x9C, 0xF6, 0x4C, 0x88, 0xD7, 0x43, 0x21, 0xFC, 0x2F, 0x63, 0x0A, 0xDF, 0x37, 0x74};
	unsigned char s[32] = {0x2F, 0x6D, 0xFF, 0x45, 0x3D, 0xFC, 0x8D, 0x7A, 0x50, 0x6D, 0x3F, 0x52, 0x30, 0x1B, 0xEE, 0x52, 0x9E, 0x62, 0xFD, 0xDD, 0x38, 0x94, 0x8F, 0x0D, 0x5D, 0x2C, 0xBC, 0xBC, 0x55, 0x90, 0x0C, 0xFA};

	ECCrefPublicKey ECC_PubKey;
	ECCSignature ECC_SignatureValue;

	printf("ECC标准数据验证测试:\n");
	printf("-----------------\n");
	printf("\n");

	memset(&ECC_PubKey, 0, sizeof(ECCrefPublicKey));
	memcpy(ECC_PubKey.x, xa, 32);
	memcpy(ECC_PubKey.y, ya, 32);
	ECC_PubKey.bits = 256;

	memset(&ECC_SignatureValue, 0, sizeof(ECCSignature));
	memcpy(ECC_SignatureValue.r, r, 32);
	memcpy(ECC_SignatureValue.s, s, 32);

	//验证签名运算
	rv = SDF_ExternalVerify_ECC(hSessionHandle, SGD_SM2_1, &ECC_PubKey, e, 32, &ECC_SignatureValue);
	if (rv != SDR_OK)
	{
		printf("ECC标准数据验证错误，错误码[0x%08x]\n", rv);
		return 1;
	}
	printf("ECC标准数据验证成功\n");
	return 0;
}

//ECC标准数据解密测试
int ECCStdDataDecTest(SGD_HANDLE hSessionHandle)
{
	unsigned int rv;

	unsigned char da[32] = {0xE7, 0xCB, 0x09, 0x60, 0x6A, 0x53, 0x32, 0x0B, 0x34, 0x7F, 0x61, 0xF3, 0xF1, 0x42, 0xDC, 0xB1, 0x18, 0xF7, 0x23, 0xA9, 0xBC, 0x27, 0x87, 0x9F, 0x28, 0x05, 0xBE, 0x77, 0x8F, 0x24, 0xAE, 0xE5};

	//标准数据
	unsigned char P[32] = {0xEA, 0x4E, 0xC3, 0x52, 0xF0, 0x76, 0xA6, 0xBE};

	//标准密文数据
	unsigned char cx[32] = {0x9E, 0x2A, 0x4A, 0x1A, 0xA4, 0xCF, 0x77, 0x26, 0x22, 0xAB, 0xBB, 0xF1, 0xC6, 0xD6, 0x61, 0xEE, 0x58, 0xFF, 0x01, 0xFF, 0x98, 0x43, 0x78, 0x2E, 0x5A, 0x63, 0x18, 0x5A, 0xBF, 0x6C, 0x2E, 0xFA};
	unsigned char cy[32] = {0x9B, 0x2D, 0x59, 0xB2, 0xB1, 0xE0, 0xD0, 0xA7, 0x95, 0xBF, 0xEF, 0x53, 0xFA, 0xBB, 0x24, 0xC0, 0x3A, 0x02, 0x26, 0x57, 0x51, 0xB8, 0x20, 0x59, 0x12, 0x00, 0xF0, 0xD3, 0x1C, 0x55, 0x1E, 0xD6};
	unsigned char cc[32] = {0x7D, 0xFD, 0xFC, 0x65, 0xCC, 0x9D, 0xF7, 0xD6};
	unsigned char cM[32] = {0x28, 0x7D, 0x5B, 0xF3, 0x35, 0x8B, 0xED, 0x99, 0x28, 0x81, 0xB6, 0x9F, 0xBA, 0x13, 0xC8, 0xAF, 0x76, 0xEF, 0xC1, 0x57, 0x45, 0x5D, 0xB8, 0x1E, 0xCF, 0xAC, 0xC7, 0xB4, 0x43, 0xEA, 0x1D, 0xB0};

	ECCrefPrivateKey ECC_PriKey;
	ECCCipher ECC_CipherData;

	//解密结果
	unsigned char pucOutData[ECCref_MAX_CIPHER_LEN] = {0};
	unsigned int uiOutDataLen;

	printf("ECC标准数据解密测试:\n");
	printf("-----------------\n");
	printf("\n");

	memset(&ECC_PriKey, 0, sizeof(ECCrefPrivateKey));
	memcpy(ECC_PriKey.D, da, 32);
	ECC_PriKey.bits = 256;

	memset(&ECC_CipherData, 0, sizeof(ECCCipher));
	ECC_CipherData.clength = 8;
	memcpy(ECC_CipherData.x, cx, 32);
	memcpy(ECC_CipherData.y, cy, 32);
	memcpy(ECC_CipherData.C, cc, 8);
	memcpy(ECC_CipherData.M, cM, 32);

	//ECC解密运算
	rv = SDF_ExternalDecrypt_ECC(hSessionHandle, SGD_SM2_3, &ECC_PriKey, &ECC_CipherData, pucOutData, &uiOutDataLen);
	if (rv != SDR_OK)
	{
		printf("ECC解密运算错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	//解密结果与标准明文比对
	if ((uiOutDataLen != 8) || (memcmp(P, pucOutData, 8) != 0))
	{
		printf("ECC解密结果与标准明文不相等\n");
		return 1;
	}
	printf("ECC解密结果与标准明文相等\n");
	return 0;
}

int SymmFuncTest(int nDefaultSelect)
{
	int rv, nSel;
	SGD_HANDLE hSessionHandle;
	int recode = 0;

	if ((nDefaultSelect < 1) || (nDefaultSelect > 7))
		nSel = 1;
	else
		nSel = nDefaultSelect;

	//创建会话句柄
	rv = SDF_OpenSession(hDeviceHandle, &hSessionHandle);
	if (rv != SDR_OK)
	{
		printf("打开会话句柄错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	printf("   1|算法正确性测试\n");
	printf("    |    使用标准数据验证对称算法的正确性。\n");
	printf("\n");
	nSel = SymmCorrectnessTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	printf("   2|MAC算法正确性测试\n");
	printf("    |    使用标准数据验证MAC算法的正确性。\n");
	printf("\n");
	nSel = SymmCalculateMACTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	SDF_CloseSession(hSessionHandle);
	return recode;
}

int SymmCorrectnessTest(SGD_HANDLE hSessionHandle)
{
	int rv;
	int num = 1;
	SGD_HANDLE hKeyHandle;
	DEVICEINFO stDeviceInfo;
	unsigned char pIv[16];
	unsigned int nInlen;

	memset(&stDeviceInfo, 0, sizeof(DEVICEINFO));

	rv = SDF_GetDeviceInfo(hSessionHandle, &stDeviceInfo);
	if (rv != SDR_OK)
	{
		printf("\n获取设备信息错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	printf("算法正确性测试:\n");
	printf("---------------------\n");
	printf("\n");
	if (stDeviceInfo.SymAlgAbility & SGD_SM1_ECB & SGD_SYMM_ALG_MASK)
	{
		//标准数据
		unsigned char pbKeyValue[16] = {0x40, 0xbb, 0x12, 0xdd, 0x6a, 0x82, 0x73, 0x86, 0x7f, 0x35, 0x29, 0xd3, 0x54, 0xb4, 0xa0, 0x26};
		unsigned char pbPlainText[16] = {0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x99, 0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0x00};
		unsigned char pbCipherText[16] = {0x6d, 0x7f, 0x45, 0xb0, 0x8b, 0xc4, 0xd9, 0x66, 0x44, 0x4c, 0x86, 0xc2, 0xb0, 0x7d, 0x29, 0x93};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| SM1_ECB运算   | ", num++);
		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		memset(pIv, 0, 16);
		nInlen = 16;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);
		rv = SDF_Encrypt(hSessionHandle, hKeyHandle, SGD_SM1_ECB, pIv, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv == SDR_OK)
		{
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pIv, 0, 16);
			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);

			rv = SDF_Decrypt(hSessionHandle, hKeyHandle, SGD_SM1_ECB, pIv, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，[%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_SM1_CBC & SGD_SYMM_ALG_MASK)
	{
		//标准数据
		unsigned char pbKeyValue[16] = {0x40, 0xbb, 0x12, 0xdd, 0x6a, 0x82, 0x73, 0x86, 0x7f, 0x35, 0x29, 0xd3, 0x54, 0xb4, 0xa0, 0x26};
		unsigned char pbIV[16] = {0xe8, 0x3d, 0x17, 0x15, 0xac, 0xf3, 0x48, 0x63, 0xac, 0xeb, 0x93, 0xe0, 0xe5, 0xab, 0x8b, 0x90};
		unsigned char pbPlainText[32] = {0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x99, 0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0x00, 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff};
		unsigned char pbCipherText[32] = {0x3a, 0x70, 0xb5, 0xd4, 0x9a, 0x78, 0x2c, 0x07, 0x2d, 0xe1, 0x13, 0x43, 0x81, 0x9e, 0xc6, 0x59, 0xf8, 0xfc, 0x7a, 0xf0, 0x5e, 0x7c, 0x6d, 0xfb, 0x5f, 0x81, 0x09, 0x0f, 0x0d, 0x87, 0x91, 0xb2};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| SM1_CBC运算   | ", num++);

		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		nInlen = 32;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);

		rv = SDF_Encrypt(hSessionHandle, hKeyHandle, SGD_SM1_CBC, pbIV, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv == SDR_OK)
		{
			//加密结果与标准密文比较
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);

			rv = SDF_Decrypt(hSessionHandle, hKeyHandle, SGD_SM1_CBC, pbIV, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					printf("运算结果：解密后结果与标准明文数据比较失败。\n");
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，[0x%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_SSF33_ECB & SGD_SYMM_ALG_MASK)
	{
		//与标准数据比较
		unsigned char pbKeyValue[16] = {0x67, 0xbe, 0x03, 0x7c, 0x41, 0x96, 0x6d, 0xdb, 0x8c, 0x36, 0x27, 0x48, 0x5a, 0x05, 0x93, 0xa5};
		unsigned char pbPlainText[16] = {0xa9, 0x37, 0x07, 0x49, 0xfc, 0x06, 0xaf, 0xe6, 0x4e, 0x30, 0x68, 0x01, 0xd2, 0x31, 0xb3, 0xac};
		unsigned char pbCipherText[16] = {0x9a, 0xb7, 0x1c, 0xcc, 0x22, 0x7e, 0x9e, 0x58, 0x7a, 0xa0, 0xe6, 0xcf, 0x49, 0x08, 0x5d, 0x1f};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| SSF33_ECB运算 | ", num++);

		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		memset(pIv, 0, 16);

		nInlen = 16;

		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);

		rv = SDF_Encrypt(hSessionHandle, hKeyHandle, SGD_SSF33_ECB, pIv, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv == SDR_OK)
		{
			//与标准密文数据比较
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pIv, 0, 16);
			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);
			rv = SDF_Decrypt(hSessionHandle, hKeyHandle, SGD_SSF33_ECB, pIv, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					printf("运算结果：解密后结果与标准明文数据比较失败。\n");
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，错误码[0x%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_SSF33_CBC & SGD_SYMM_ALG_MASK)
	{
		//标准数据校验
		unsigned char pbKeyValue[16] = {0x40, 0xbb, 0x12, 0xdd, 0x6a, 0x82, 0x73, 0x86, 0x7f, 0x35, 0x29, 0xd3, 0x54, 0xb4, 0xa0, 0x26};
		unsigned char pbIV[16] = {0xe8, 0x3d, 0x17, 0x15, 0xac, 0xf3, 0x48, 0x63, 0xac, 0xeb, 0x93, 0xe0, 0xe5, 0xab, 0x8b, 0x90};
		unsigned char pbPlainText[32] = {0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x99, 0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0x00, 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff};
		unsigned char pbCipherText[32] = {0xfd, 0x3e, 0x17, 0xf4, 0xde, 0x33, 0xe2, 0x96, 0xf9, 0x9e, 0x37, 0x92, 0x45, 0x6b, 0x76, 0x2b, 0x9e, 0xe7, 0x13, 0x44, 0x5d, 0x91, 0x95, 0xf6, 0x4b, 0x34, 0x1b, 0x3a, 0xe7, 0x5c, 0x68, 0x75};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| SSF33_CBC运算 | ", num++);
		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		nInlen = 32;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);
		rv = SDF_Encrypt(hSessionHandle, hKeyHandle, SGD_SSF33_CBC, pbIV, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv == SDR_OK)
		{
			//与标准密文数据比较
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);
			rv = SDF_Decrypt(hSessionHandle, hKeyHandle, SGD_SSF33_CBC, pbIV, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					printf("运算结果：解密结果与标准明文数据比较失败。\n");
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，错误码[0x%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_AES_ECB & SGD_SYMM_ALG_MASK)
	{
		//与标准数据比较
		unsigned char pbKeyValue[16] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef};
		unsigned char pbPlainText[16] = {0x4e, 0x6f, 0x77, 0x20, 0x69, 0x73, 0x20, 0x74, 0x68, 0x65, 0x20, 0x74, 0x69, 0x6d, 0x65, 0x20};
		unsigned char pbCipherText[16] = {0xde, 0x2e, 0x12, 0xe4, 0x0b, 0xd1, 0xd8, 0x60, 0xe3, 0xe4, 0x24, 0x31, 0x3b, 0xd3, 0x72, 0xdc};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| AES_ECB运算   | ", num++);

		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		memset(pIv, 0, 16);
		nInlen = 16;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);
		rv = SDF_Encrypt(hSessionHandle, hKeyHandle, SGD_AES_ECB, pIv, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv == SDR_OK)
		{
			//与标准密文数据比较
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pIv, 0, 16);
			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);
			rv = SDF_Decrypt(hSessionHandle, hKeyHandle, SGD_AES_ECB, pIv, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					printf("运算结果：解密结果与标准明文数据比较失败。\n");
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，错误码[0x%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_DES_ECB & SGD_SYMM_ALG_MASK)
	{
		//与标准数据比较
		unsigned char pbKeyValue[8] = {0x67, 0xbe, 0x03, 0x7c, 0x41, 0x96, 0x6d, 0xdb};
		unsigned char pbPlainText[8] = {0xa9, 0x37, 0x07, 0x49, 0xfc, 0x06, 0xaf, 0xe6};
		unsigned char pbCipherText[8] = {0x60, 0x78, 0x32, 0xe8, 0xb3, 0x5a, 0x9c, 0x6d};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| DES_ECB运算   | ", num++);

		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 8, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		memset(pIv, 0, 16);
		nInlen = 8;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);
		rv = SDF_Encrypt(hSessionHandle, hKeyHandle, SGD_DES_ECB, pIv, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv == SDR_OK)
		{
			//与标准密文数据比较
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pIv, 0, 16);
			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);
			rv = SDF_Decrypt(hSessionHandle, hKeyHandle, SGD_DES_ECB, pIv, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					printf("运算结果：解密结果与标准数据比较失败。\n");
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，错误码[0x%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_3DES_ECB & SGD_SYMM_ALG_MASK)
	{
		//与标准数据比较
		unsigned char pbKeyValue[16] = {0x40, 0xbb, 0x12, 0xdd, 0x6a, 0x82, 0x73, 0x86, 0x7f, 0x35, 0x29, 0xd3, 0x54, 0xb4, 0xa0, 0x26};
		unsigned char pbPlainText[8] = {0x49, 0x07, 0x37, 0xa9, 0xe6, 0xaf, 0x06, 0xfc};
		unsigned char pbCipherText[8] = {0x43, 0x01, 0xc5, 0x6b, 0x14, 0x00, 0xe7, 0xce};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| 3DES_ECB运算  | ", num++);

		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		memset(pIv, 0, 16);
		nInlen = 8;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);
		rv = SDF_Encrypt(hSessionHandle, hKeyHandle, SGD_3DES_ECB, pIv, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv == SDR_OK)
		{
			//与标准密文数据比较
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pIv, 0, 16);
			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);
			rv = SDF_Decrypt(hSessionHandle, hKeyHandle, SGD_3DES_ECB, pIv, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					printf("运算结果：解密结果与标准数据比较失败。\n");
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，错误码[0x%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_SM4_ECB & SGD_SYMM_ALG_MASK)
	{
		//与标准数据比较
		unsigned char pbKeyValue[16] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10};
		unsigned char pbPlainText[16] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10};
		unsigned char pbCipherText[16] = {0x68, 0x1e, 0xdf, 0x34, 0xd2, 0x06, 0x96, 0x5e, 0x86, 0xb3, 0xe9, 0x4f, 0x53, 0x6e, 0x42, 0x46};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| SM4_ECB运算   | ", num++);

		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		memset(pIv, 0, 16);
		nInlen = 16;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);
		rv = SDF_Encrypt(hSessionHandle, hKeyHandle, SGD_SM4_ECB, pIv, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv == SDR_OK)
		{
			//与标准密文数据比较
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pIv, 0, 16);
			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);
			rv = SDF_Decrypt(hSessionHandle, hKeyHandle, SGD_SM4_ECB, pIv, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					printf("运算结果：解密结果与标准明文数据比较失败。\n");
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，错误码[0x%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_SM4_CBC & SGD_SYMM_ALG_MASK)
	{
		//与标准数据比较
		unsigned char pbKeyValue[16] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10};
		unsigned char pbIV[16] = {0xeb, 0xee, 0xc5, 0x68, 0x58, 0xe6, 0x04, 0xd8, 0x32, 0x7b, 0x9b, 0x3c, 0x10, 0xc9, 0x0c, 0xa7};
		unsigned char pbPlainText[32] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10, 0x29, 0xbe, 0xe1, 0xd6, 0x52, 0x49, 0xf1, 0xe9, 0xb3, 0xdb, 0x87, 0x3e, 0x24, 0x0d, 0x06, 0x47};
		unsigned char pbCipherText[32] = {0x3f, 0x1e, 0x73, 0xc3, 0xdf, 0xd5, 0xa1, 0x32, 0x88, 0x2f, 0xe6, 0x9d, 0x99, 0x6c, 0xde, 0x93, 0x54, 0x99, 0x09, 0x5d, 0xde, 0x68, 0x99, 0x5b, 0x4d, 0x70, 0xf2, 0x30, 0x9f, 0x2e, 0xf1, 0xb7};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| SM4_CBC运算   | ", num++);

		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		nInlen = 32;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);
		rv = SDF_Encrypt(hSessionHandle, hKeyHandle, SGD_SM4_CBC, pbIV, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv == SDR_OK)
		{
			//与标准密文数据比较
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);
			rv = SDF_Decrypt(hSessionHandle, hKeyHandle, SGD_SM4_CBC, pbIV, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					printf("运算结果：解密结果与标准明文数据比较失败。\n");
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，错误码[0x%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}

	if ((stDeviceInfo.SymAlgAbility & SGD_SM4_XTS & SGD_SYMM_ALG_MASK) && (stDeviceInfo.SymAlgAbility & SGD_SM4_XTS & SGD_SYMM_ALG_MODE_MASK))
	{
		//与标准数据比较
		unsigned char pbKeyValue[16] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10};
		unsigned char pbIV[16] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10};
		unsigned char pbPlainText[48] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10,
										 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x11,
										 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x12};
		unsigned char pbCipherText[48] = {0x55, 0x13, 0xa7, 0x57, 0x57, 0xaf, 0xc1, 0xc2, 0xa2, 0xb6, 0xc2, 0x11, 0x6f, 0xeb, 0x2b, 0x19,
										  0x29, 0x53, 0x9b, 0x73, 0xe5, 0x35, 0x00, 0x06, 0xab, 0x29, 0xb6, 0xe0, 0x84, 0x7b, 0xe1, 0x67,
										  0x6d, 0xd9, 0x21, 0x65, 0x41, 0x51, 0x4a, 0x24, 0xc4, 0x19, 0xd3, 0xb7, 0xd7, 0xe0, 0x3c, 0xf1};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| SM4_XTS运算   | ", num++);

		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		nInlen = 48;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);
		rv = SDF_Encrypt_Ex(hSessionHandle, hKeyHandle, hKeyHandle, SGD_SM4_XTS, pbIV, pbPlainText, nInlen, pbTempData, &ulTempDataLen, nInlen);
		if (rv == SDR_OK)
		{
			//与标准密文数据比较
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);
			rv = SDF_Decrypt_Ex(hSessionHandle, hKeyHandle, hKeyHandle, SGD_SM4_XTS, pbIV, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen, ulTempDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					printf("运算结果：解密结果与标准明文数据比较失败。\n");
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，错误码[0x%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_SM7_ECB & SGD_SYMM_ALG_MASK)
	{
		//标准数据 -- 第一组
		//unsigned char pbKeyValue[16] = {0x00,0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,0x99,0xaa,0xbb,0xcc,0xdd,0xee,0xff};
		//unsigned char pbPlainText[8] = {0x77,0x66,0x55,0x44,0x33,0x22,0x11,0x00};
		//unsigned char pbCipherText[8] = {0x67,0xfa,0xa9,0x75,0xf1,0x28,0xd1,0xfc};

		//标准数据 -- 第二组
		//unsigned char pbKeyValue[16] = {0x1F,0xD3,0x84,0xD8,0x6B,0x50,0xBE,0x01,0x21,0x43,0xD6,0x16,0x18,0x15,0x19,0x83};
		//unsigned char pbPlainText[8] = {0xE2,0x73,0x2F,0xB8,0x1D,0x7D,0x7E,0x51};
		//unsigned char pbCipherText[8] = {0xCE,0x3C,0x08,0xD4,0x02,0xAE,0x24,0x7C};

		//标准数据 -- 第三组
		unsigned char pbKeyValue[16] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef};
		unsigned char pbPlainText[8] = {0x1a, 0x17, 0x02, 0xe5, 0xea, 0x62, 0x31, 0xb4};
		unsigned char pbCipherText[8] = {0xaf, 0xa2, 0xb6, 0x9d, 0xca, 0x09, 0xa3, 0xef};

		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;
		unsigned char pbOutData[128] = {0};
		unsigned int ulOutDataLen;

		printf("   %02d| SM7_ECB运算   | ", num++);
		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		nInlen = 8;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);
		rv = SDF_Encrypt(hSessionHandle, hKeyHandle, SGD_SM7_ECB, NULL, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv == SDR_OK)
		{
			if ((nInlen == ulTempDataLen) && (memcmp(pbCipherText, pbTempData, nInlen) == 0))
			{
				printf("运算结果：加密密文与标准密文数据比较成功。\n");
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：加密密文与标准密文数据比较失败。\n");
				return 1;
			}

			memset(pbOutData, 0, sizeof(pbOutData));
			ulOutDataLen = sizeof(pbOutData);

			rv = SDF_Decrypt(hSessionHandle, hKeyHandle, SGD_SM7_ECB, NULL, pbTempData, ulTempDataLen, pbOutData, &ulOutDataLen);
			if (rv == SDR_OK)
			{
				if ((ulOutDataLen == nInlen) && (memcmp(pbPlainText, pbOutData, nInlen) == 0))
				{
					printf("标准数据加密、解密及结果比较均正确。\n");
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
				}
				else
				{
					SDF_DestroyKey(hSessionHandle, hKeyHandle);
					printf("运算结果：解密后结果与标准明文数据比较失败。\n");
					return 1;
				}
			}
			else
			{
				SDF_DestroyKey(hSessionHandle, hKeyHandle);
				printf("运算结果：解密错误，[%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：加密错误，错误码[0x%08x]\n", rv);
			return 1;
		}
	}
	return 0;
}

//计算MAC测试
int SymmCalculateMACTest(SGD_HANDLE hSessionHandle)
{
	int rv;
	int num = 1;
	SGD_HANDLE hKeyHandle;
	DEVICEINFO stDeviceInfo;
	unsigned int nInlen;

	memset(&stDeviceInfo, 0, sizeof(DEVICEINFO));

	rv = SDF_GetDeviceInfo(hSessionHandle, &stDeviceInfo);
	if (rv != SDR_OK)
	{
		printf("\n获取设备信息错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	printf("MAC算法正确性测试:\n");
	printf("---------------------\n");
	printf("\n");
	printf("\n");

	if (stDeviceInfo.SymAlgAbility & SGD_SM1_CBC & SGD_SYMM_ALG_MASK)
	{
		//标准数据
		unsigned char pbKeyValue[16] = {0x40, 0xbb, 0x12, 0xdd, 0x6a, 0x82, 0x73, 0x86, 0x7f, 0x35, 0x29, 0xd3, 0x54, 0xb4, 0xa0, 0x26};
		unsigned char pbIV[16] = {0xe8, 0x3d, 0x17, 0x15, 0xac, 0xf3, 0x48, 0x63, 0xac, 0xeb, 0x93, 0xe0, 0xe5, 0xab, 0x8b, 0x90};
		unsigned char pbPlainText[32] = {0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x99, 0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0x00, 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff};
		unsigned char pbCipherText[32] = {0x3a, 0x70, 0xb5, 0xd4, 0x9a, 0x78, 0x2c, 0x07, 0x2d, 0xe1, 0x13, 0x43, 0x81, 0x9e, 0xc6, 0x59, 0xf8, 0xfc, 0x7a, 0xf0, 0x5e, 0x7c, 0x6d, 0xfb, 0x5f, 0x81, 0x09, 0x0f, 0x0d, 0x87, 0x91, 0xb2};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;

		printf("   %02d| SM1_MAC   | ", num++);

		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		//标准数据计算MAC测试
		nInlen = 32;
		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);

		rv = SDF_CalculateMAC(hSessionHandle, hKeyHandle, SGD_SM1_MAC, pbIV, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv != SDR_OK)
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：标准数据计算MAC错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		//销毁对称密钥
		SDF_DestroyKey(hSessionHandle, hKeyHandle);

		//与标准MAC比较
		if ((ulTempDataLen != 16) || (memcmp(&pbCipherText[16], pbTempData, 16) != 0))
		{
			printf("运算结果：标准数据计算MAC结果值与标准MAC值不相等。\n");
			return 1;
		}
		else
		{
			printf("标准数据计算MAC值及结果比较均正确。\n");
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_SSF33_CBC & SGD_SYMM_ALG_MASK)
	{
		//标准数据校验
		unsigned char pbKeyValue[16] = {0x40, 0xbb, 0x12, 0xdd, 0x6a, 0x82, 0x73, 0x86, 0x7f, 0x35, 0x29, 0xd3, 0x54, 0xb4, 0xa0, 0x26};
		unsigned char pbIV[16] = {0xe8, 0x3d, 0x17, 0x15, 0xac, 0xf3, 0x48, 0x63, 0xac, 0xeb, 0x93, 0xe0, 0xe5, 0xab, 0x8b, 0x90};
		unsigned char pbPlainText[32] = {0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x99, 0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0x00, 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff};
		unsigned char pbCipherText[32] = {0xfd, 0x3e, 0x17, 0xf4, 0xde, 0x33, 0xe2, 0x96, 0xf9, 0x9e, 0x37, 0x92, 0x45, 0x6b, 0x76, 0x2b, 0x9e, 0xe7, 0x13, 0x44, 0x5d, 0x91, 0x95, 0xf6, 0x4b, 0x34, 0x1b, 0x3a, 0xe7, 0x5c, 0x68, 0x75};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;

		printf("   %02d| SSF33_MAC | ", num++);
		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		//标准数据计算MAC测试
		nInlen = 32;

		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);
		rv = SDF_CalculateMAC(hSessionHandle, hKeyHandle, SGD_SSF33_MAC, pbIV, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv != SDR_OK)
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：标准数据计算MAC错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		//销毁对称密钥
		SDF_DestroyKey(hSessionHandle, hKeyHandle);

		//与标准MAC比较
		if ((ulTempDataLen != 16) || (memcmp(&pbCipherText[16], pbTempData, 16) != 0))
		{
			printf("运算结果：标准数据计算MAC结果值与标准MAC值不相等。\n");
			return 1;
		}
		else
		{
			printf("标准数据计算MAC值及结果比较均正确。\n");
		}
	}

	if (stDeviceInfo.SymAlgAbility & SGD_SM4_CBC & SGD_SYMM_ALG_MASK)
	{
		//与标准数据比较
		unsigned char pbKeyValue[16] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10};
		unsigned char pbIV[16] = {0xeb, 0xee, 0xc5, 0x68, 0x58, 0xe6, 0x04, 0xd8, 0x32, 0x7b, 0x9b, 0x3c, 0x10, 0xc9, 0x0c, 0xa7};
		unsigned char pbPlainText[32] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10, 0x29, 0xbe, 0xe1, 0xd6, 0x52, 0x49, 0xf1, 0xe9, 0xb3, 0xdb, 0x87, 0x3e, 0x24, 0x0d, 0x06, 0x47};
		unsigned char pbCipherText[32] = {0x3f, 0x1e, 0x73, 0xc3, 0xdf, 0xd5, 0xa1, 0x32, 0x88, 0x2f, 0xe6, 0x9d, 0x99, 0x6c, 0xde, 0x93, 0x54, 0x99, 0x09, 0x5d, 0xde, 0x68, 0x99, 0x5b, 0x4d, 0x70, 0xf2, 0x30, 0x9f, 0x2e, 0xf1, 0xb7};
		unsigned char pbTempData[128] = {0};
		unsigned int ulTempDataLen;

		printf("   %02d| SM4_MAC   | ", num++);
		rv = SDF_ImportKey(hSessionHandle, pbKeyValue, 16, &hKeyHandle);
		if (rv != SDR_OK)
		{
			printf("导入明文会话密钥错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		//标准数据计算MAC测试
		nInlen = 32;

		memset(pbTempData, 0, sizeof(pbTempData));
		ulTempDataLen = sizeof(pbTempData);

		rv = SDF_CalculateMAC(hSessionHandle, hKeyHandle, SGD_SM4_MAC, pbIV, pbPlainText, nInlen, pbTempData, &ulTempDataLen);
		if (rv != SDR_OK)
		{
			SDF_DestroyKey(hSessionHandle, hKeyHandle);
			printf("运算结果：标准数据计算MAC错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		//销毁对称密钥
		SDF_DestroyKey(hSessionHandle, hKeyHandle);

		//与标准MAC比较
		if ((ulTempDataLen != 16) || (memcmp(&pbCipherText[16], pbTempData, 16) != 0))
		{
			printf("运算结果：标准数据计算MAC结果值与标准MAC值不相等。\n");
			return 1;
		}
		else
		{
			printf("标准数据计算MAC值及结果比较均正确。\n");
		}
	}

	return 0;
}

int HashFuncTest(int nDefaultSelect)
{
	int rv;
	int nSel;
	int recode = 0;
	SGD_HANDLE hSessionHandle;

	if ((nDefaultSelect < 1) || (nDefaultSelect > 2))
		nSel = 1;
	else
		nSel = nDefaultSelect;

	//创建会话句柄
	rv = SDF_OpenSession(hDeviceHandle, &hSessionHandle);
	if (rv != SDR_OK)
	{
		printf("打开会话句柄错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	printf("   1|杂凑算法运算测试\n");
	printf("    |    对输入数据进行杂凑运算并输出结果。\n");
	printf("\n");
	nSel = HashTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	printf("   2|杂凑算法正确性测试\n");
	printf("    |    使用标准数据验证杂凑算法的正确性。\n");
	printf("\n");
	nSel = HashCorrectnessTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	SDF_CloseSession(hSessionHandle);
	return recode;
}

int HashTest(SGD_HANDLE hSessionHandle)
{
	int rv;
	unsigned int puiAlg[20];
	int nSelAlg = 1;
	int i = 1;
	int nInlen, nOutlen;
	DEVICEINFO stDeviceInfo;
	unsigned char pIndata[16384], pOutdata[128];

	memset(&stDeviceInfo, 0, sizeof(DEVICEINFO));

	rv = SDF_GetDeviceInfo(hSessionHandle, &stDeviceInfo);
	if (rv != SDR_OK)
	{
		printf("\n获取设备信息错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	printf("哈希算法运算测试:\n");
	printf("-------------\n");
	printf("\n");
	printf("当前密码卡支持以下算法，默认测试第一项。\n");
	printf("\n");

	if (stDeviceInfo.HashAlgAbility & SGD_SM3 & 0xFF)
	{
		printf("  %d | SGD_SM3\n\n", i);
		puiAlg[i++] = SGD_SM3;
	}
	if (stDeviceInfo.HashAlgAbility & SGD_SHA1 & 0xFF)
	{
		printf("  %d | SGD_SHA1\n\n", i);
		puiAlg[i++] = SGD_SHA1;
	}
	if (stDeviceInfo.HashAlgAbility & SGD_SHA224 & 0xFF)
	{
		printf("  %d | SGD_SHA224\n\n", i);
		puiAlg[i++] = SGD_SHA224;
	}
	if (stDeviceInfo.HashAlgAbility & SGD_SHA256 & 0xFF)
	{
		printf("  %d | SGD_SHA256\n\n", i);
		puiAlg[i++] = SGD_SHA256;
	}
	if (stDeviceInfo.HashAlgAbility & SGD_SHA384 & 0xFF)
	{
		printf("  %d | SGD_SHA384\n\n", i);
		puiAlg[i++] = SGD_SHA384;
	}
	if (stDeviceInfo.HashAlgAbility & SGD_SHA512 & 0xFF)
	{
		printf("  %d | SGD_SHA512\n\n", i);
		puiAlg[i++] = SGD_SHA512;
	}
	if (stDeviceInfo.HashAlgAbility & SGD_MD5 & 0xFF)
	{
		printf("  %d | SGD_MD5\n\n", i);
		puiAlg[i++] = SGD_MD5;
	}
	nSelAlg = 1;
	nInlen = 1024;
	printf("算法标识：0x%08x\n", puiAlg[nSelAlg]);
	printf("数据长度：%d\n", nInlen);

	rv = SDF_GenerateRandom(hSessionHandle, nInlen, pIndata);
	if (rv == SDR_OK)
	{
		rv = SDF_HashInit(hSessionHandle, puiAlg[nSelAlg], NULL, NULL, 0);
		if (rv == SDR_OK)
		{
			rv = SDF_HashUpdate(hSessionHandle, pIndata, nInlen);
			if (rv == SDR_OK)
			{
				rv = SDF_HashFinal(hSessionHandle, pOutdata, &nOutlen);
				if (rv == SDR_OK)
				{
					PrintData("运算结果", pOutdata, nOutlen, 16);
				}
				else
				{
					printf("运算结果：SDF_HashFinal()错误，[0x%08x]\n", rv);
					return 1;
				}
			}
			else
			{
				printf("运算结果：SDF_HashUpdate()错误，[0x%08x]\n", rv);
				return 1;
			}
		}
		else
		{
			printf("运算结果：SDF_HashInit()错误，[0x%08x]\n", rv);
			return 1;
		}
	}
	else
	{
		printf("运算结果：产生随机加密数据错误，[0x%08x]\n", rv);
		return 1;
	}

	return 0;
}

int HashCorrectnessTest(SGD_HANDLE hSessionHandle)
{
	unsigned int rv;
	int num = 1;

	DEVICEINFO stDeviceInfo;

	memset(&stDeviceInfo, 0, sizeof(DEVICEINFO));

	rv = SDF_GetDeviceInfo(hSessionHandle, &stDeviceInfo);
	if (rv != SDR_OK)
	{
		printf("\n获取设备信息错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	printf("杂凑算法正确性测试:\n");
	printf("---------------------\n");
	printf("\n");

	if (stDeviceInfo.HashAlgAbility & SGD_SM3)
	{
		unsigned char bHashData[64] = {0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64,
									   0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64,
									   0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64,
									   0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64, 0x61, 0x62, 0x63, 0x64};

		unsigned char bHashStdResult[32] = {0xde, 0xbe, 0x9f, 0xf9, 0x22, 0x75, 0xb8, 0xa1, 0x38, 0x60, 0x48, 0x89, 0xc1, 0x8e, 0x5a, 0x4d,
											0x6f, 0xdb, 0x70, 0xe5, 0x38, 0x7e, 0x57, 0x65, 0x29, 0x3d, 0xcb, 0xa3, 0x9c, 0x0c, 0x57, 0x32};
		unsigned char bHashResult[256];
		unsigned int uiHashResultLen;

		printf("   %02d|   SM3运算   | ", num++);

		rv = SDF_HashInit(hSessionHandle, SGD_SM3, NULL, NULL, 0);
		if (rv != SDR_OK)
		{
			printf("SDF_HashInit函数错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		rv = SDF_HashUpdate(hSessionHandle, bHashData, 64);
		if (rv != SDR_OK)
		{
			printf("SDF_HashUpdate函数错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		memset(bHashResult, 0x0, sizeof(bHashResult));
		uiHashResultLen = sizeof(bHashResult);

		rv = SDF_HashFinal(hSessionHandle, bHashResult, &uiHashResultLen);
		if (rv != SDR_OK)
		{
			printf("SDF_HashFinal函数错误，错误码[0x%08x]\n", rv);
			return 1;
		}

		//哈希值与标准哈希值比对
		if ((uiHashResultLen != 32) || (memcmp(bHashStdResult, bHashResult, 32) != 0))
		{
			printf("杂凑值与标准数据杂凑值比较失败\n");
			return 1;
		}
		else
		{
			printf("标准数据杂凑运算验证成功。\n");
		}
	}

	return 0;
}

int FileFuncTest(int nDefaultSelect)
{
	int nSel, rv;
	SGD_HANDLE hSessionHandle;
	int recode = 0;

	if ((nDefaultSelect < 1) || (nDefaultSelect > 4))
		nSel = 1;
	else
		nSel = nDefaultSelect;

	//创建会话句柄
	rv = SDF_OpenSession(hDeviceHandle, &hSessionHandle);
	if (rv != SDR_OK)
	{
		printf("打开会话句柄错误，错误码[0x%08x]\n", rv);
		return 1;
	}

	printf("   1|用户文件操作测试\n");
	printf("    |    根据指定的文件名和大小，创建用户文件。\n");
	printf("    |    将数据写入用户文件。\n");
	printf("    |    读取用户文件。\n");
	printf("    |    根据指定的文件名删除用户文件。\n");
	printf("\n");
	nSel = CreateFileTest(hSessionHandle);
	if (nSel == 1)
	{
		recode = 1;
	}

	SDF_CloseSession(hSessionHandle);

	return recode;
}

int CreateFileTest(SGD_HANDLE hSessionHandle)
{
	char filename[256];
	int nInlen;
	int nOffset = 0;
	unsigned char inData[65536];
	unsigned int rv;

	printf("创建用户文件测试:\n");
	printf("-----------------\n");
	strcpy(filename, "keycard_test_del_file");
	nInlen = 32;
	printf("文件名称：%s\n", filename);
	printf("文件大小：%d\n", nInlen);

	rv = SDF_CreateFile(hSessionHandle, filename, (unsigned int)strlen(filename), nInlen);
	if (rv != SDR_OK)
	{
		printf("执行结果：创建文件错误，[0x%08x]\n", rv);
		return 1;
	}
	printf("执行结果：创建文件成功\n");

	rv = SDF_GenerateRandom(hSessionHandle, nInlen, inData);
	if (rv != SDR_OK)
	{
		printf("产生随机数据错误，[0x%08x]\n", rv);
		return 1;
	}

	rv = SDF_WriteFile(hSessionHandle, filename, (unsigned int)strlen(filename), nOffset, nInlen, inData);
	if (rv != SDR_OK)
	{
		printf("执行结果：写文件错误，[0x%08x]\n", rv);
		return 1;
	}
	printf("执行结果：写文件成功\n");
	PrintData("写入数据", inData, nInlen, 16);

	rv = SDF_ReadFile(hSessionHandle, filename, (unsigned int)strlen(filename), nOffset, &nInlen, inData);
	if (rv != SDR_OK)
	{
		printf("执行结果：读文件错误，[0x%08x]\n", rv);
		return 1;
	}
	printf("执行结果：读文件成功\n");
	PrintData("读取数据", inData, nInlen, 16);

	rv = SDF_DeleteFile(hSessionHandle, filename, (unsigned int)strlen(filename));
	if (rv != SDR_OK)
	{
		printf("执行结果：删除文件错误，错误码[%08x]\n", rv);
		return 1;
	}
	printf("执行结果：删除文件成功\n");

	return 0;
}