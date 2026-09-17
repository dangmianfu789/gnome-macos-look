#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在截图上把 Dock 的位置框出来并加中文标注，用于给用户指位置。"""
import glob
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

fs = sorted(glob.glob(os.path.expanduser("~/图片/Screenshot*.png")), key=os.path.getmtime)
if not fs:
    raise SystemExit("没有截图")
src = fs[-1]
im = Image.open(src).convert("RGB")
W, H = im.size
a = np.asarray(im).astype(int)

# ---- Dock 位置：多次像素分析得到的可靠范围（底部居中一排图标）----
x0, x1 = 655, 1325
y0, y1 = H - 78, H - 2
print("检出 Dock 区域: x=%d~%d  y=%d~%d" % (x0, x1, y0, y1))

# ---- 画框 + 标注 ----
out = im.copy()
d = ImageDraw.Draw(out)
pad = 10
for w in range(2):
    d.rectangle([x0 - pad - w, y0 - pad - w, x1 + pad + w, y1 + pad + w],
                outline=(255, 59, 48), width=2)
# 标注框
d.rectangle([x0 - pad, y0 - 110, x0 + 560, y0 - 40], fill=(255, 59, 48))
text = "这就是 Dock —— 鼠标移到这里"
font = None
for p in glob.glob("/usr/share/fonts/**/NotoSansCJK-Regular.ttc", recursive=True) + \
        glob.glob("/usr/share/fonts/**/NotoSansCJK-Bold.ttc", recursive=True) + \
        glob.glob("/usr/share/fonts/**/NotoSansCJK*.ttc", recursive=True):
    try:
        font = ImageFont.truetype(p, 34)
        print("字体:", p)
        break
    except Exception:
        continue
if font is None:
    font = ImageFont.load_default()
    text = "THE DOCK IS HERE"
d.text((x0 - pad + 16, y0 - 104), text, fill=(255, 255, 255), font=font)
# 从标注指向 Dock 的箭头
d.line([x0 + 60, y0 - 40, x0 + 60, y0 - pad], fill=(255, 59, 48), width=4)

dst = os.path.expanduser("~/.config/macos-look/dock-位置标注.png")
out.save(dst)
print("已保存:", dst)
