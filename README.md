# oec-hardware

## 背景介绍
oec-hardware工具是openEuler社区提供的一款硬件兼容性测试工具，oec-hardware提供服务器整机、板卡与openEuler的兼容性验证测试，验证仅限于基本功能验证，不包括性能测试等其它测试。

硬件厂商在需要验证硬件产品与openEuler的兼容性时，可以使用oec-hardware。社区提供硬件兼容性测试流程，硬件厂商可以参考 [社区兼容性适配流程](https://www.openeuler.org/zh/compatibility/hardware/) 进行和openEuler的适配。

通过oec-hardware工具测试的硬件产品，openEuler会在社区官网发布 [兼容性清单](https://www.openeuler.org/zh/compatibility/) ，硬件厂商会在厂商官网发布对应的兼容性信息。

## 安装测试框架

### 前提条件

本工具支持在 openEuler 20.03 (LTS) 或更高版本上运行，详细支持操作系统版本信息请查看 oec-hardware/scripts/kernelrelease.json 文件。

### 获取安装包

配置 [openEuler 官方 repo](https://repo.openeuler.org/) 中对应版本的 everything  和 update repo源，使用 `dnf` 获取软件包进行安装。

### 安装过程

#### 客户端

1. 使用 `dnf` 安装客户端 oec-hardware。

   ```
   dnf install oec-hardware
   ```

2. 输入 `oech` 命令，可正常运行，则表示安装成功。

#### 服务端

1. 使用 `dnf` 安装服务端 oec-hardware-server。

   ```
   dnf install oec-hardware-server
   ```

2. 启动服务。本服务通过搭配 nginx 服务提供 web 服务，默认使用 80 端口，可以通过 nginx 服务配置文件修改对外端口，启动前请保证这些端口未被占用。

   ```
   systemctl start oech-server.service
   systemctl start nginx.service
   ```

3. 关闭防火墙和 SElinux。

   ```
   systemctl stop firewalld
   iptables -F
   setenforce 0
   ```

## 使用说明

1. 在客户端启动测试框架。在客户端启动 `oech`，填写`ID`、`URL`、`Server`配置项，`ID` 建议填写 gitee 上的 issue ID（注意：`ID`中不能带特殊字符）；`URL`建议填写产品链接；`Server` 必须填写为客户端可以直接访问的服务器域名或 ip，用于展示测试报告和作网络测试的服务端。服务端`nginx`默认端口号是`80`，如果服务端安装完成后没有修改该端口，`Compatibility Test Server` 的值只需要输入服务端的业务IP地址；否则需要带上端口号，比如：`172.167.145.2:90`。

   ```
   # oech
   The openEuler Hardware Compatibility Test Suite
   Please provide your Compatibility Test ID:
   Please provide your Product URL:
   Please provide the Compatibility Test Server (Hostname or Ipaddr):
   ```

2. 进入测试套选择界面。在用例选择界面，框架将自动扫描硬件并选取当前环境可供测试的测试套，输入 `edit` 可以进入测试套选择界面。

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
   9     yes     NotRun    ipmi                                                                              
   10    yes     NotRun    kabi                                                                              
   11    yes     NotRun    kdump                                                                             
   12    yes     NotRun    memory                                                                            
   13    yes     NotRun    perf                                                                              
   14    yes     NotRun    system                                                                            
   15    yes     NotRun    usb                                                                               
   16    yes     NotRun    watchdog                                                      
   Ready to begin testing? (run|edit|quit)
   ```

3. 选择测试套。`all|none` 分别用于 `全选|全取消`（必测项 `system` 不可取消，多次执行成功后 `system` 的状态会变为`Force`）；数字编号可选择测试套，每次只能选择一个数字，按回车符之后 `no` 变为 `yes`，表示已选择该测试套。

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
   9     no      NotRun    ipmi                                                                              
   10    no      NotRun    kabi                                                                              
   11    no      NotRun    kdump                                                                             
   12    no      NotRun    memory                                                                            
   13    no      NotRun    perf                                                                              
   14    yes     NotRun    system                                                                            
   15    no      NotRun    usb                                                                               
   16    no      NotRun    watchdog     
   Selection (<number>|all|none|quit|run):
   ```

4. 开始测试。选择完成后输入 `run` 开始测试。

5. 上传测试结果。测试完成后可以上传测试结果到服务器，便于结果展示和日志分析。如果上传失败，请检查网络配置，然后重新上传测试结果。

   ```
   ...
   -------------  Summary  -------------
   ethernet-enp3s0                  PASS
   system                           FAIL
   Log saved to /usr/share/oech/logs/oech-20200228210118-TnvUJxFb50.tar succ.
   Do you want to submit last result? (y|n) y
   Uploading...
   Successfully uploaded result to server X.X.X.X.
   ```
   
## 查看结果

### 如何查看

1. 浏览器打开服务端 IP 地址，点击导航栏 `Results` 界面，找到对应的测试 id 进入。


2. 进入单个任务页可以看到具体的测试结果展示，包括环境信息和执行结果等。

   - `Submit` 表示将结果上传到欧拉官方认证服务器（**当前尚未开放**）。

   - `Devices` 查看所有测试设备信息。

   - `Runtime` 查看测试运行日志。

   - `Attachment` 下载测试附件


### 结果说明&建议

在 **Result** 列展示测试结果，结果有两种：**PASS** 或者 **FAIL**。如果结果为**FAIL**，可以直接点击结果来查看执行日志，根据报错对照用例代码进行排查。

