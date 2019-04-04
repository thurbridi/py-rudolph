import gi
import numpy as np
from gi.repository import Gtk, Gdk

from graphics import (
    make_offset_matrix,
    make_rotation_matrix,
    make_scale_matrix,
    GraphicObject,
    Line,
    Point,
    Polygon,
    Rect,
    Vec2,
)

gi.require_version('Gtk', '3.0')
gi.require_foreign('cairo')


NB_PAGES = {
    0: 'point',
    1: 'line',
    2: 'polygon'
}

BUTTON_EVENTS = {
    1: 'left',
    2: 'middle',
    3: 'right',
}


class NewObjectDialogHandler:
    def __init__(self, dialog, builder):
        self.dialog = dialog
        self.builder = builder
        self.vertices = []

    def on_ok(self, widget):
        window = self.builder.get_object('new_object_window')
        notebook = self.builder.get_object('notebook1')

        page_num = notebook.get_current_page()
        name = self.builder.get_object('entry_name').get_text()

        if NB_PAGES[page_num] == 'point':
            x = float(self.builder.get_object('entryX').get_text())
            y = float(self.builder.get_object('entryY').get_text())

            self.dialog.new_object = Point(Vec2(x, y), name=name)
        elif NB_PAGES[page_num] == 'line':
            y2 = float(self.builder.get_object('entryY2').get_text())
            x1 = float(self.builder.get_object('entryX1').get_text())
            y1 = float(self.builder.get_object('entryY1').get_text())
            x2 = float(self.builder.get_object('entryX2').get_text())

            self.dialog.new_object = Line(
                Vec2(x1, y1),
                Vec2(x2, y2),
                name=name
            )
        elif NB_PAGES[page_num] == 'polygon':
            if len(self.vertices) >= 3:
                self.dialog.new_object = Polygon(self.vertices, name=name)
        else:
            raise ValueError('No page with given index.')

        window.destroy()

    def on_cancel(self, widget):
        window = self.builder.get_object('new_object_window')
        window.destroy()

    def on_add_point(self, widget):
        vertice_store = self.builder.get_object('vertice_store')

        x = float(self.builder.get_object('entryX3').get_text())
        y = float(self.builder.get_object('entryY3').get_text())

        vertice_store.append([x, y, 1])
        self.vertices.append(Vec2(x, y))


class NewObjectDialog(Gtk.Dialog):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

        self.builder = Gtk.Builder.new_from_file('ui/newobjectdialog.ui')
        self.builder.connect_signals(
            NewObjectDialogHandler(self, self.builder)
        )
        self.new_object = None

        self.dialog_window = self.builder.get_object('new_object_window')


class MainWindowHandler:
    def __init__(self, builder):
        self.builder = builder
        self.window = self.builder.get_object('main_window')
        self.object_store = self.builder.get_object('object_store')
        self.display_file = []
        self.world_window = Rect(
            Vec2(0, 0),
            Vec2(600, 300)
        )
        self.press_start = None

    def on_destroy(self, *args):
        self.window.get_application().quit()

    def on_draw(self, widget, cr):
        def window_to_viewport(v: Vec2):
            return Vec2(
                ((v.x - self.world_window.min.x) / window_w) * vp_w,
                (1 - ((v.y - self.world_window.min.y) / window_h)) * vp_h
            )

        vp_w = widget.get_allocated_width()
        vp_h = widget.get_allocated_height()

        cr.set_line_width(2.0)
        cr.paint()
        cr.set_source_rgb(0.8, 0.0, 0.0)

        window_w = self.world_window.width
        window_h = self.world_window.height

        for object in self.display_file:
            object.draw(cr, window_to_viewport)

    def on_new_object(self, widget):
        dialog = NewObjectDialog()
        response = dialog.dialog_window.run()

        if response == Gtk.ResponseType.OK:
            self.add_object(dialog.new_object)
            self.builder.get_object('drawing_area').queue_draw()
        elif response == Gtk.ResponseType.CLOSE:
            print('CANCEL')

    def on_quit(self, widget):
        self.window.close()

    def on_about(self, widget):
        about_dialog = Gtk.AboutDialog(
            None,
            authors=['Arthur Bridi Guazzelli', 'João Paulo T. I. Z.'],
            version='1.0.0',
            program_name='Rudolph'
        )
        about_dialog.run()

    def on_button_press(self, widget, event):
        if BUTTON_EVENTS[event.button] == 'left':
            # register x, y
            self.press_start = Vec2(-event.x, event.y)
            self.dragging = True

    def on_motion(self, widget, event):
        # register x, y
        # translate window
        if self.dragging:
            current = Vec2(-event.x, event.y)
            delta = current - self.press_start
            self.press_start = current
            self.world_window.min += delta
            self.world_window.max += delta
            widget.queue_draw()

    def on_button_release(self, widget, event):
        if BUTTON_EVENTS[event.button] == 'left':
            self.dragging = False

    def on_scroll(self, widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            # zoom in 10%
            self.world_window.max *= 0.9

        elif event.direction == Gdk.ScrollDirection.DOWN:
            # zoom out 10%
            self.world_window.max *= 1.1

        widget.queue_draw()

    def on_press_navigation_button(self, widget):
        TRANSFORMATIONS = {
            'nav-move-up': make_offset_matrix(0, 10),
            'nav-move-down': make_offset_matrix(0, -10),
            'nav-move-left': make_offset_matrix(-10, 0),
            'nav-move-right': make_offset_matrix(10, 0),
            'nav-rotate-left': make_rotation_matrix(-5),
            'nav-rotate-right': make_rotation_matrix(5),
            'nav-zoom-in': make_scale_matrix(1.1, 1.1),
            'nav-zoom-out': make_scale_matrix(0.9, 0.9),
        }

        selected_objs = self.selected_objs

        for obj in selected_objs:
            obj.transform(matrix=TRANSFORMATIONS[widget.get_name()])

        self.window.queue_draw()

    @property
    def selected_objs(self):
        tree = self.builder.get_object('tree-displayfiles')
        store, rows = tree.get_selection().get_selected_rows()

        return (self.display_file[int(str(index))] for index in rows)

    def add_object(self, obj: GraphicObject):
        self.display_file.append(obj)
        self.object_store.append([
            obj.name,
            str(f'<{type(obj).__name__}>')
        ])


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        builder = Gtk.Builder.new_from_file('ui/mainwindow.ui')

        self.window = builder.get_object('main_window')

        builder.connect_signals(MainWindowHandler(builder))
