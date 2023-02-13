# openEuler驱动开发规范

## 目的

为规范和统一 openEuler 驱动开发的提交流程及方式，使驱动在 openEuler上使能，特制定 openEuler 驱动开发规范。

## 适用范围

openEuler 驱动开发规范适用于 openEuler 在开发以及已发布的所有版本的开发过程。

## 前提

### 签署贡献者协议 （CLA)

贡献者贡献openEuler社区前，需签署贡献者协议[CLA](https://openeuler.org/zh/community/contribution/)。

>**说明** ：CLA签署后大约需要一周时间生效。

### 驱动要求

### 必须满足以下要求

驱动需满足如下要求：

1. 名称不能与系统已有名称发生冲突。
Linux lsmod命令用于显示已经加载到内核中的模块的状态信息。执行lsmod命令后会列出所有已载入系统的模块。lsmod命令查询出的结果仅供参考，新开发的驱动命名不应与上游社区的驱动重名。
建议查看/lib/modules/xx 下面的Modules信息，避免与系统中所有已存在的模块发生冲突。
2. 驱动命名要有意义。
命名要结合驱动的作用或者来源来命名，不能随便用字母的排列组合来命名驱动。
例如某网卡使用的驱动hinic，某RAID卡使用的驱动megaraid_sas，某GPU使用的驱动nvidia。
3. 对照openEuler社区KABI检测。
KABI是Kernel Application Binary Interface的缩写。
KABI主要用于校验插入的ko等模块是否与当前内核版本兼容。内核ko都会用到内核提供的ABI接口（且地址是固定的），通过校验ko对应的ABI接口地址与当前内核版本提供的ABI对应接口地址是否一致，即可判断ko是否与当前版本兼容。
内核ko使用的KABI接口可以通过modprobe --dump xxx.ko查看（在ko文件目录下使用） 。
4. 正确的驱动版本信息。
系统中用命令读出来的驱动版本信息要和说明文档中的驱动版本信息以及驱动软件包中的驱动版本信息一致。
例如igb驱动
modinfo igb|grep version   查看驱动版本信息
查出来的版本信息要和驱动的软件包名称一致
5. 驱动模块参数需要解释说明。
解释说明参数的使用方法、功能、原理等。
6. 声明 license 信息。
License：许可证，是供应商与客户对所销售/购买的产品（这里特指软件版本）使用范围、期限等进行授权/被授权的一种合约形式，通过License，客户获得供应商所承诺的相应服务。物理形式表现为License授权证书和License文件。
7. 代码要符合社区的编码规范。
不符合编码规范的代码无法通过社区的代码检测。
8. 声明驱动的来源。
驱动是自己开发的或者是从开源网站上面下载直接使用的要做出说明。
9. 驱动的modinfo信息要包含适配的卡类型的标识，网卡、RAID卡、GPU等等。

### 可选

1. 建议增加驱动与操作系统发行版耦合方式的规范，比如直接检查 /etc/openEuler-release 文件或者其它作为技术路线的判断，不再与具体的发行版信息耦合。
驱动的版本不在与openEuler具体的版本绑定，比如驱动在openEuler-20.03-LTS-SP3上可以正常安装， 在openEuler-22.03-LTS上无法正常安装，驱动可以尽可能的与不同的版本兼容。
2. 有配套的工具建议一并提供。
例如RAID卡驱动，有没有配套的做RAID的工具，如果有对应的工具，建议提供对应的工具与使用手册。
3. outbox驱动建议做成rpm类型（包含说明文档）。
4. 模块作者等信息。

## 驱动持续演进管理
1. 能否维护驱动
驱动来源，驱动提供人，驱动升级，解决驱动使用过程中产生的问题，驱动硬件适配。
2. 能否持续管理
不同版本的驱动维护、长期对驱动持续管理，维护周期至少是一个LTS系统的生命周期，LTS通常两年发布一个新版本。


## 参考资料

- [Kernel SIG | openEuler Kernel 补丁合入规范](https://mp.weixin.qq.com/s/rSH79v7btJfsdivC2mki1w)
- [如何参与 openEuler 内核开发](https://mp.weixin.qq.com/s/a42a5VfayFeJgWitqbI8Qw)
