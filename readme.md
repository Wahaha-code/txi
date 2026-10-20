# Retinex 与 TXI 图像增强

本仓库保留原有 Retinex 算法，并增加了基于 Sato 等人论文的 TXI 图像增强实现。

## Conda 环境

```bash
conda env create -f environment.yml
conda activate retinex-txi
```

已创建环境时更新依赖：`conda env update -f environment.yml --prune`。

## 处理一张图像

```bash
python txi.py /path/to/image.png
```

默认在输入图像旁生成 `image_txi_mode1.png` 和 `image_txi_mode2.png`。mode 2 增强暗部和纹理，色调更接近原图；mode 1 在此基础上增强红色与浅色的对比。仅生成一种模式并指定路径：

```bash
python txi.py /path/to/image.png --mode 1 --output /path/to/enhanced.png
```

对于 PitVis 手术视频，可显式选用调参版：

```bash
python txi.py /path/to/frame.png --preset pitvis
```

调参版输出文件名包含 `_txi_pitvis_`，不会覆盖默认版。它提高暗部和纹理增益，并扩展 mode 1 的红浅色映射范围；这是针对当前样本的探索性设置，**不是论文报告的参数，也没有临床验证**。

也可通过 Python 调用：

```python
import cv2
from code.txi import enhance_txi

image = cv2.imread("input.png")
mode1, mode2 = enhance_txi(image)
cv2.imwrite("output.png", mode1)
```

支持常见 8 位或 16 位灰度、RGB、RGBA 图像。16 位输入输出为 8 位 PNG；PNG 的透明通道会保留。输入文件名含中文也可以使用。输出用于图像观察和研究，不应仅凭增强图像作临床诊断。

## PitVis 原始视频测试帧

`data/pitvis_unlabeled/` 最初保存了从 PitVis 原始 `video_23.mp4` 等间距提取的 10 张无标注 PNG；目前其中 1 张已不在目录，实际留存 9 张。`manifest.csv` 记录最初提取的帧号和时间戳。该目录中的 `README.md` 记录数据来源及许可。提取脚本可用于其他 PitVis 视频：

原始视频、帧图和增强结果仅保留在本地，不纳入代码仓库；从仓库克隆后请按该目录 `README.md` 的命令重新提取。

```bash
python scripts/extract_pitvis_frames.py /path/to/video_23.mp4 data/pitvis_unlabeled
```

例如，处理其中一帧：

```bash
python txi.py data/pitvis_unlabeled/video_23_frame_004529.png
```

批量处理当前保留的测试帧，并生成 mode 1、mode 2 及对照图：

```bash
python scripts/test_txi_frames.py data/pitvis_unlabeled data/pitvis_txi_results
```

PitVis 调参版九帧结果：

```bash
python scripts/test_txi_frames.py data/pitvis_unlabeled data/pitvis_txi_tuned --preset pitvis
```

## 实现与论文的对应关系

TXI 模块位于 `code/txi.py`，依次执行六步：

1. 用双边滤波近似论文中的边缘保留滤波，将图像分为基底层与细节层；把近白色反光像素并入基底层。
2. 根据论文公式 (7)–(9) 仅提高暗部基底亮度，RGB 三通道使用同一增益以保持色比。
3. 对基底层应用色调曲线；已处理照片默认使用恒等映射。
4. 按公式 (11) 对细节层施加默认 1.2 倍纹理增益。
5. 按公式 (12) 重组，得到 TXI mode 2。
6. 在 CIE Lab 的 `a*` 通道使用论文给出的 `(0,0) → (15,5) → (30,30)` 折线，得到 TXI mode 1。

论文没有给出双边滤波的具体参数、反光检测规则以及内镜设备的色调曲线。本实现提供可用的默认值，但不宣称与 Olympus 商用 TXI 像素一致。可通过 `--spatial-sigma`、`--range-sigma`、`--tone-gamma` 调整常见输入；其他参数见 `TXIConfig`。

论文默认参数针对动物胃肠内镜图像；PitVis 经鼻垂体手术视频的亮度和色彩分布不同。九帧测试中，默认暗部阈值平均只覆盖约 12% 的可见画面，因此默认版变化较小。`PITVIS_CONFIG` 是单独保留的探索性调参版，使用更宽的暗部阈值、纹理增益与 Lab `a*` 映射范围。

## 原有 Retinex 示例

```bash
python demo.py
```

原有算法及说明见 `code/retinex.py`。

## 参考文献

- Sato et al., *TXI: Texture and Color Enhancement Imaging for Endoscopic Image Enhancement*, Journal of Healthcare Engineering, 2021. https://pmc.ncbi.nlm.nih.gov/articles/PMC8049784/
- Petro et al., *Multiscale Retinex*, Image Processing On Line, 2014. https://doi.org/10.5201/ipol.2014.107
