# PitVis 无标注测试帧

此目录中的 PNG 来自 [PitVis-2023 Challenge 原始视频数据集](https://doi.org/10.5522/04/26531686.v3) 的 `video_23.mp4`。下载的视频文件与仓库公布的 MD5 `ffc5857e6bff8d767e6f6e2780c6bf70` 一致。仅从视频解码原始帧，没有使用对应的 `annotations_23.csv`，也没有叠加标签或做 TXI 增强。

使用 `scripts/extract_pitvis_frames.py` 在视频的 5% 至 95% 时间范围内等间距提取 10 帧。视频为 1280×720、24 FPS。最初提取的 10 帧的源视频、帧号和时间戳见 `manifest.csv`。当前工作目录中 `video_23_frame_013588.png` 不在，因此本地实际留存 9 张原始帧。

视频和 PNG 不随代码仓库上传。克隆项目后可从官方文件地址重新获取并提取：

```bash
curl -L --fail -o video_23.mp4 https://ndownloader.figshare.com/files/48617401
python scripts/extract_pitvis_frames.py video_23.mp4 data/pitvis_unlabeled
```

原始数据集许可为 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)；使用或分享这些帧时请保留来源与许可信息。
