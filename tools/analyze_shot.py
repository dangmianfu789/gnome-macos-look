#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 numpy 核对截图里的 macOS 化效果。需要带 numpy 的 python 环境。"""
import glob
import os
import sys

import numpy as np
from PIL import Image

_cands = glob.glob(os.path.expanduser("~/图片/Screenshot*.png")) + \
         glob.glob(os.path.expanduser("~/Pictures/Screenshot*.png"))
SHOT = sys.argv[1] if len(sys.argv) > 1 else (max(_cands, key=os.path.getmtime) if _cands else "")
im = Image.open(SHOT).convert("RGB")
a = np.asarray(im).astype(int)
H, W, _ = a.shape
print("截图 %dx%d\n" % (W, H))

# ---------- 1. 三色灯（严格阈值，避免壁纸近似色干扰）----------
print("=== 1. 窗口按钮三色灯 ===")
TARGETS = [("关闭", (255, 95, 87)), ("最小化", (254, 188, 46)), ("最大化", (40, 200, 64))]
found = {}
for name, (tr, tg, tb) in TARGETS:
    d = np.abs(a[:, :, 0] - tr) + np.abs(a[:, :, 1] - tg) + np.abs(a[:, :, 2] - tb)
    ys, xs = np.where(d < 18)          # 严格：只认几乎精确的颜色
    if len(xs) < 20:
        print("  %-8s 未找到（匹配 %d 像素）" % (name, len(xs)))
        continue
    # 取像素最多的那一簇所在的 y 行
    cy = int(np.median(ys))
    sel = np.abs(ys - cy) < 15
    xs2, ys2 = xs[sel], ys[sel]
    if len(xs2) < 20:
        print("  %-8s 未找到（无紧凑色块）" % name)
        continue
    print("  %-8s %4d 像素   x=%d~%d  y=%d~%d" %
          (name, len(xs2), xs2.min(), xs2.max(), ys2.min(), ys2.max()))
    found[name] = (int(np.median(xs2)), int(np.median(ys2)), len(xs2))

if len(found) == 3:
    row_ys = [v[1] for v in found.values()]
    xs = [found[k][0] for k in ("关闭", "最小化", "最大化")]
    ok_row = max(row_ys) - min(row_ys) <= 6
    ok_order = xs[0] < xs[1] < xs[2]
    print("  → 同一行: %s   顺序 红→黄→绿: %s   %s" %
          (ok_row, ok_order, "✅ 与 macOS 一致" if (ok_row and ok_order) else "⚠ 与 macOS 不一致"))
else:
    print("  → ❌ 未检出完整三色灯（可能窗口标题栏不在此截图内）")

# ---------- 2. 顶栏毛玻璃 ----------
print("\n=== 2. 顶栏（0~31px）===")
panel = a[0:31, :, :].mean(axis=2)
below = a[36:67, :, :].mean(axis=2)


def ds(x, k=16):
    n = (x.shape[0] // k) * k
    return x[:n].reshape(-1, k).mean(axis=1)


c = np.corrcoef(ds(panel), ds(below))[0, 1]
print("  顶栏整体亮度 %.0f，与正下方壁纸条带的相关性 %.2f（降采样后比较）" % (panel.mean(), c))
print("  → %s" % ("半透明/毛玻璃生效（顶栏透着壁纸纹理）" if c > 0.6 else
                  "顶栏偏不透明（或模糊半径大把纹理抹平了）"))

# ---------- 3. 底部 Dock ----------
print("\n=== 3. 底部 Dock ===")
strip = a[H - 70:H, :, :].mean(axis=2)
mid = strip[:, 610:1310].mean()
left = strip[:, 0:250].mean()
right = strip[:, 1670:1920].mean()
print("  底部 70px 亮度：左 %.0f  中(610~1310) %.0f  右 %.0f" % (left, mid, right))
if abs(mid - (left + right) / 2) > 12:
    print("  → ✅ 底部中央存在一块 Dock 面板（与两侧壁纸亮度差 %.0f）" % abs(mid - (left + right) / 2))
else:
    print("  → ⚠ 底部中央与两侧亮度接近，没看出独立 Dock 面板")

# ---------- 4. 左上角苹果菜单 ----------
print("\n=== 4. 左上角 x=8~40, y=4~28 ===")
logo = a[4:28, 8:40, :].mean(axis=2)
print("  平均亮度 %.0f，局部对比度(标准差) %.1f → %s" %
      (logo.mean(), logo.std(), "有图形" if logo.std() > 15 else "看着是空的"))
