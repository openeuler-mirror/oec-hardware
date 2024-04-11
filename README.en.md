<!-- TOC -->

- [Overview](#Overview)
  - [tool describes](#tool describes)
  - [Compatibility Conclusion Inheritance Description](#Compatibility Conclusion Inheritance Description)
    - [Overall compatibility Conclusion Inheritance strategy](#Overall compatibility Conclusion Inheritance strategy)
    - [Board Compatibility Conclusion Inheritance Strategy](#Board Compatibility Conclusion Inheritance Strategy)
  - [version release](#version release)
    - [Version Maintenance Statement](#Version Maintenance Statement)
  - [tool uses](#tool uses)
  - [use process](#use process)
    - [User Usage Process](#User Usage Process)
  - [operating environment](#operating environment)
    - [environmental requirements](#environmental requirements)
    - [Operating environment networking](#Operating environment networking)
- [tool mounting](#tool mounting)
  - [prerequisite](#prerequisite)
  - [Get the installation package](#Get the installation package)
  - [installation process](#installation process)
    - [Client](#Client)
    - [Server](#Server)
- [use guidance](#use guidance)
  - [prerequisite](#prerequisite-1)
  - [using step](#using step)
- [result acquisition](#result acquisition)
  - [view results](#view results)
  - [results show](#results show)
  - [Review of test results](#Review of test results)
- [Test item introduction](#Test item introduction)
  - [Existing test items](#Existing test items)
- [Community Developer Involvement Presentations](#Community Developer Involvement Presentations)
  - [environment deployment](#environment deployment)
  - [New test item](#New test item)
- [FAQ](#FAQ)

<!-- /TOC -->

# Overview

## tool describes

oec-hardware tool is a hardware compatibility test tool provided by openEuler community. oec-hardware provides compatibility verification test of server whole machine, board and openEuler. Verification is limited to basic function verification, excluding performance test and other tests. 

Hardware manufacturers can use oec-hardware when they need to verify the compatibility of hardware products with openEuler. The community provides a hardware compatibility test process, and hardware manufacturers can refer to the community compatibility adaptation process to adapt to openEuler.

For hardware products tested by oec-hardware tools, openEuler will publish compatibility lists on the community website, and hardware manufacturers will publish corresponding compatibility information on the manufacturer's website.

# Compatibility Conclusion Inheritance Description

## Overall compatibility Conclusion Inheritance strategy

If the verification adapter has the same motherboard and CPU generation, the compatibility conclusion can be inherited. 

## Board Compatibility Conclusion Inheritance Strategy

The card type is generally confirmed by quadruples. 

```
Quadruple tuple information:
    - vendorID: Chip manufacturer ID
    - deviceID: Chip model ID
    - svID: Board manufacturer ID
    - ssID: Board model ID

Ways to view the quadruple tuple:
    - View it through iBMC
    - Run the command "lspci -nvv" in the system
```

The board compatibility conclusion inherits the following three points: 

1. vendorID and deviceID are different 

   Unable to inherit compatibility conclusions. 

2. vendorID and deviceID, svID are different 

   The chip model is the same but the board manufacturer is different, and the compatibility conclusion cannot be inherited. 

3. Same vendorID, deviceID, svID 

   Different boards made of the same chip can inherit the compatibility conclusion on behalf of the same board manufacturer. 

4. Same vendorID, deviceID, svID, ssID 

   Represents the same board manufacturer, the same series of boards made of the same chip, the same quadruple information, and can inherit the compatibility conclusion. The manufacturer evaluates this series of boards by himself, and can write representative board names. 

The board manufacturer refers to the compatibility list of the community and the board being adapted. If the compatibility conclusion can be inherited, it needs to be explained in the corresponding adaptation issue. The compatibility sig group will conduct manual review, and the corresponding compatibility list will be issued after the review is passed. 

# version release

Detailed release strategy and release plan see `docs/design_docs/oech_rpm_version_design.md` 

## Version Maintenance Statement

oec-hardware-version 1.1.1 will no longer be updated and maintained. Please obtain the latest version of oec-hardware for installation and use. 

# tool uses

## use process

### User Usage Process

![user-flow](docs/pictures/user-flow.png)

## operating environment

### environmental requirements

#### Environmental requirements for complete machine test

| Project            | Requirements                                                 |
| ------------------ | ------------------------------------------------------------ |
| Number of machines | Two complete machines are required, and the service network interface is interconnected. |
| Hardware           | At least one RAID card and one NIC (including integrated motherboard hardware) |
| Memory内存         | Recommended full                                             |

#### Board test environment requirements

| Project       | Requirements                                                 |
| ------------- | ------------------------------------------------------------ |
| server models | Taishan200(Model 2280), 2288H V5 or equivalent servers (see the community compatibility list for details). For x86_64 servers, you can choose one of icelake/cooperlake/cascade, preferably icelake. |
| RAID Card     | group raid is required, at least group raid 0                |
| NIC/IB Card   | The server and the test end need to insert a board of the same type respectively, configure the IP of the same network segment, and ensure direct connection and intercommunication. |
| FC Card       | Magnetic array needs to be connected, at least two luns      |

**Note**

If you want to test external drivers, install the drivers in advance and configure the test environment. 

GPU, VGPU, keycard and other test items need to install external drivers in advance to ensure that the environment deployment is completed, and then use this tool for testing. 

### Operating environment networking

![test-network](docs/pictures/test-network.png)

# Offline Installation Environment Deployment Requirements

1. Download openEuler's official everything iso and mount the local repo source. 

   If you cannot find a dependent package in everything iso, download the package manually from the openEuler repo and upload it to the tester for installation.

2. Root different test items, configure offline test dependencies 

   | Test item | filename                                                     | path   |
   | --------- | ------------------------------------------------------------ | ------ |
   | GPU       | [https://github.com/wilicc/gpu-burn](https://gitee.com/link?target=https%3A%2F%2Fgithub.com%2Fwilicc%2Fgpu-burn) | `/opt` |
   |           | [https://github.com/NVIDIA/cuda-samples/archive/refs/heads/master.zip](https://gitee.com/link?target=https%3A%2F%2Fgithub.com%2FNVIDIA%2Fcuda-samples%2Farchive%2Frefs%2Fheads%2Fmaster.zip) | `/opt` |
   | VGPU      | NVIDIA vgpu client driver package                            | /root  |
   |           | Download the virtual machine image file with the corresponding version and architecture, taking openEuler 22.03LTS and x86_64 as an example：[https://repo.openeuler.org/openEuler-22.03-LTS/virtual_machine_img/x86_64/openEuler-22.03-LTS-x86_64.qcow2.xz](https://gitee.com/link?target=https%3A%2F%2Frepo.openeuler.org%2FopenEuler-22.03-LTS%2Fvirtual_machine_img%2Fx86_64%2FopenEuler-22.03-LTS-x86_64.qcow2.xz) | `/opt` |

# tool mounting

## prerequisite

This tool supports openEuler 20.03 (LTS) or higher. For details of supported operating system versions, please see file `oec-hardware/scripts/kernelrelease.json` .

## Get the installation package

Configure the everything and update repo sources of the corresponding versions in the openEuler official repo, and use `dnf` to get the package for installation.

## installation process

### client

1. Install client oec-hardware using `dnf` .

   ```
   dnf install oec-hardware
   ```

2. Enter `oech` command, it can run normally, it means that the installation is successful.

### server

1. Install server-side oec-hardware-server using `dnf` .

   ```
   dnf install oec-hardware-server
   ```

2. Start the service. This service provides web services through nginx service. By default, port 80 is used. External ports can be modified through nginx service configuration files. Please ensure that these ports are not occupied before starting. 

   ```
   systemctl start oech-server.service
   systemctl start nginx.service
   ```

3. Turn off firewall and SElinux. 

   ```
   systemctl stop firewalld
   iptables -F
   setenforce 0
   ```

# use guidance

## prerequisite

- The `/usr/share/oech/kernelrelease.json` file lists all currently supported system versions. Use the `uname -a` command to confirm whether the current system kernel version belongs to the supported version of the framework.
- By default, the framework scans all network cards. Before testing the network cards, please filter the tested network cards by yourself. The test port is required to be connected and the status is up. It is recommended not to use the service network interface for network card testing. 
-  `/usr/share/oech/lib/config/test_config.yaml ` is the configuration file template of hardware test items. `fc` , `raid` , `disk` , `ethernet` and `infiniband` need to be configured according to the actual environment before hardware test. Other hardware tests do not need to be configured. For network card test, if the IP address is automatically added by the tool, after the test is completed, for security reasons, the IP of the server needs to be manually deleted.

## using step

1. Launch the test framework on the client side. The client starts `oech` , selects the test category, `compatible` indicates compatibility, `virtualization` indicates virtualization, and fills in the category number, i.e., enter `1` to indicate the selected compatibility category.

   ```
   # oech
   Please select test category.
   No.   category
   1     compatible
   2     virtualization
   Please select test category No:1
   ```

2. Fill in configuration items `ID` , `URL` and `Server` ; `ID` is recommended to fill in the issue ID on gitee (note: `ID` cannot contain special characters); `URL` is recommended to fill in the product link; `Server` must be filled in as the server domain name or ip that the client can directly access, which is used to display the test report and the server for network testing. The default port number of server `nginx` is `80` . If the port is not modified after the server is installed, you only need to enter the service IP address of the server for the value `Compatibility Test Server` ; otherwise, you need to bring the port number, such as `172.167.145.2:90` .

   ```
   The openEuler Hardware Compatibility Test Suite
   Please provide your Compatibility Test ID:
   Please provide your Product URL:
   Please provide the Compatibility Test Server (Hostname or Ipaddr):
   ```

3. Enter the test kit selection interface. In the case selection interface, the framework will automatically scan the hardware and select the test suite available for testing in the current environment. Enter `edit` to enter the test suite selection interface.

   ```
   These tests are recommended to complete the compatibility test: 
   No. Run-Now?  status    Class         Device         driverName     driverVersion     chipModel           boardModel
   1     yes     NotRun    acpi                                                                              
   2     yes     NotRun    clock                                                                             
   3     yes     NotRun    cpufreq                                                                           
   4     yes     NotRun    disk                                                                              
   5     yes     NotRun    ethernet      enp3s0         hinic          2.3.2.17          Hi1822              SP580
   6     yes     NotRun    ethernet      enp4s0         hinic          2.3.2.17          Hi1822              SP580
   7     yes     NotRun    ethernet      enp125s0f0     hns3                             HNS GE/10GE/25GE    TM210/TM280
   8     yes     NotRun    ethernet      enp125s0f1     hns3                             HNS GE/10GE/25GE    TM210/TM280
   9     yes     NotRun    raid          0000:04:00.0   megaraid_sas   07.714.04.00-rc1  SAS3408             SR150-M
   10    yes     NotRun    gpu           0000:03:00.0   amdgpu                           Navi                Radeon PRO W6800
   11    yes     NotRun    ipmi                                                                              
   12    yes     NotRun    kabi                                                                              
   13    yes     NotRun    kdump                                                                             
   14    yes     NotRun    memory                                                                            
   15    yes     NotRun    perf                                                                              
   16    yes     NotRun    system                                                                            
   17    yes     NotRun    usb                                                                               
   18    yes     NotRun    watchdog                                                      
   Ready to begin testing? (run|edit|quit)
   ```

4. Select the test kit. `all|none` is used for `全选|全取消` respectively (the mandatory test item `system` cannot be cancelled, and the status of `system` will change to `Force` after repeated successful execution); the number number can be selected as the test set, and only one number can be selected at a time. After pressing the enter character, `no` changes to `yes` , indicating that the test set has been selected.

   ```
   Select tests to run:
   No. Run-Now?  status    Class         Device         driverName     driverVersion     chipModel           boardModel
   1     no      NotRun    acpi                                                                              
   2     no      NotRun    clock                                                                             
   3     no      NotRun    cpufreq                                                                           
   4     no      NotRun    disk                                                                              
   5     yes     NotRun    ethernet      enp3s0         hinic          2.3.2.17          Hi1822              SP580
   6     no      NotRun    ethernet      enp4s0         hinic          2.3.2.17          Hi1822              SP580
   7     no      NotRun    ethernet      enp125s0f0     hns3                             HNS GE/10GE/25GE    TM210/TM280
   8     no      NotRun    ethernet      enp125s0f1     hns3                             HNS GE/10GE/25GE    TM210/TM280
   9     yes     NotRun    raid          0000:04:00.0   megaraid_sas   07.714.04.00-rc1  SAS3408             SR150-M
   10    yes     NotRun    gpu           0000:03:00.0   amdgpu                           Navi                Radeon PRO W6800
   11    yes     NotRun    ipmi                                                                              
   12    yes     NotRun    kabi                                                                              
   13    yes     NotRun    kdump                                                                             
   14    yes     NotRun    memory                                                                            
   15    yes     NotRun    perf                                                                              
   16    yes     NotRun    system                                                                            
   17    yes     NotRun    usb                                                                               
   18    yes     NotRun    watchdog     
   Selection (<number>|all|none|quit|run):
   ```

5. Start testing. Enter `run` to start the test.

6. Upload test results. After the test is completed, you can upload the test results to the server for easy result display and log analysis. If the upload fails, check the network configuration and re-upload the test results. 

   ```
   ...
   -------------  Summary  -------------
   ethernet-enp3s0                  PASS
   system                           PASS
   Log saved to /usr/share/oech/logs/oech-20200228210118-TnvUJxFb50.tar succ.
   Do you want to submit last result? (y|n) y
   Uploading...
   Successfully uploaded result to server X.X.X.X.
   ```

# result acquisition

## view results

1. Open the server IP address in the browser, click the navigation bar `Results` interface, and find the corresponding test id to enter.

   ![results](docs/pictures/results.png)

2. Enter a single task page to see specific test results, including environmental information and execution results. 

   - `Summary` View all test results.

   -  `Devices` View all hardware device information.

   -  `Runtime` View test run times and total task execution logs.

   - `Attachment` Download Test Log Attachment.

   -  `Submit` means upload the results to Euler's official authentication server (currently not open).

      ![result-qemu](docs/pictures/result-qemu.png)

## results show

The Result column displays the test results, which can be either PASS or FAIL. If the result is FAIL, you can click the result directly to view the execution log, and check the case code according to the error report.

## Review of test results

If the tested hardware and complete machine need to be published to the openEuler compatibility list, please upload all the following test results to the relevant adaptation issue: 

- oec-hardware test log 

- html test report generated by oec-hardware-server 

- Compatibility manifest file 

  After oec-hardware is executed, compatibility information file `hw_compatibility.json` will be automatically generated for the hardware passing the test. Please refer to this file to fill in templates under templates directory, and then upload the filled template file.

  The whole machine adaptation needs to test at least one RAID card and one network card, and provide corresponding information. 

# Test item introduction

## Existing test items

### compatible

1. **system**

   - Check if this tool has been modified. 
   - Check if OS version and kernel version match. 
   - Check if the kernel is modified/infected. 
   - Check if selinux is enabled properly. 
   - Use the dmidecode tool to read hardware information. 

2. **cpufreq**

   - Test whether cpu runs at the same frequency as expected under different fm strategies. 
   - Test whether the time required for cpu to calculate exactly the same specification at different frequencies is inversely related to the frequency value. 

3. **clock**

   - Test time vectoricity, no backtracking. 
   - Test basic stability of RTC hardware clock. 

4. **memory**

   - Use the memtester tool for memory read and write testing. 
   - mmap all available system memory, trigger swap, 120s read and write test. 
   - Test hugetlb. 
   - Memory hot plug test. 

5. **network**

   - Use ethtool to get network card information and ifconfig to perform down/up tests on the network card. 

   - Use qperf to test ethernet tcp/udp latency and bandwidth, as well as http upload and download rates. 

   - Use perftest to test latency and bandwidth of infiniband(IB) or RoCE network protocols. 

     **Note**

     When testing the network bandwidth, please confirm in advance that the network card speed of the server is not lower than that of the client, and ensure that there is no other traffic interference on the test network. 

6. **disk**

   Sequential/random read-write testing of bare disks/file systems using fio tools. 

7. **kdump**

   Trigger kdump to test whether the vmcore file can be generated and parsed normally. 

8. **watchdog**

   Trigger watchdog to test whether the system can be reset normally. 

9. **perf**

   - Collect events generated by hardware in the system. 
   - Collect sampling information and view statistical results. 

10. **cdrom**

    Burn and read optical drives using mkisofs and cdrecord. 

11. **ipmi**

    Query IPMI information using ipmitool. 

12. **nvme**

    Use nvme-cli tool to format, read and write, query and test the disk. 

13. **usb**

    Plug and unplug usb devices and test whether usb interfaces can be recognized normally. 

14. **acpi**

    Use the acpidump tool to read the data. 

15. **FC**

    Sequential/random read-write testing of FC storage servers using fio tools. 

16. **RAID**

    Use fio tool for sequential/random read/write test of hard disk under RAID. 

17. **keycard**

    Test whether the encryption card can be used normally. 

18. **GPU**

    - NVIDIA GPU

      - Stress test GPU using gpu_burn tool. 
      - Use cuda_samples to test basic GPU functionality. 

    - AMD GPU

      - Use the radeontop tool to view GPU usage. 

      - Use the glmark2 tool to view GPU screen information. 

      - Stress testing GPU using glmark2 tool. 

        **Note**

        AMD GPU testing relies on a graphical interface, which needs to be deployed and switched to before testing. 

19. **infiniband**

    - Use ethtool to get network card information. 

    - Use perftest to test the latency and bandwidth of the infiniband(IB) network protocol. 

      **Note**

      When testing the network bandwidth, please confirm in advance that the network card speed of the server is not lower than that of the client, and ensure that there is no other traffic interference on the test network. 

20. **kabi**

    - Test whether the kernel kabi has changed compared to the standard system. 

21. **VGPU**

    - Test NVIDIA VGPU server-side basics. 
    - Deploy NVIDIA VGPU client virtual machines, test driver installation, test client VGPU functionality. 
    - The VGPU server monitors the operation of the client. 

22. **spdk**

    - Sequential and random read and write testing of SSDs using the spdk tool. 

23. **dpdk**

    - Use dpdk-testpmd to connect two Ethernet ports in loopback mode. In the absence of an external traffic generator, the client uses Tx-only mode as the packet source, and the server uses Rx-only mode as the packet receiver to test the port transmission rate function. 

### virtualization

```
Virtualization has use cases waiting for updates.
```

# Community Developer Involvement Presentations

## environment deployment

1. Fork oec-hardware source code repository to personal space; 

2. clone repository source code; 

   ```
   git clone https://gitee.com/${gitee_id}/oec-hardware.git
   ```

3. Enter the corresponding directory, compile and install; 

   ```
   cd oec-hardware
   make && make install
   ```

4. Package verification, here take version 1.0.0 as an example for packaging, the specific packaging version please refer to the version in the spec file. 

   ```
   dnf install -y rpm-build 
   cd oec-hardware
   tar jcvf oec-hardware-1.0.0.tar.bz2 *
   mkdir -p /root/rpmbuild/SOURCES
   cp oec-hardware-1.0.0.tar.bz2 /root/rpmbuild/SOURCES/
   rpmbuild -ba oec-hardware.spec
   ```

## New test item

1. If there is already a category of test items in the directory `tests/` , add test items directly under the category. The directory name of the test items should be the same as the name of the following entry function. For example, the entry file of acpi test items is acpi.py file, and inherit the framework `Test` to implement your own test class. Otherwise, add category catalog first, and then add test items under category.
2. Important member variables or functions in the test class: 
   -  Function `test` -Required to test the main flow.
   - Function `setup` -environment preparation before test, mainly used to initialize the relevant information of the tested equipment, you can refer to network test.
   - Function `teardown` -environment cleaning after test is completed, mainly used to ensure that the environment can be restored correctly regardless of test success or failure, you can refer to network test.
   - Variable `requirements` -stores the rpm package names that the test depends on as an array, and the framework is automatically installed before the test starts.
   - Variables `reboot` and `rebootup` -If `reboot = True` indicates that the test suite/test case will restart the system and continue to execute the function specified by `rebootup` after restart, refer to kdump test.
3. Add identification display of corresponding test item in `hwcompatible/compatibility.py` file. Refer to https://gitee.com/openeuler/oec-hardware/blob/master/docs/develop_doc/get_board.md for card identification method.

# FAQ

 Kunpeng Xiaozhi provides solutions to problems that may be encountered during oec-hardware testing, and users can retrieve solutions to problems. In addition, the Kunpeng Forum provides complete oec-hardware installation and use questions, and users can obtain solutions according to scenarios.

If you encounter problems in the adaptation process, it is recommended that users first obtain support through Kunpeng Xiaozhi or Kunpeng Forum. 

If Kunpeng Xiaozhi can't solve it, you can submit issue feedback under this repository or send an email to openEuler Community Compatibility SIG Group Email: oecompatibility@openeuler.org