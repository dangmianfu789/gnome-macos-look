#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""弹一个带 libadwaita 标题栏（含窗口按钮）的临时窗口，用于核对三色灯；25 秒后自动关闭。"""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.example.WindowProbe")

    def do_activate(self):
        win = Adw.ApplicationWindow(application=self)
        win.set_title("窗口按钮自检")
        win.set_default_size(820, 480)
        view = Adw.ToolbarView()
        view.add_top_bar(Adw.HeaderBar())
        view.set_content(Gtk.Label(label="正在核对窗口按钮颜色…"))
        win.set_content(view)
        win.present()
        GLib.timeout_add_seconds(25, self.quit)


print(App().run([]))
