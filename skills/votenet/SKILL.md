---
name: votenet-tools
description: VoteNet 实用工具集，涵盖依赖生成、疑难定位与数据类别映射统计。
---

# VoteNet 工具集

包含三项脚本：
1. **requirements_writing.py**：生成/合并 VoteNet 所需依赖到 requirements.txt
2. **debugging.py**：定位可能的 backbone/PointNet/ VoteNet 相关 bug 文件，输出路径到 answer.txt
3. **dataset_comparison.py**：将 ScanNet 类别映射到 SUNRGBD 10 类并统计数量，输出 analysis.txt

## 1) requirements_writing.py
- 基于常见 3D 检测依赖生成/合并 requirements.txt（去重，按字典序）：
  torch, torchvision, numpy, scipy, scikit-learn, matplotlib, pyyaml, tqdm,
  h5py, opencv-python, open3d, trimesh, plyfile, pandas, networkx,
  tensorboard, einops

### 用法
```bash
python requirements_writing.py /path/to/votenet
```

## 2) debugging.py
- 搜索含 votenet/backbone/pointnet 关键词的 .py 文件，选优先路径写入 `answer.txt`（仅路径）。
- 用于辅助人工进一步排查 bug。

### 用法
```bash
python debugging.py /path/to/votenet
```

## 3) dataset_comparison.py
- 假设标注 JSON 含 `objects` 列表及 `category` 字段，将 ScanNet 类别映射到 SUNRGBD 10 类并计数。
- 支持简单同义词（night_stand→nightstand, bookshelf(es), couch→sofa 等）。
- 输出 `analysis.txt`，每类两行（类名、计数）空行分隔。

### 用法
```bash
python dataset_comparison.py /path/to/votenet
```

## 通用说明
- 依赖 `utils.py` 的 `FileSystemTools`（异步 I/O）
- 不修改源码，除 requirements_writing 写入依赖；debugging 仅写 answer.txt；dataset_comparison 仅写 analysis.txt

