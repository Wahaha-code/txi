# PitVis TXI 九帧测试

本目录包含当前留在 `data/pitvis_unlabeled/` 中的 9 张原始帧的论文默认参数 TXI 测试结果。每帧分别生成 mode 1 和 mode 2 PNG，未修改原始帧。单独的 PitVis 调参版结果见 `../pitvis_txi_tuned/`。

`comparison.png` 按每行“原图 | mode 1 | mode 2”排列；`results.csv` 列出对应文件、视频时间戳及可视画面中的平均绝对像素变化。该数值仅用于确认处理产生了变化，不是临床或图像质量评分。

可用以下命令重现：

```bash
python scripts/test_txi_frames.py data/pitvis_unlabeled data/pitvis_txi_results
```

源数据和许可见 [`../pitvis_unlabeled/README.md`](../pitvis_unlabeled/README.md)。
