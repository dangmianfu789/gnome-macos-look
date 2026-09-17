#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 xdg-desktop-portal 截取当前桌面（GNOME Wayland 唯一可行的自检方式）"""
import os
import sys

from gi.repository import Gio, GLib

bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
PORTAL = "org.freedesktop.portal.Desktop"
PATH = "/org/freedesktop/portal/desktop"

result = {}
loop = GLib.MainLoop()


def on_response(conn, sender, obj_path, iface, signal, params):
    code, results = params.unpack()
    result["code"] = code
    result["uri"] = results.get("uri")
    loop.quit()


unique = bus.get_unique_name().lstrip(":").replace(".", "_")
token = "macoslookshot%d" % os.getpid()
handle = "/org/freedesktop/portal/desktop/request/%s/%s" % (unique, token)

bus.signal_subscribe(PORTAL, "org.freedesktop.portal.Request", "Response",
                     handle, None, 0, on_response)

opts = {
    "handle_token": GLib.Variant("s", token),
    "interactive": GLib.Variant("b", False),
}
try:
    bus.call_sync(PORTAL, PATH, "org.freedesktop.portal.Screenshot", "Screenshot",
                  GLib.Variant("(sa{sv})", ("", opts)),
                  None, Gio.DBusCallFlags.NONE, 30000, None)
except GLib.Error as e:
    print("调用失败:", e.message)
    sys.exit(2)

GLib.timeout_add_seconds(45, lambda: loop.quit())
loop.run()

code = result.get("code")
uri = result.get("uri")
if code == 0 and uri:
    print("截图成功:", uri.replace("file://", ""))
else:
    print("未取得截图 (response code=%s)" % code)
    sys.exit(1)
