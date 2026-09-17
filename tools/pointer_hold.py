#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过 xdg-desktop-portal 的 RemoteDesktop 接口真实移动鼠标指针。
用法: pointer_hold.py <x> <y> <保持秒数>
用于验证 Dock 悬停放大 —— Wayland 下没有 xdotool/wtype，这是唯一无需 root 的注入途径。
第一次运行 GNOME 会弹授权框，需要在屏幕上点「允许」。
"""
import os
import sys
import time

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

X = float(sys.argv[1])
Y = float(sys.argv[2])
HOLD = float(sys.argv[3])

bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
PORTAL = "org.freedesktop.portal.Desktop"
PATH = "/org/freedesktop/portal/desktop"


def call(iface, method, params, timeout=30000):
    return bus.call_sync(PORTAL, PATH, iface, method, params, None,
                         Gio.DBusCallFlags.NONE, timeout, None)


def wait_response(handle, timeout_s=60):
    res = {}
    loop = GLib.MainLoop()

    def on_resp(conn, sender, path, iface, sig, params):
        code, results = params.unpack()
        res["code"] = code
        res["results"] = results
        loop.quit()

    sub = bus.signal_subscribe(PORTAL, "org.freedesktop.portal.Request", "Response",
                               handle, None, 0, on_resp)
    GLib.timeout_add_seconds(timeout_s, loop.quit)
    loop.run()
    bus.signal_unsubscribe(sub)
    return res


tok = "hptr%d" % os.getpid()

print("1) 建立会话…")
r = call("org.freedesktop.portal.RemoteDesktop", "CreateSession",
         GLib.Variant("(a{sv})", ({"handle_token": GLib.Variant("s", tok + "req"),
                                   "session_handle_token": GLib.Variant("s", tok)},)))
req_path = r.unpack()[0]
resp = wait_response(req_path, 30)
if resp.get("code") != 0:
    raise SystemExit("CreateSession 失败: %s" % resp)
session = resp["results"]["session_handle"]
print("   session =", session)

print("2) 申请指针设备…")
r = call("org.freedesktop.portal.RemoteDesktop", "SelectDevices",
         GLib.Variant("(oa{sv})", (session, {"types": GLib.Variant("u", 2),
                                             "handle_token": GLib.Variant("s", tok + "sel")})))
resp = wait_response(r.unpack()[0], 30)
if resp.get("code") != 0:
    raise SystemExit("SelectDevices 失败: %s" % resp)
print("   OK")

print("2.5) 申请屏幕源（GNOME 需要 stream 才能换算绝对坐标）…")
r = call("org.freedesktop.portal.ScreenCast", "SelectSources",
         GLib.Variant("(oa{sv})", (session, {"types": GLib.Variant("u", 1),
                                             "multiple": GLib.Variant("b", False),
                                             "handle_token": GLib.Variant("s", tok + "src")})))
resp = wait_response(r.unpack()[0], 30)
if resp.get("code") != 0:
    raise SystemExit("SelectSources 失败: %s" % resp)
print("   OK")

print("3) 请求授权（屏幕上会弹窗，请点「允许」）…")
r = call("org.freedesktop.portal.RemoteDesktop", "Start",
         GLib.Variant("(osa{sv})", (session, "",
                                    {"handle_token": GLib.Variant("s", tok + "start")})))
resp = wait_response(r.unpack()[0], 60)
if resp.get("code") != 0:
    raise SystemExit("未被授权 (code=%s) —— 需要你在弹出窗口上点「允许」" % resp.get("code"))
streams = resp["results"].get("streams", [])
print("   已授权 ✓  streams=%s" % (streams,))
if streams:
    node = streams[0][0]
    props = streams[0][1]
    size = props.get("size")
    pos = props.get("position")
    print("   stream 内容: node=%s size=%s position=%s" % (node, size, pos))
    if size:
        sw, sh = size
        if sw < X or sh < Y:
            print("   ⚠ 坐标超出 stream 尺寸，按比例换算")
            X = X * sw / 1920.0
            Y = Y * sh / 1080.0
            print("   换算后: (%.0f, %.0f)" % (X, Y))

print("4) 把指针移到 (%d, %d)，保持 %.0f 秒…" % (X, Y, HOLD))
call("org.freedesktop.portal.RemoteDesktop", "NotifyPointerMotionAbsolute",
     GLib.Variant("(oa{sv}udd)", (session, {}, 0, X, Y)))
time.sleep(HOLD)

print("5) 移开指针并结束会话")
call("org.freedesktop.portal.RemoteDesktop", "NotifyPointerMotionAbsolute",
     GLib.Variant("(oa{sv}udd)", (session, {}, 0, 960.0, 540.0)))
try:
    call("org.freedesktop.portal.Session", "Close", GLib.Variant("()", ()))
except Exception:
    pass
print("完成")
