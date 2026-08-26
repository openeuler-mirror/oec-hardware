# Ascend NPU 兼容性测试设计

## 1. 概述

Ascend NPU 测试位于 `tests/compatible/ascend/`，用于验证 Ascend NPU 的运行环境、版本兼容性、健康状态、PCIe 传输带宽、算力，以及 Ascend C 编译工具链的编译与运行能力。目前暂时只支持 Atlas 300I A2。

测试由 `AscendTest` 统一入口编排。框架在 `compatibility.py` 中按 PCI ID 归类设备：任何 `PCI_ID` 命中 `ASCEND_PCI_IDS`（`19e5:d802`、`19e5:d803`）的设备都会被绑定到一个空设备并归入 `ascend` 用例，因此无论机器上有多少张卡，该测试只调度执行一次；测试内部通过 `lspci -nnk` 自行枚举全部 NPU 卡并逐卡测试。

Ascend 测试会完整执行所有子测试并收集结果，最后统一判断：任一项返回 `False`，整体返回 `False`；全部通过返回 `True`。

## 2. 文件与职责

| 文件 | 主要职责 |
| --- | --- |
| `ascend.py` | 测试入口与编排；包含版本检查、健康检查、带宽、算力、编译等子测试的实现类。 |
| `helper.py` | PCIe 理论带宽计算，按代际区分编码效率（Gen1/2 为 8b/10b，Gen3+ 为 128b/130b）。 |
| `map.py` | SoC 名称到 `bisheng --npu-arch` 的映射，以及各 SoC 各数据类型的理论算力规格表。 |
| `vector_add.asc` | 编译测试使用的 Ascend C 向量加示例源码。 |
| `Makefile` | 安装时将 `.py` 与 `.asc` 文件拷贝到目标目录。 |

## 3. 总体流程

```text
compatibility.py 设备归类（PCI_ID ∈ ASCEND_PCI_IDS → ascend 用例，仅调度一次）
  └─ AscendTest.test()
     ├─ 1. lspci -nnk 按 PCI ID 枚举全部 NPU 设备，并记录各卡驱动信息
     ├─ 2. 检查 CANN 环境（import acl，获取 SoC 名称）
     ├─ 3. 检查 Ascend toolbox（ascend-dmi -v）
     ├─ 4. 版本兼容性检查（ascend-dmi -c）
     ├─ 5. 对每张卡（按枚举序号）：
     │     ├─ 健康检查（cann/device/driver/hbm 诊断）
     │     ├─ PCIe 传输带宽测试（h2d/d2h × 3 种数据量）
     │     └─ 算力测试（5 种数据类型）
     ├─ 6. 编译与运行测试（仅一次）
     └─ 7. 汇总全部结果，任一失败则整体失败
```

所有依赖 CANN/toolbox 工具链的命令（`ascend-dmi`、`bisheng` 等）都由 `_AscendCommandRunner` 统一封装：先 `source /usr/local/Ascend/cann/set_env.sh && source /usr/local/Ascend/toolbox/set_env.sh`，再通过 `bash -c` 执行。

## 4. 详细设计

### 4.1 设备枚举与调度

测试不依赖框架传入的 `device.pci`，而是执行 `lspci -nnk`，用正则提取 `bus:device.function` 形式的 BDF（不含域前缀），凡是同一行包含任一 `ASCEND_PCI_IDS` 的即视为 NPU 设备。枚举失败（无任何设备）直接判失败。

健康检查、带宽和算力子测试中的设备编号使用枚举序号（0、1、2…），即 `ascend-dmi` 的逻辑设备号，而非 PCI BDF。BDF 仅用于通过 `lspci -vvs` 读取 PCIe 链路信息。

### 4.2 环境检查

| 检查项 | 执行方式 | 通过条件 |
| --- | --- | --- |
| CANN | `source cann/set_env.sh` 后执行 `python3 -c "import acl;print(acl.get_soc_name())"` | 命令成功且 SoC 名称非空；记录 `soc_name` 供算力比对和编译测试使用。 |
| toolbox | `ascend-dmi -v` | 命令成功，记录版本信息。 |

### 4.3 版本兼容性检查

`AscendVersion.version_check()` 执行 `ascend-dmi -c --fmt json`，对返回的 JSON 递归遍历，收集所有包含 `status` 字段的节点（附带完整 JSON 路径）。通过条件：

1. 至少解析出一个 `status` 节点；
2. 所有节点的 `status` 均为 `OK`。

非 `OK` 节点会连同其 JSON 路径一起记录到日志。

### 4.4 健康检查

对每张卡执行 `ascend-dmi -dg -i <item> -d <index>`，按 `<item>:\n    <status>` 的缩进格式解析结果：

| 检查项 | 参数 | 期望结果 |
| --- | --- | --- |
| cann | `-i cann -p /usr/local/Ascend` | `PASS` |
| device | `-i device` | `HEALTH` |
| driver | `-i driver` | `HEALTH` |
| hbm | `-i hbm` | `PASS` |

四项全部符合期望值该卡健康检查才通过。

### 4.5 PCIe 传输带宽

带宽测试前先通过 `lspci -vvs <pci>` 解析 `LnkSta` 得到协商的速率（GT/s）和链路宽度，理论单向带宽按以下公式计算：

```text
理论带宽（GB/s）= 速率（GT/s）× 编码效率 × lane 数 / 8
```

编码效率按代际取值：PCIe 1.x/2.x 为 8b/10b（0.8），PCIe 3.x 及以上为 128b/130b。速率无法匹配已知代际或 lane 数非法时直接报错。

随后对每个方向（`h2d`、`d2h`）× 每种数据量执行 `ascend-dmi --bw -t <方向> -d <index> --et 100 -s <数据量> -q --fmt json`，从 `bandwidths[0].results[0].bandwidth` 解析实测带宽（GB/s），共 6 组。实测带宽相对理论值的偏差 `(理论 - 实测) / 理论` 须满足：

| 数据量 | 最大允许偏差 |
| --- | ---: |
| 512 KB | 30% |
| 2 MB | 20% |
| 512 MB | 10% |

链路速率或宽度缺失时该组测试直接判失败。

### 4.6 算力检查

对每张卡、每种数据类型执行 `ascend-dmi -f -q -d <index> -t <dtype> --et 60 --fmt json`，数据类型为 fp16、bf16、fp32、hf32、int8，结果分别从 `computing_power.tflops_<dtype>`（int8 为 `tops_int8`）解析。

实测值与 `map.py` 中 `THEORETICAL_SPECS` 的理论值比对，SoC 名称按前缀匹配。当前已内置 Atlas 300I A2 系列：

| 数据类型 | 理论算力 |
| --- | ---: |
| fp16 | 280 TFLOPS |
| bf16 | 280 TFLOPS |
| fp32 | 75 TFLOPS |
| hf32 | 140 TFLOPS |
| int8 | 560 TOPS |

相对偏差不得超过 5%。若 `soc_name` 在规格表中没有匹配项，仅记录警告并跳过比对，该数据类型视为通过。

### 4.7 编译与运行测试

编译测试在所有卡测完后执行一次，验证 Ascend C 工具链可用：

1. 根据 `soc_name` 在 `NPU_ARCH_MAP` 中查找 `bisheng --npu-arch` 目标（Atlas 300I A2 映射为 `dav-2201`），无映射直接判失败。
2. 在 `/tmp` 下创建临时目录，将 `vector_add.asc` 拷贝进去。
3. 使用 `bisheng vector_add.asc --npu-arch=<arch> -o vector_add` 编译，编译失败即判失败。
4. 运行生成的二进制，输出必须包含 `[Success] Case accuracy is verification passed`，确认向量加计算结果校验通过。
5. 无论成败都清理临时目录。
