---
name: threestudio-tools
description: 实用工具集，用于 ThreeStudio 代码库的依赖修复、文件定位与输出结构分析。
---

# ThreeStudio 工具集

包含三项脚本：
1. **requirements_completion.py**：补全 Zero123 相关依赖到 requirements.txt
2. **code_locating.py**：定位 Zero123 guidance 实现文件，输出路径到 answer.txt
3. **output_analysis.py**：分析 zero123.py 中 guidance_out 的结构，写入 answer.txt

## 1) requirements_completion.py
- 搜索项目内 requirements.txt
- 将 Zero123 常用依赖（einops、k-diffusion、transformers、diffusers、omegaconf、pytorch-lightning、open-clip-torch、trimesh、imageio[ffmpeg]）追加到文件末尾，避免重复

### 用法
```bash
python requirements_completion.py /path/to/threestudio
```

## 2) code_locating.py
- 搜索包含 “zero123” 且路径含 “guidance” 的 .py 文件
- 优先选择 `threestudio/models/guidance/zero123*.py`
- 将相对路径写入项目根的 `answer.txt`

### 用法
```bash
python code_locating.py /path/to/threestudio
```

## 3) output_analysis.py
- 读取 `threestudio/systems/zero123.py`（或搜索 zero123.py）
- 定位 guidance_out 赋值行附近，若为字典则提取键；否则输出片段
- 写入 `answer.txt`（含结构或片段，以及文件相对路径）

### 用法
```bash
python output_analysis.py /path/to/threestudio
```

## 通用说明
- 依赖 `utils.py` 中的 `FileSystemTools`（异步 I/O）
- 不修改源码内容，除 requirements_completion 写回依赖
- 输出文件均写到项目根目录（answer.txt 或修改 requirements.txt）

