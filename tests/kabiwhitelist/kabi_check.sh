#!/usr/bin/bash
# Copyright (c) 2023 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @liqiang1118
# Create: 2023-05-15

mkdir /usr/share/oech/lib/tests/kabiwhitelist/test_log
testdir="/usr/share/oech/lib/tests/kabiwhitelist/test_log"
cd $testdir

os_version=`cat /etc/openEuler-latest|grep openeulerversion |awk -F = '{print $2}'`
arch=`uname -m`
url="https://gitee.com/src-openeuler/kernel/raw/$os_version/kabi_whitelist_$arch"
wget $url
kernel_version=`uname -r`
symvers_gz="symvers-"$kernel_version".gz"
cp /boot/$symvers_gz   /usr/share/oech/lib/tests/kabiwhitelist/test_log
gunzip /usr/share/oech/lib/tests/kabiwhitelist/test_log/$symvers_gz

# Desc: Test kabi
# Input: xxx.ko or xxx.rpm
function test_kabi() {
	cat $kabi.kabi |while read line;
	do
		kabiname=`echo $line |awk '{print $2}'`
		filename=`echo $line |awk '{print $1}'`
		cat kabi_whitelist_$arch|grep "$kabiname" >> $filename.txt
		have=`cat $filename.txt|wc -l`
		if [ $have == 0 ]; then
			echo $line >> $kabi"_change_"$arch
		fi
	done
	cat $kabi.kabi |while read line;
	do	
		real=`echo $line|awk '{print $2}'`
		if [ -f $kabi"_change_"$arch ]; then
			white_list=`cat $kabi"_change_"$arch|grep "$real" |wc -l`
			if [ $white_list == 0 ]; then
				echo $line >> $kabi"_white_"$arch
			fi
		else
			echo $line >> $kabi"_white_"$arch
		fi
	done
}


function test_inlist(){
	if [ -f $kabi"_change_"$arch ]; then
		cat $kabi"_change_"$arch |while read line;
		do
			changekb=`echo $line |awk '{print $2}'`
			inos=`cat  symvers-"$kernel_version" |grep $changekb|wc -l`
			if [ $inos == 0 ]; then 
				echo $changekb >> $kabi"_changeos"
			else
				echo $changekb >> $kabi"_inlist"
			fi
		done
	fi
}


function real_result(){
	if [ -f $kabi"_change_"$arch ]; then
		cat $kabi"_change_"$arch|while read line;
		do
			inlist=`echo $line|awk '{print $2}'`
			noin=`cat $kabi"_changeos" |grep $inlist|wc -l`
			if [ $noin == 0 ]; then 
				echo $line >> $kabi"_change"

			fi

		done
	fi
}

echo "####################KABI TEST START####################"
cat /usr/share/oech/lib/config/test_config.yaml|grep name|awk -F "'" '{print $2}' >> dir.txt
if_test=`cat dir.txt|wc -w`
if [ $if_test == 0 ]; then
	echo "Please configure the board information in the configuration file" > change.txt
	echo "no ko or rpm" >> nokorpm.txt
	cat change.txt
fi
cat dir.txt|while read line;
do
	lineword=`echo $line |wc -w`
	if [ "$lineword" -gt 0 ]; then
		echo $line >> dirt.txt
	fi
done
cat dirt.txt |while read line;
do
	if [ -f /root/$line ]; then
		cp /root/$line  ./
		echo $line >> dirth
	fi
done
cat dirth|while read line;
do
	for i in $line
	do
		class=`echo $i|awk -F . '{print $NF}'`
		if [ $class == ko ]; then
			kabi=`echo $i|awk -F . '{print $1}'`
			modprobe --dump $i > $kabi.kabi
			test_kabi
			test_inlist
			real_result
		elif [ $class == rpm ]; then
			echo "this is a rpm please wait" > /dev/null
			rpm2cpio $i |cpio -div
			find ./  -name   "*.ko*" |grep module >> rpmko
		 	ifrpm=`cat rpmko|wc -l`
			if [ $ifrpm == 0 ]; then
				echo "Please check rpm" > rpmchange
				echo "Please check rpm"
				exit 0
			else
				echo "$i rpm decompression completed"
			fi
			cat rpmko|while read line;
			do
				cp $line ./
				koname=`echo $line |awk -F "/" '{print $NF}'`
				kabi=`echo $koname|awk -F . '{print $1}' `
				modprobe --dump $koname  > $kabi.kabi
				echo $koname >> realname
				test_kabi
				test_inlist
				real_result
			done
		fi
	done
done


# save test log
cat dirth |grep ko >> realname
cat realname |while read line;
do
	kabi=`echo $line |awk -F . '{print $1}'`
	if [ ! -f $kabi"_change_"$arch ]; then
		echo "$kabi kabi $arch test pass" >> result
	else
		echo "$kabi kabi $arch test fail" >> result 
	fi
done
echo "Test results are as follows"
cat result
cat realname|grep ko |awk -F . '{print $1}' > res.txt
cat res.txt |while read line;
do
	if [ -f $line"_change" ] || [ -f $line"_white_"$arch ]; then
		if [ -f $line"_change" ]; then
			whitenum=`cat $line"_change" |wc -l`
			echo "Here are $line.ko KABI not in whitelist count=$whitenum"
			cat $line"_change"
		fi
		if [ -f $line"_white_"$arch ]; then
			notnum=`cat $line"_white_"$arch |wc -l`
			echo "Here are $line.ko KABI in whitelist count=$notnum"
		        cat $line"_white_"$arch
		fi
	fi
	if [ -f $line"_changeos" ]; then
		echo "Here are $line.ko KABI not in OS KABI list"
		cat $line"_changeos"
	fi	
done
