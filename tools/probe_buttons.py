#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查 libadwaita 窗口按钮的真实 CSS 节点名与类名，并打印计算后的前景色。
   用来确认 ~/.config/gtk-4.0/gtk.css 里的选择器到底匹不匹配。"""
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

hits = []


def walk(w, depth=0):
    try:
        node = w.get_name()
    except Exception:
        node = "?"
    cls = " ".join(w.get_css_classes() or [])
    line = "%s%s  [%s]  <%s>" % ("  " * depth, type(w).__name__, node, cls)
    if isinstance(w, Gtk.Button) or "windowcontrols" in (node or "") or "titlebutton" in cls:
        hits.append(line)
        try:
            c = w.get_color()
            hits.append("      color = %s" % c.to_string())
        except Exception:
            pass
        try:
            hits.append("      has_css_class(close)=%s minimize=%s maximize=%s" %
                        (w.has_css_class("close"), w.has_css_class("minimize"), w.has_css_class("maximize")))
        except Exception:
            pass
    child = w.get_first_child()
    while child is not None:
        walk(child, depth + 1)
        child = child.get_next_sibling()


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.example.WindowProbe2")

    def do_activate(self):
        win = Adw.ApplicationWindow(application=self)
        win.set_default_size(700, 420)
        view = Adw.ToolbarView()
        view.add_top_bar(Adw.HeaderBar())
        view.set_content(Gtk.Label(label="probe"))
        win.set_content(view)
        win.present()
        GLib.timeout_add(1500, self.probe, win)

    def probe(self, win):
        walk(win)
        print("\n".join(hits) if hits else "没有找到任何 button/windowcontrols 节点")
        self.quit()
        return False


App().run([])
