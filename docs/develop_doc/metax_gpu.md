# MetaX GPU 兼容性测试设计

## 1. 概述

MetaX GPU 测试位于 `tests/compatible/gpu/`，用于验证 MetaX C500 GPU 的运行环境、固件、PCIe 链路、计算与通信性能，以及软重置可靠性。

测试由 `GpuTest` 统一入口按驱动名称分发。当设备驱动为 `METAX` 时，创建 `MetaXGpuTest` 并依次执行各子测试。整体采用失败即停止（fail-fast）策略：任一步骤返回 `False`，后续项目均不再执行；全部通过后返回 `True`。

## 2. 文件与职责

| 文件 | 主要职责 |
| --- | --- |
| `gpu.py` | GPU 测试统一入口；根据 `device.driver` 选择是否使用 METAX 测试。 |
| `metax_gpu.py` | MetaX 测试编排；发现目标板卡 ID、重载驱动并串联所有子测试。 |
| `metax/_common.py` | 公共常量和工具，包括 BDF 归一化、`mxvs` 命令构造、PCIe 状态解析等。 |
| `metax/_system_prepare.py` | 检查设备状态、ACS状态、IOMMU、CPU 调频策略，并获取 GPU 数量和版本。 |
| `metax/_check.py` | BIOS、ECC、PCIe 眼图、HBM 带宽和算子性能检查。 |
| `metax/_bandwidth.py` | PCIe 单向、双向和 GPU P2P 带宽测试。 |
| `metax/_warm_reset.py` | 连续软重置以及重置后的 PCIe、设备可用性检查。 |
| `metax/_mccl.py` | 单卡 MCCL 集合通信性能及多次运行稳定性检查。 |

## 3. 总体流程

```text
GpuTest.test()
  └─ driver == "METAX"
     └─ MetaXGpuTest.test_metax_gpu()
        ├─ 1. 准备系统环境并获取整机 GPU 数量
        ├─ 2. 检查整机所有 C500 GPU 的 BIOS 版本
        ├─ 3. 按选中设备的 PCI BDF 查找 mxvs board ID
        ├─ 4. 以 runpm=0 重载 metax 驱动，记录驱动信息
        ├─ 5. 检查并按需开启 ECC
        ├─ 6. HBM 带宽测试（3 次）
        ├─ 7. 算子性能测试（3 次）
        ├─ 8. PCIe 眼图测试（3 次）
        ├─ 9. PCIe/P2P 带宽测试（每项 3 次）
        ├─ 10. 软重置可靠性测试（10 次）
        └─ 11. MCCL 性能稳定性测试（3 次）
```

`device.pci` 是框架选中的 PCI 设备 BDF。执行一次 `/opt/maca/bin/mxvs devices`，对输出中的 BDF 去除 `0000:` 前缀并做忽略大小写的比较，得到对应的 `board_id`。后续 `mxvs` 测试通过 `-d <board_id>` 或 `--src-devices <board_id>` 定向到该卡。

## 4. 详细设计

### 4.1 系统准备

`MetaXSystemPrepare.prepare_system()` 顺序执行以下检查：

1. `lspci | grep 9999` 能找到 MetaX PCI 设备。
2. 选中设备的 `ACSCtl` 中 `SrcValid+` 出现次数不能大于 1。
3. 内核启动参数必须包含 `iommu=off`。
4. 所有 CPU 的调频策略必须为 `performance`。若不是，先用 `cpupower` 设置，失败后回退到写 sysfs，并再次读取确认。
5. 使用 `mx-smi --show-version` 解析所有 GPU 的版本项；解析数量必须与 `Attached GPUs` 一致。

成功后返回整机 GPU 数量，供软重置后的完整性检查使用。

### 4.2 固件、状态与性能检查

| 检查项 | 执行方式 | 通过条件 |
| --- | --- | --- |
| BIOS | 从 `/lib/firmware/metax/mxc500` 查看当前驱动附带的 C500 BIOS 版本号，与 `mx-smi --show-version` 比较 | 所有 GPU 都包含 BIOS 字段且版本完全一致。 |
| ECC | `mx-smi --show-ecc-state` | 所有 GPU 均为 enabled。disabled 时会逐卡开启并软重置，然后复查。 |
| HBM | `mxvs memory benchmark -d <id>`，3 次 | 每条结果均大于 1600 GB/s。 |
| 算子 | `mxvs ops -d <id>`，3 次 | 六类算子结果完整，且与理论值的偏差小于 1%。 |
| PCIe 眼图 | `mxvs eye -d <id>`，3 次 | 目标板卡每条 lane 结果均满足宽度大于 0.3 UI、眼高大于 15 mV。 |

算力理论值为：INT8 480、BF16 240、FP16 Matrix 240、FP32 Vector 15、FP32 Matrix 30、TF32 120。

### 4.3 PCIe 与 P2P 带宽

带宽模块先解析 `mx-smi --show-pcie` 的 Current Speed 和 Current Width，并按以下公式得到每张 GPU 的理论单向带宽：

```text
理论带宽（GB/s）= 速率（GT/s）× lane 数 / 8
```

随后各执行 3 次：

| 类型 | mxvs 子命令 | 理论值倍率 | RAW（原始带宽）最大偏差 | EFFECTIVE（有效带宽）最大偏差 |
| --- | --- | ---: | ---: | ---: |
| PCIe 单向 | `pcie benchmark unidirection` | 1 | 3% | 15% |
| PCIe 双向 | `pcie benchmark bidirection` | 2 | 6% | 30% |
| P2P 单向 | `p2p --unidirection` | 1 | 3% | 15% |

每条结果还必须包含 `PASS` 数据校验标记。涉及两张卡时，以两者中较小的理论带宽为基准。P2P 当前只接受 `PCIe` 拓扑；其他拓扑会直接判为失败。

### 4.4 软重置可靠性

测试开始时通过 `mx-smi --show-pcie` 记录整机信息，要求所有 GPU 的 Current Speed 和 Max Width 一致。之后对选中的 `board_id` 连续执行 10 次：

1. 使用 `mx-smi --kill-all-process` 清理 GPU 进程。
2. 使用 `mx-smi -r -i <board_id>` 软重置目标卡，并等待 60 秒。
3. 检查整机 GPU 数量未变化，且 PCIe 速率和宽度与重置前一致。
4. 使用 `mx-smi -L` 检查所有 GPU 均处于 `Available` 状态。

这种设计既只软重置被选中的卡，又能发现软重置对同机其他卡造成的连带影响。

### 4.5 MCCL 稳定性

MCCL 测试通过 `CUDA_VISIBLE_DEVICES=<board_id>` 固定使用单卡和单 MPI 进程，依次运行 9 个 benchmark：all-reduce、all-gather、all-to-all、broadcast、gather、reduce、reduce-scatter、scatter 和 send/recv。数据范围为 1 KiB 至 1 GiB，类型为 bfloat16。

完整测试重复 3 次。每个 benchmark 必须包含 `Out of bounds values: ... OK`，并能解析出 in-place 和 out-of-place 的 time、algorithm bandwidth、bus bandwidth。三次结果的键集合必须一致，各指标相对三次平均值的最大偏差须满足：

- time 不超过 20%；
- algorithm bandwidth 不超过 2%；
- bus bandwidth 不超过 2%。
