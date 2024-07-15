#!/usr/bin/env bash

set -e

rootdir=$(readlink -f $(dirname $0))/..

function linux_iter_pci {
	# Argument is the class code
	# TODO: More specifically match against only class codes in the grep
	# step.
	lspci -mm -n -D | grep $1 | tr -d '"' | awk -F " " '{print $1}'
}

function linux_bind_driver() {
	bdf="$1"
	driver_name="$2"
	old_driver_name="no driver"
	ven_dev_id=$(lspci -n -s $bdf | cut -d' ' -f3 | sed 's/:/ /')

	if [ -e "/sys/bus/pci/devices/$bdf/driver" ]; then
		old_driver_name=$(basename $(readlink /sys/bus/pci/devices/$bdf/driver))

		if [ "$driver_name" = "$old_driver_name" ]; then
			return 0
		fi

		echo "$ven_dev_id" > "/sys/bus/pci/devices/$bdf/driver/remove_id" 2> /dev/null || true
		echo "$bdf" > "/sys/bus/pci/devices/$bdf/driver/unbind"
	fi

	echo "$bdf ($ven_dev_id): $old_driver_name -> $driver_name"

	if [ "$driver_name" = "nvme" ]
        then
                echo 1 > /sys/bus/pci/devices/$bdf/remove
                sleep 1
                echo 1 > /sys/bus/pci/rescan
        else
                echo "$ven_dev_id" > "/sys/bus/pci/drivers/$driver_name/new_id" 2> /dev/null || true
                echo "$bdf" > "/sys/bus/pci/drivers/$driver_name/bind" 2> /dev/null || true
        fi
}

function linux_hugetlbfs_mount() {
	mount | grep ' type hugetlbfs ' | awk '{ print $3 }'
}

function is_device_in_except_device_list() {
	exists_flag=0
	if [ $# -gt 1 ]; then
		except_dev_list=$2
	fi

	for dev in ${except_dev_list[@]}
	do
		if [ "$dev" == "$1" ]; then
			exists_flag=1
		fi
	done
	echo ${exists_flag}
}

function config_linux_device {
	if [ $# -gt 0 ]; then
		configlist=$*
		echo configure devices $configlist
	else
		echo "need to specify at least one device to bind uio driver."
		exit 1
	fi
	driver_name=uio_pci_generic

	# NVMe
	modprobe $driver_name || true
	for bdf in ${configlist[@]}; do
		existflag=0
		for confbdf in $(linux_iter_pci 0108); do
			if [ "$bdf" == "$confbdf" ]; then
				linux_bind_driver "$bdf" "$driver_name"
				existflag=1
				break
			fi
		done
		if [ $existflag -eq 0 ]; then
			echo "nvme device \"$bdf\" is not in present"
		fi
	done
	config_linux_hugepage
}

function configure_linux {
	if [ $# -gt 0 ]; then
		exceptdevlist=$*
		echo configure devices except $exceptdevlist
	fi
	# Use uio, Not IOMMU.
	driver_name=uio_pci_generic

	# NVMe
	modprobe $driver_name || true
	for bdf in $(linux_iter_pci 0108); do
		need_configure=`is_device_in_except_device_list ${bdf} "${exceptdevlist}"`
		if [ $need_configure -ne 0 ]; then
			continue
		fi
		linux_bind_driver "$bdf" "$driver_name"
	done

	echo "1" > "/sys/bus/pci/rescan"

	config_linux_hugepage
}

function config_linux_hugepage {
	hugetlbfs_mount=$(linux_hugetlbfs_mount)

	if [ -z "$hugetlbfs_mount" ]; then
		hugetlbfs_mount=/mnt/huge
		echo "Mounting hugetlbfs at $hugetlbfs_mount"
		mkdir -p "$hugetlbfs_mount"
		mount -t hugetlbfs nodev "$hugetlbfs_mount"
	fi
	echo "$NRHUGE" > /proc/sys/vm/nr_hugepages
}

function reset_linux {
	# NVMe
	modprobe nvme || true
	for bdf in $(linux_iter_pci 0108); do
		linux_bind_driver "$bdf" nvme
	done

	echo "1" > "/sys/bus/pci/rescan"

	hugetlbfs_mount=$(linux_hugetlbfs_mount)
	rm -f "$hugetlbfs_mount"/spdk*map_*
}

function status_linux {
	echo "NVMe devices"

	echo -e "BDF\t\tNuma Node\tDriver name\t\tDevice name"
	for bdf in $(linux_iter_pci 0108); do
		driver=`grep DRIVER /sys/bus/pci/devices/$bdf/uevent |awk -F"=" '{print $2}'`
		node=`cat /sys/bus/pci/devices/$bdf/numa_node`;
		if [ "$driver" = "nvme" ]; then
			if [ -d "/sys/bus/pci/devices/$bdf/nvme" ]; then
				name="\t"`ls /sys/bus/pci/devices/$bdf/nvme`;
			else
				name="\t"`ls /sys/bus/pci/devices/$bdf/misc`;
			fi
		else
			name="-";
		fi
		echo -e "$bdf\t$node\t\t$driver\t\t$name";
	done
}

function reset_device_linux {
	#NVMe
	if [ $# -gt 0 ]; then
		resetdevlist=$*
		echo reset nvme devices $resetdevlist
	else
		echo no devices to reset
		return
	fi

	for bdf in ${resetdevlist[@]}; do
		exist=0
		for existbdf in $(linux_iter_pci 0108); do
			if [[ "$existbdf" == "$bdf" ]]; then
				exist=1
			fi
		done

		if [ $exist -eq 0 ]; then
			echo nvme device \"$bdf\" is not in present
			continue
		fi

		linux_bind_driver "$bdf" nvme
	done
}

function reset_all_linux {
	# NVMe
	echo "1" > "/sys/bus/pci/rescan"
	reset_device_linux $(linux_iter_pci 0108)

	hugetlbfs_mount=$(linux_hugetlbfs_mount)
	rm -f "$hugetlbfs_mount"/spdk*map_*
}

function help_linux {
	# NVMe
	echo ""
	echo "setup.sh"
	echo "setup.sh config"
	echo "setup.sh status"
	echo "setup.sh reset"
	echo "setup.sh hugepage"
	echo "setup.sh config except_device=\"pci_addr\""
	echo "setup.sh config except_device=\"pci_addr1,pci_addr2,pci_addr3,...\""
	echo "setup.sh config_device \"pci_addr\""
	echo "setup.sh config_device \"pci_addr1,pci_addr2,pci_addr3,...\""
	echo "setup.sh reset_device \"pci_addr\""
	echo "setup.sh reset_device \"pci_addr1,pci_addr2,pci_addr3,...\""
	echo "setup.sh reset_all"
	echo ""
}

function configure_freebsd {
	TMP=`mktemp`

	# NVMe
	GREP_STR="class=0x010802"

	AWK_PROG="{if (count > 0) printf \",\"; printf \"%s:%s:%s\",\$2,\$3,\$4; count++}"
	echo $AWK_PROG > $TMP

	BDFS=`pciconf -l | grep "${GREP_STR}" | awk -F: -f $TMP`

	kldunload nic_uio.ko || true
	kenv hw.nic_uio.bdfs=$BDFS
	kldload nic_uio.ko
	rm $TMP

	kldunload contigmem.ko || true
	kenv hw.contigmem.num_buffers=$((NRHUGE * 2 / 256))
	kenv hw.contigmem.buffer_size=$((256 * 1024 * 1024))
	kldload contigmem.ko
}

function reset_freebsd {
	kldunload contigmem.ko || true
	kldunload nic_uio.ko || true
}

function get_slot_id {
	pciaddr=$1

	return_msg=`lspci -vvv -xxx -s "$pciaddr"  | grep -i "Slot:"`
	slot_id=${return_msg##* }

	echo $slot_id
}

function get_except_device_linux {
	param=$1
	if [[ $param == except_device=* ]]; then
		devstr=${param#*=}
		OLD_IFS="$IFS"
		IFS=","
		expdev=($devstr)
		IFS=$OLD_IFS
	fi
	if [ ${#expdev[@]} -ne 0 ]; then
		echo ${expdev[@]}
	fi
}

function get_device_linux {
	devstr=$1
	OLD_IFS="$IFS"
	IFS=","
	resetdev=($devstr)
	IFS=$OLD_IFS

	if [ ${#resetdev[@]} -ne 0 ]; then
		echo ${resetdev[@]}
	fi
}

: ${NRHUGE:=1024}

username=$1
mode=$2

if [ "$username" = "reset" -o "$username" = "config" -o "$username" = "status" ]; then
	mode="$username"
	username=""
fi

if [ "$username" = "reset_device" -o "$username" = "reset_all" -o "$username" = "help" ]; then
	mode="$username"
	username=""
fi

if [ "$username" = "config_device" -o "$username" = "hugepage" ]; then
	mode="$username"
	username=""
fi

if [ "$mode" == "" ]; then
	mode="config"
fi

if [ "$username" = "" ]; then
	username="$SUDO_USER"
	if [ "$username" = "" ]; then
		username=`logname 2>/dev/null` || true
	fi
fi

if [ "$mode" == "config" ]; then
	paramcnt=$#
	if [ $paramcnt -eq 2 ]; then
		paramstr=$2
		exceptdev=`get_except_device_linux $paramstr`
	fi
fi

if [ "$mode" == "reset_device" ]; then
	paramcnt=$#
	if [ $paramcnt -eq 2 ]; then
		paramstr=$2
		resetdev=`get_device_linux $paramstr`
	fi
fi

if [ "$mode" == "config_device" ]; then
	paramcnt=$#
	if [ $paramcnt -eq 2 ]; then
		paramstr=$2
		configdev=`get_device_linux $paramstr`
	fi
fi

if [ `uname` = Linux ]; then
	if [ "$mode" == "config" ]; then
       configure_linux $exceptdev
	elif [ "$mode" == "reset" ]; then
		reset_linux
	elif [ "$mode" == "status" ]; then
		status_linux
	elif [ "$mode" == "reset_device" ]; then
		reset_device_linux $resetdev
	elif [ "$mode" == "reset_all" ]; then
		reset_all_linux
	elif [ "$mode" == "help" ]; then
		help_linux
	elif [ "$mode" == "config_device" ]; then
		config_linux_device $configdev
	elif [ "$mode" == "hugepage" ]; then
		config_linux_hugepage
	fi
else
	if [ "$mode" == "config" ]; then
		configure_freebsd
	elif [ "$mode" == "reset" ]; then
		reset_freebsd
	fi
fi
