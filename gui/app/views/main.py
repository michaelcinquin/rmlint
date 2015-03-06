#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
import os
import math

# External:
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import GLib

# Internal:
from app.util import View, IndicatorLabel
from app.runner import Runner

from app.cellrenderers import CellRendererSize
from app.cellrenderers import CellRendererModifiedTime
from app.cellrenderers import CellRendererCount
from app.cellrenderers import CellRendererLint


class StatsRow(Gtk.Grid):
    def __init__(self):
        Gtk.Grid.__init__(self)
        self.set_margin_start(10)
        self.set_margin_end(10)

        self.label = IndicatorLabel()
        self.label.set_state(None)
        self.label.set_halign(Gtk.Align.START)

        self.bar = Gtk.LevelBar()
        self.bar.set_hexpand(True)
        self.bar.set_vexpand(False)
        self.bar.set_margin_left(5)
        self.bar.set_mode(Gtk.LevelBarMode.DISCRETE)
        self.bar.set_size_request(150, -1)
        self.bar.set_halign(Gtk.Align.END)

        self.attach(self.label, 0, 0, 1, 1)
        self.attach_next_to(self.bar, self.label, Gtk.PositionType.RIGHT, 1, 1)

        # TODO:
        self.label.set_markup(
            "<b>10 Duplicates</b> in <b>5 Groups</b> / <b>100</b> Total files"
        )
        self.bar.set_value(0.5)

        self.set_halign(Gtk.Align.FILL)


class Chart(Gtk.DrawingArea):
    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.set_size_request(300, 300)
        self.connect('draw', self._on_draw)

    def _on_draw(self, _, ctx):
        alloc = self.get_allocation()

        ctx.move_to(alloc.width / 2, alloc.height / 2)
        ctx.set_source_rgba(1.0, 0.5, 0.1, 0.5)
        ctx.arc(
            alloc.width / 2,
            alloc.height / 2,
            min(alloc.width, alloc.height) / 3 ,
            0,
            math.pi * (2 / 3)
        )
        ctx.fill()

        ctx.move_to(alloc.width / 2, alloc.height / 2)
        ctx.set_source_rgba(0.5, 0.1, 1.0, 0.5)
        ctx.arc(
            alloc.width / 2,
            alloc.height / 2,
            min(alloc.width, alloc.height) / 3 ,
            math.pi * (2 / 3),
            1.5 * math.pi
        )
        ctx.fill()

        ctx.move_to(alloc.width / 2, alloc.height / 2)
        ctx.set_source_rgba(0.1, 1.0, 0.5, 0.5)
        ctx.arc(
            alloc.width / 2,
            alloc.height / 2,
            min(alloc.width, alloc.height) / 3 ,
            1.5 * math.pi,
            2 * math.pi
        )
        ctx.fill()


class ResultActionBar(Gtk.ActionBar):
    def __init__(self):
        Gtk.ActionBar.__init__(self)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.get_style_context().add_class("linked")
        self.set_center_widget(box)

        icon_names = [
            'view-refresh-symbolic',
            'printer-printing-symbolic',
            'system-run-symbolic'
        ]

        for icon_name in icon_names:
            btn = Gtk.Button()
            btn.add(
                Gtk.Image.new_from_gicon(
                    Gio.ThemedIcon(name=icon_name),
                    Gtk.IconSize.BUTTON
                )
            )
            box.pack_start(btn, False, False, 0)


def build_stats_pane():
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.pack_start(
        Chart(), True, True, 0
    )
    box.pack_start(
        StatsRow(), False, True, 5
    )
    box.pack_start(
        StatsRow(), False, True, 5
    )
    box.pack_start(
        ResultActionBar(), False, True, 0
    )
    return box


def _create_column(title, renderer, pack_end=True, expand=False, **kwargs):
    column = Gtk.TreeViewColumn()
    column.set_title(title)
    column.set_resizable(True)
    column.set_expand(expand)
    # column.set_min_width(100)

    renderer = renderer[0]
    renderer.set_alignment(1.0 if pack_end else 0.0, 0.5)

    pack_func = column.pack_end if pack_end else column.pack_start
    if expand is True:
        pack_func(Gtk.CellRendererToggle(), False)

    pack_func(renderer, expand)

    column.set_attributes(cell_renderer=renderer, **kwargs)
    return column


def _get_dir_size(path):
    # TODO: This is wrong, use du like walk or level up.
    try:
        return os.stat(path).st_size
    except OSError:
        return -1

class RmlintTreeView(Gtk.TreeView):
    def __init__(self):
        Gtk.TreeView.__init__(self)

        self.md = Gtk.TreeStore(bool, str, int, int, int, int, str)
        self._filter_query = None
        self.filter_model = self.md.filter_new()
        self.filter_model.set_visible_func(self._filter_func)

        self.set_model(self.filter_model)

        self.append_column(_create_column(
            'Path', [CellRendererLint()], pack_end=False, expand=True, text=1, tag=5
        ))
        self.append_column(_create_column(
            'Size', [CellRendererSize()], size=2
        ))
        self.append_column(_create_column(
            'Count', [CellRendererCount()], count=3
        ))
        self.append_column(_create_column(
            'Changed', [CellRendererModifiedTime()], mtime=4
        ))
        self.set_tooltip_column(6)

        self.iter_map = {}

    def refilter(self, filter_query):
        self._filter_query = filter_query
        print(self._filter_query)
        self.filter_model.refilter()
        self.expand_all()

    def _filter_func(self, model, iter, data):
        print(model, self.md)
        if self.md.iter_n_children(iter) > 0:
            return True

        if self._filter_query is not None:
            # print(model[iter][1], self._filter_query, self._filter_query in model[iter][1])
            return self._filter_query in model[iter][1]
        return True

    def add_path(self, elem):
        GLib.idle_add(self._add_path_deferred, elem, len(elem.silbings))
        for twin in elem.silbings:
            GLib.idle_add(self._add_path_deferred, twin, len(elem.silbings))

    def set_root(self, root_path):
        self.root_path = root_path
        self.iter_map[root_path] = self.root = self.md.append(
            None, (False, os.path.basename(root_path), 0, 0, 0, IndicatorLabel.THEME, '/')
        )

    def _add_path_deferred(self, elem, twin_count):
        folder = os.path.dirname(elem.path)
        if folder.startswith(self.root_path):
            folder = folder[len(self.root_path):]

        parts = folder.split('/')[1:] if folder else []
        parent = self.iter_map[self.root_path]

        for idx, part in enumerate(parts):
            part_path = os.path.join(*parts[:idx + 1])
            part_iter = self.iter_map.get(part_path)
            if part_iter is None:
                full_path = os.path.join(self.root_path, part_path)
                print(full_path)
                part_iter = self.iter_map[part_path] = self.md.append(
                    parent, (
                        idx % 2,
                        part or '',
                        _get_dir_size(full_path),
                        0, 0,
                        IndicatorLabel.NONE,
                        elem.path
                    )
                )

            parent = part_iter

        tag = IndicatorLabel.SUCCESS if elem.is_original else IndicatorLabel.ERROR
        self.md.append(
            parent, (
                False,
                os.path.basename(elem.path),
                elem.size,
                -twin_count,
                elem.mtime,
                tag,
                elem.path
            )
        )

        # Do not repeat this idle action.
        return False

    def finish_add(self):
        self.expand_all()
        self.columns_autosize()


class MainView(View):
    def __init__(self, app):
        View.__init__(self, app)

        # Disable scrolling for the main view:
        self.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.NEVER
        )

        self.tv = RmlintTreeView()
        self.tv.set_halign(Gtk.Align.FILL)

        scw = Gtk.ScrolledWindow()
        scw.set_vexpand(True)
        scw.set_valign(Gtk.Align.FILL)
        scw.add(self.tv)

        stats = build_stats_pane()
        stats.set_halign(Gtk.Align.FILL)
        stats.set_vexpand(True)
        stats.set_valign(Gtk.Align.FILL)

        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        right_pane = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        right_pane.pack_start(separator, False, False, 0)
        right_pane.pack_start(stats, True , True, 0)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.attach(scw, 0, 0, 1, 1)
        grid.attach_next_to(right_pane, scw, Gtk.PositionType.RIGHT, 1, 1)

        self.add(grid)

        def _search_changed(entry):
            print(entry.get_text())
            self.tv.refilter(entry.get_text() or None)

        self.app_window.search_entry.connect('search-changed', _search_changed)

        # TODO: call later
        self.create_runner()

    def create_runner(self):
        root_path = '/usr/include'
        self.tv.set_root(root_path)

        runner = Runner(self.app.settings, [root_path])
        runner.connect(
            'lint-added', lambda _, elem: self.tv.add_path(elem)
        )

        progress_source = GLib.timeout_add(
            100,
            lambda: self.app_window.show_progress(None) or True
        )

        # self.tv.set_sensitive(False)
        self.app_window.show_progress(None)

        def on_process_finish(runner, msg):
            # self.tv.set_sensitive(True)
            self.tv.finish_add()

            self.app_window.hide_progress()

            GLib.source_remove(progress_source)

            if msg is not None:
                self.app_window.show_infobar(
                    msg, message_type=Gtk.MessageType.WARNING
                )

        runner.connect('process-finished', on_process_finish)

        # Start the process asynchronously
        runner.run()