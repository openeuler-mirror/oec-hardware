# SoC name -> bisheng --npu-arch value.
# acl.get_soc_name() may carry a variant suffix (e.g. "Ascend910B4-1"),
# so each known variant is listed explicitly.
NPU_ARCH_MAP = {
    "Ascend910B4": "dav-2201",
    "Ascend910B4-1": "dav-2201",
}

# Theoretical peak computing power (T) per SoC name and data type.
# Keys are matched as prefixes of the acl.get_soc_name() output.
THEORETICAL_SPECS = {
    "Ascend910B4": {
        # Source: Atlas 800I A2 official spec (FP16 280T, FP32 75T,
        # INT8 560T); BF16 equals FP16 on Da Vinci; HF32 is half of
        # FP16 (Cube unit rate).
        "fp16": 280.0,
        "bf16": 280.0,
        "fp32": 75.0,
        "hf32": 140.0,
        "int8": 560.0,
    },
}
