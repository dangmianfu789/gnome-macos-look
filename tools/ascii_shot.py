#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把截图降采样成 ASCII 布局图 + 精确定位 macOS 三色灯色块。"""
import glob
import os
import sys

import numpy as np
from PIL import Image

_cands = glob.glob(os.path.expanduser("~/图片/Screenshot*.png")) + \
         glob.glob(os.path.expanduser("~/Pictures/Screenshot*.png"))
SHOT = sys.argv[1] if len(sys.argv) > 1 else (max(_cands, key=os.path.getmtime) if _cands else "")
im = Image.open(SHOT).convert("RGB")
W, H = im.size
print("截图 %s  %dx%d\n" % (SHOT.split("/")[-1], W, H))

# ---------- ASCII 亮度布局图 ----------
CW, CH = 96, 30
small = im.resize((CW, CH), Image.BILINEAR)
a = np.asarray(small).astype(int)
lum = a.mean(axis=2)
chars = " .:-=+*#%@"
print("=== 亮度布局图（每字符 %.0fx%.0f px，行号=像素 y）===" % (W / CW, H / CH))
print("    " + "".join(str((int(i * W / CW) // 100) % 10) for i in range(CW)))
for i, row in enumerate(lum):
    y = int(i * H / CH)
    line = "".join(chars[min(9, int(v / 25.6))] for v in row)
    print("%3d %s" % (y, line))

# ---------- 色块定位 ----------
print("\n=== 彩色块定位（红/黄/绿，阈值 40）===")
big = np.asarray(im).astype(int)
for name, (tr, tg, tb) in [("红", (255, 95, 87)), ("黄", (254, 188, 46)), ("绿", (40, 200, 64))]:
    d = np.abs(big[:, :, 0] - tr) + np.abs(big[:, :, 1] - tg) + np.abs(big[:, :, 2] - tb)
    ys, xs = np.where(d < 40)
    if len(xs) == 0:
        print("  %s: 无" % name)
        continue
    # 按 y 聚簇
    order = np.argsort(ys)
    ys, xs = ys[order], xs[order]
    clusters = []
    cur = [0]
    for i in range(1, len(ys)):
        if ys[i] - ys[cur[-1]] <= 8:
            cur.append(i)
        else:
            clusters.append(cur)
            cur = [i]
    clusters.append(cur)
    info = []
    for c in clusters:
        if len(c) < 15:
            continue
        cy, cx = ys[c], xs[c]
        info.append("n=%d x=%d~%d y=%d~%d" % (len(c), cx.min(), cx.max(), cy.min(), cy.max()))
    print("  %s: %s" % (name, " | ".join(info) if info else "无成簇色块"))
