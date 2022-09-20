# oec-hardware软件包发布设计文档

## 版本发布策略

oec-hardware 工具的软件包会发布在支持的openEuler操作系统版本repo源里，用户在安装工具支持的 openEuler 操作系统后，可以直接从 everything 或 update repo 源里获取工具软件包。

在版本停止维护之前，兼容性sig组会同步更新每个版本下的工具。

## 版本发布管理方案

1. 稳定版本管理

oec-hardware 工具和版本是解耦的，为了保证稳定版本发布，源码会通过标签的方式发布稳定版；后续如果工具和版本耦合，会在源码仓库下拉取对应的版本分支。

注：如果要使用开发版本，请直接下载 oec-hardware 源码编译安装使用。

2. 版本号管理

    2.1 openEuler/oec-hardware

    源码仓库里的版本号通过 Version 进行管理。在新增功能特性后，工具的版本号+1，并在SPEC中增加 changelog 说明，Version 演进说明如下：

        Version: X.Y.Z

        （1）X: 工具框架优化；

        （2）Y: 新增架构支持；

        （3）Z: 新增OS版本支持、测试项；

    版本号发生变化后，将在 master 分支打上对应版本的标签，发布该版本的 source 包，src-openEuler 仓库下的 oec-hardware 软件包会取用最新版本的 source 包进行发布。

    2.2 src-openEuler/oec-hardware

    软件包仓库里的 Version 版本跟随上游源码版本更新，如果发布的软件包存在issue，可以通过提交patch的方式对软件包进行维护，版本号通过 Release 进行管理，提交patch需要同步修改 Release 号，并在SPEC中增加 changelog 说明。在软件包发布后，patch需要回合到上游源码仓库。

3. 版本维护声明

    oec-hardware在发布新版本软件包后，会在工具的readme文档中显式声明从某个版本的工具不再进行更新维护。

4. 软件包更新发布周期

    （1）上游源码version更新后，及时更新发布；

    （2）上游源码version没有更新的情况下，定期（每三个月）更新维护。