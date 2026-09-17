#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""顶栏内容分布检查：苹果 logo 是否在左端、时钟是否在最右端。"""
import glob
import os

import numpy as np
from PIL import Image

cands = glob.glob(os.path.expanduser("~/图片/Screenshot*.png")) + \
        glob.glob(os.path.expanduser("~/.config/macos-look/预览-三色窗口按钮.png"))
SHOT = max(cands, key=os.path.getmtime)
im = Image.open(SHOT).convert("RGB")
a = np.asarray(im).astype(int)
H, W, _ = a.shape
print("截图 %s\n" % os.path.basename(SHOT))

panel = a[2:30, :, :]
lum = panel.mean(axis=2)

# 每 12px 一列，取该列的最大对比度 → 有文字/图标的地方对比度高
cols = []
for x in range(0, W, 12):
    seg = lum[:, x:x + 12]
    if seg.size == 0:
        continue
    cols.append((x, seg.max() - seg.min()))
prof = np.array([c[1] for c in cols])
xs = np.array([c[0] for c in cols])

print("=== 顶栏内容分布（每字符=12px，@=有内容 . =空白）===")
print("   x: 0" + " " * 38 + "960（屏幕中心）" + " " * 28 + "1920")
line = "".join("@" if v > 60 else ("+" if v > 35 else ".") for v in prof)
print("      " + line[:80])
print("      " + line[80:])
print("  说明: @=明显内容(文字/图标)  +=弱内容  .=空")

blocks = []
inb = False
for x, v in zip(xs, prof):
    if v > 55 and not inb:
        start = x
        inb = True
    elif v <= 55 and inb:
        blocks.append((start, x))
        inb = False
if inb:
    blocks.append((start, W))
blocks = [b for b in blocks if b[1] - b[0] >= 12]
print("\n  内容块: %s" % ", ".join("%d~%d" % b for b in blocks))

left_end = W // 6
if any(b[0] < left_end for b in blocks):
    print("  → ✅ 顶栏左端有内容（苹果菜单所在处）")
else:
    print("  → ⚠ 顶栏左端是空的（苹果 logo 可能没显示）")

right = [b for b in blocks if b[0] > W * 0.75]
mid = [b for b in blocks if W * 0.35 < b[0] < W * 0.65]
if right:
    print("  → ✅ 顶栏右侧 %d 个内容块（北京时间/状态图标，最右块到 x=%d）" % (len(right), right[-1][1]))
if not mid:
    print("  → ✅ 顶栏中部为空（Activities 文字与工作区圆点已隐藏）")
else:
    print("  → ⚠ 顶栏中部仍有内容块 %s（可能是没隐藏干净）" % ", ".join("%d~%d" % b for b in mid))
