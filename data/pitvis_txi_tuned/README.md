# PitVis 调参版 TXI 九帧测试

此目录包含当前留存的 9 张 PitVis 原始帧经 `PITVIS_CONFIG` 处理后的 mode 1 和 mode 2。`comparison.png` 每行依次为原图、mode 1、mode 2。`results.csv` 记录文件名、时间戳和可视画面内的平均绝对像素变化。

调参版使用较宽的双边滤波范围、较高的暗部阈值和纹理增益，并将 mode 1 的 Lab `a*` 折线调整为 `(0,0) → (20,8) → (45,45)`。这些是针对当前手术视频的探索性参数，**并非论文参数或经临床验证的设置**。论文默认版结果保存在 `../pitvis_txi_results/`，原始帧未改动。

重现命令：

```bash
python scripts/test_txi_frames.py data/pitvis_unlabeled data/pitvis_txi_tuned --preset pitvis
```
