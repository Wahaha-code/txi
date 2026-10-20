# PitVis 优化预设测试

使用 `PITVIS_CONFIG` 处理当前保留的 9 张无标注 `video_23` 帧：

```bash
python scripts/test_txi_frames.py data/pitvis_unlabeled data/pitvis_txi_optimized --preset pitvis
```

`comparison.png` 按原图、mode 1、mode 2 排列。`results.csv` 保存每帧的平均像素变化、暗部亮度增量、新增接近饱和像素比例和组织内部梯度比。PNG 是从原始视频生成的本地文件，不纳入 Git。参数与评估局限见项目 `readme.md`。
