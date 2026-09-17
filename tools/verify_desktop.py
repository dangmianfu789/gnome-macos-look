#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""综合核对截图：三色灯几何 + 底部 Dock 区域（自动取最新截图）。"""
import glob
import os
import sys

import numpy as np
from PIL import Image

if len(sys.argv) > 1:
    SHOT = sys.argv[1]
else:
    cands = glob.glob(os.path.expanduser("~/图片/Screenshot*.png"))
    SHOT = max(cands, key=os.path.getmtime)
im = Image.open(SHOT).convert("RGB")
big = np.asarray(im).astype(int)
H, W, _ = big.shape
print("截图 %s  %dx%d\n" % (os.path.basename(SHOT), W, H))

print("=== 1. 三色灯几何 ===")
res = {}
for name, (tr, tg, tb) in [("关闭红", (255, 95, 87)), ("最小化黄", (254, 188, 46)), ("最大化绿", (40, 200, 64))]:
    d = np.abs(big[:, :, 0] - tr) + np.abs(big[:, :, 1] - tg) + np.abs(big[:, :, 2] - tb)
    ys, xs = np.where(d < 40)
    if len(xs) < 50:
        print("  %-8s 未找到" % name)
        continue
    cy = int(np.median(ys))
    m = np.abs(ys - cy) < 20
    xs2, ys2 = xs[m], ys[m]
    w, h = int(xs2.max() - xs2.min() + 1), int(ys2.max() - ys2.min() + 1)
    res[name] = (int(xs2.min()), int(xs2.max()), w, h, int(ys2.min()))
    print("  %-8s x=%d~%d  y起=%d  尺寸 %dx%d  %s" %
          (name, xs2.min(), xs2.max(), ys2.min(), w, h,
           "✅ 接近正圆" if abs(w - h) <= 4 else "⚠ 宽%d 高%d" % (w, h)))
if len(res) == 3:
    xs = [res[k][0] for k in ("关闭红", "最小化黄", "最大化绿")]
    print("  → 顺序红→黄→绿: %s" % ("✅ 与 macOS 一致" if xs[0] < xs[1] < xs[2] else "⚠ 不同"))

print("\n=== 2. 底部 150px 高分辨率亮度图（每字符 10x6 px）===")
band = big[H - 150:H, :, :]
bw, bhh = 192, 25
small = Image.fromarray(band.astype("uint8")).resize((bw, bhh), Image.BILINEAR)
arr = np.asarray(small).astype(int).mean(axis=2)
chars = " .:-=+*#%@"
lo, hi = arr.min(), arr.max()
print("    亮度范围 %.0f~%.0f" % (lo, hi))
for i, row in enumerate(arr):
    y = H - 150 + int(i * 150 / bhh)
    print(" %4d %s" % (y, "".join(chars[min(9, int((v - lo) / max(hi - lo, 1) * 9.99))] for v in row)))

print("\n=== 3. Dock 区域判定 ===")
strip = band.mean(axis=2)
colvar = strip.std(axis=0)                 # 每列的纵向起伏：图标处起伏大
mid = colvar[610:1310].mean()
side = np.concatenate([colvar[0:400], colvar[1520:1920]]).mean()
print("  中央(610~1310)列起伏 %.1f   两侧列起伏 %.1f" % (mid, side))
rowmean = strip.mean(axis=1)
grad = np.abs(np.diff(rowmean))
top_grad = int(np.argmax(grad))
print("  纵向最大亮度突变在 y=%d（强度 %.1f）" % (H - 150 + top_grad, grad[top_grad]))
print("  → %s" % ("✅ 中央有图标状的纵向起伏，且底部存在面板边界 → Dock 正常"
                  if mid > side * 1.3 else "⚠ 中央起伏与两侧接近，Dock 特征不明显"))
