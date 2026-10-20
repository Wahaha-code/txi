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

调参版输出文件名包含 `_txi_pitvis_`，不会覆盖默认版。它提高暗部覆盖范围，针对视频噪声限制纹理放大，并减弱圆形视野边界的处理；这是针对当前样本的探索性设置，**不是 Olympus 商用参数，也没有临床验证**。

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
python scripts/test_txi_frames.py data/pitvis_unlabeled data/pitvis_txi_optimized --preset pitvis
```

结果目录含 `comparison.png` 和 `results.csv`。CSV 记录暗部亮度变化、新增接近白色饱和像素比例、组织内部梯度变化以及平均像素变化。这些是无标注图像的工程指标，不能代替医生评价或证明病灶检出率提高。

## 实现与论文的对应关系

TXI 模块位于 `code/txi.py`，依次执行六步：

1. 用双边滤波近似论文中的边缘保留滤波，将图像分为基底层与细节层；把近白色反光像素并入基底层。
2. 根据论文公式 (7)–(9) 仅提高暗部基底亮度，RGB 三通道使用同一增益以保持色比。
3. 对基底层应用色调曲线；已处理照片默认使用恒等映射。
4. 按公式 (11) 对细节层施加默认 1.2 倍纹理增益。
5. 按公式 (12) 重组，得到 TXI mode 2。
6. 在 CIE Lab 的 `a*` 通道使用论文给出的 `(0,0) → (15,5) → (30,30)` 折线，得到 TXI mode 1。

论文没有给出双边滤波的具体参数、反光检测规则以及内镜设备的色调曲线。本实现提供可用的默认值，但不宣称与 Olympus 商用 TXI 像素一致。可通过 `--spatial-sigma`、`--range-sigma`、`--tone-gamma` 调整常见输入；其他参数见 `TXIConfig`。

论文默认参数针对动物胃肠内镜图像；PitVis 经鼻垂体手术视频的亮度和色彩分布不同。九帧测试中，默认暗部阈值平均只覆盖约 12% 的可见画面，因此默认版变化较小。`PITVIS_CONFIG` 是单独保留的探索性调参版。

### 参数依据与 PitVis 优化

| 参数 | 论文复现预设 | PitVis 实验预设 | 作用 |
| --- | ---: | ---: | --- |
| 暗部阈值 `brightness_threshold` | 0.25 × 图像最大值 | 0.45 × 图像最大值 | 覆盖更多较暗组织；论文给出曾测试 0.20–0.75 |
| 暗部指数 `brightness_alpha` | 1/1.4 ≈ 0.714 | 0.60 | 较小值提亮更强；论文测试 0.5–1 |
| 纹理增益 `texture_gain` | 1.2 | 1.45 | 论文测试 1–2，并提醒过强会过度增强 |
| 双边滤波 `spatial_sigma` / `range_sigma` | 15 / 0.12 | 25 / 0.22 | 论文没有公布数值；仅为本实现的经验值 |
| Lab 红浅色折线 | (0,0)→(15,5)→(30,30) | (0,0)→(20,8)→(45,45) | PitVis 色彩范围不同；扩展幅度未获临床验证 |
| 对数细节噪声门槛 / 额外增益上限 | 0 / 无 | 0.035 / 0.30 | 新增视频降噪保护，避免小波动及强边缘过度放大 |
| 视野边界渐隐 | 关闭 | 原图最大通道值 0.04–0.16 | 减少手术视频圆形视野旁彩边 |

输入是已渲染的 8 位视频帧，原设备的色调曲线与原始传感器数据不可得，因此两个预设的 `tone_gamma` 都保持 1。可在命令行覆盖参数，例如 `--texture-gain 1.3 --detail-noise-floor 0.05`；其他可调项见 `python txi.py --help`。对不同内镜和曝光条件应重新评估预设。

当前九帧的 mode 2 测试中，优化前后暗部亮度中位增量平均约为 5.11 与 5.22 灰度级；新增接近饱和像素比例平均从 0.192% 降至 0.036%。在原图最大通道值为 5–34 的边界区域，mode 1 的平均绝对变化从 13.33 降至 3.74 灰度级。结果保存在本地 `data/pitvis_txi_optimized/`，源视频帧和生成图像按项目设置不提交到 Git。

## 原有 Retinex 示例

```bash
python demo.py
```

原有算法及说明见 `code/retinex.py`。

## 参考文献

- Sato et al., *TXI: Texture and Color Enhancement Imaging for Endoscopic Image Enhancement*, Journal of Healthcare Engineering, 2021. https://pmc.ncbi.nlm.nih.gov/articles/PMC8049784/
- Olympus, *Technical Description of EVIS X1*, pp. 12–15. https://www.olympus-global.com/ir/data/pdf/Technical_Description_of_EVIS_X1.pdf
- Petro et al., *Multiscale Retinex*, Image Processing On Line, 2014. https://doi.org/10.5201/ipol.2014.107
