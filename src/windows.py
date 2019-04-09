from enum import auto, Enum

import gi
from gi.repository import Gtk, Gdk

import graphics
from graphics import (
    GraphicObject,
    Line,
    Point,
    Polygon,
    Rect,
    Vec2,
    Scene,
)

from cgcodecs import ObjCodec

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


class RotationRef(Enum):
    CENTER = auto()
    ORIGIN = auto()
    ABSOLUTE = auto()


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
        self.window = builder.get_object('main_window')
        self.object_store = builder.get_object('object_store')
        self.display_file = []
        self.world_window = None
        self.output_buffer = builder.get_object('outputbuffer')
        self.press_start = None
        self.old_size = None
        self.rotation_ref = RotationRef.CENTER
        self.current_file = None

        self.add_object(Point(Vec2(0, 0), name='origin'))
        self.add_object(Line(Vec2(200, 200), Vec2(100, 150), name='line'))
        self.add_object(Polygon(
            [Vec2(400, 400), Vec2(500, 400), Vec2(450, 300)],
            name='poly'
        ))
        self.add_object(Polygon(
            [Vec2(100, 300), Vec2(200, 300), Vec2(200, 400), Vec2(100, 400)],
            name='poly'
        ))

    def on_destroy(self, *args):
        self.window.get_application().quit()

    def log(self, msg: str):
        self.output_buffer.insert_at_cursor(f'{msg}\n')
        scrollwindow = self.builder.get_object('output_scrollwindow')
        adjustment = scrollwindow.get_vadjustment()
        adjustment.set_value(adjustment.get_upper())

    def on_resize(self, widget: Gtk.Widget, allocation: Gdk.Rectangle):
        if self.world_window is None:
            self.old_size = allocation
            self.world_window = Rect(
                Vec2(0, 0),
                Vec2(allocation.width, allocation.height)
            )

        w_proportion = allocation.width / self.old_size.width
        h_proportion = allocation.height / self.old_size.height

        self.world_window.max = Vec2(
            self.world_window.max.x * w_proportion,
            self.world_window.max.y * h_proportion
        )
        self.world_window.min = Vec2(
            self.world_window.min.x * w_proportion,
            self.world_window.min.y * h_proportion
        )

        self.old_size = allocation

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

        for obj in self.display_file:
            obj.draw(
                cr,
                graphics.Viewport(
                    region=Rect(min=Vec2(0, 0), max=Vec2(vp_w, vp_h)),
                    window=self.world_window,
                ),
                window_to_viewport
            )

    def on_new_object(self, widget):
        dialog = NewObjectDialog()
        response = dialog.dialog_window.run()

        if response == Gtk.ResponseType.OK:
            if dialog.new_object is not None:
                self.log(f"Object added: <{type(dialog.new_object).__name__}>")
                self.add_object(dialog.new_object)
                self.builder.get_object('drawing_area').queue_draw()
            else:
                self.log("ERROR: invalid object")

    def on_quit(self, widget):
        self.window.close()

    def on_about(self, widget):
        about_dialog = Gtk.AboutDialog(
            None,
            authors=['Arthur Bridi Guazzelli', 'João Paulo T. I. Z.'],
            version='1.3.0',
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
            self.world_window.zoom(0.5)
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.world_window.zoom(2.0)

        widget.queue_draw()

    def on_press_navigation_button(self, widget):
        TRANSFORMATIONS = {
            'nav-move-up': ('translate', Vec2(0, 10)),
            'nav-move-down': ('translate', Vec2(0, -10)),
            'nav-move-left': ('translate', Vec2(-10, 0)),
            'nav-move-right': ('translate', Vec2(10, 0)),
            'nav-rotate-left': ('rotate', -5),
            'nav-rotate-right': ('rotate', 5),
            'nav-zoom-in': ('scale', Vec2(1.1, 1.1)),
            'nav-zoom-out': ('scale', Vec2(0.9, 0.9)),
        }

        op, *args = TRANSFORMATIONS[widget.get_name()]

        for obj in self.selected_objs():
            if op == 'translate':
                obj.translate(*args)

            elif op == 'scale':
                obj.scale(*args)

            elif op == 'rotate':
                try:
                    abs_x = int(self.builder.get_object('rotation-ref-x').get_text())
                    abs_y = int(self.builder.get_object('rotation-ref-y').get_text())
                except:
                    abs_x = 0
                    abs_y = 0

                ref = {
                    RotationRef.CENTER: obj.centroid,
                    RotationRef.ORIGIN: Vec2(0, 0),
                    RotationRef.ABSOLUTE: Vec2(float(abs_x), float(abs_y)),
                }[self.rotation_ref]

                obj.rotate(*args, ref)

        self.window.queue_draw()

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

    def on_toggle_fixed_window(self, checkbox: Gtk.ToggleButton):
        editable = checkbox.get_active()
        for widget_id in ['window-width', 'window-height']:
            widget = self.builder.get_object(widget_id)
            widget.set_editable(editable)
            widget.set_can_focus(editable)

    def on_change_rotation_ref(self, widget: Gtk.RadioButton):
        for w in widget.get_group():
            if w.get_active():
                self.rotation_ref = {
                    'rotate-ref-obj-center': RotationRef.CENTER,
                    'rotate-ref-origin': RotationRef.ORIGIN,
                    'rotate-ref-abs': RotationRef.ABSOLUTE,
                }[w.get_name()]
                if w.get_name() == 'rotate-ref-abs':
                    self.builder.get_object('rotation-ref-x').set_editable(True)
                    self.builder.get_object('rotation-ref-y').set_editable(True)

    def on_new_file(self, item):
        self.log('NEW FILE')
        # Translate world_window center to (0, 0) and wipe display_file
        self.display_file.clear()
        self.object_store.clear()
        self.current_file = None
        self.builder.get_object('drawing_area').queue_draw()

    def on_open_file(self, item):
        file_chooser = Gtk.FileChooserDialog(
            title='Open File',
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
        )

        filter = Gtk.FileFilter()
        filter.set_name('CG OBJ')
        filter.add_pattern('*.obj')
        file_chooser.add_filter(filter)

        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            self.log('OPEN FILE:')
            path = file_chooser.get_filename()
            self.log(path)
            file = open(path)
            contents = file.read()
            scene = ObjCodec.decode(contents)
            self.display_file.clear()
            self.object_store.clear()
            for obj in scene.objs:
                self.add_object(obj)

            self.log(f'{contents}\n')
            file.close()
            self.current_file = path
            self.builder.get_object('drawing_area').queue_draw()

        file_chooser.destroy()

    def on_save_file(self, item):
        label = item.get_label()
        if label == 'gtk-save' and self.current_file is not None:
            file = open(self.current_file, 'w+')
            scene = Scene(window=self.world_window, objs=self.display_file)
            contents = ObjCodec.encode(scene)
            file.write(contents)
            file.close()

        elif label == 'gtk-save-as' or self.current_file is None:
            file_chooser = Gtk.FileChooserDialog(
                title='Save File',
                parent=self.window,
                action=Gtk.FileChooserAction.SAVE,
                buttons=(
                    Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_SAVE_AS, Gtk.ResponseType.OK
                )
            )

            filter = Gtk.FileFilter()
            filter.set_name('CG OBJ')
            filter.add_pattern('*.obj')
            file_chooser.add_filter(filter)

            file_chooser.set_current_name('untitled.obj')

            response = file_chooser.run()
            if response == Gtk.ResponseType.OK:
                if label == 'gtk-save':
                    self.log('SAVE FILE:')
                elif label == 'gtk-save-as':
                    self.log('SAVE AS FILE:')
                path = file_chooser.get_filename()
                self.log(path)
                file = open(path, 'w+')
                scene = Scene(window=self.world_window, objs=self.display_file)
                contents = ObjCodec.encode(scene)
                file.write(contents)
                file.close()
                self.current_file = path
            file_chooser.destroy()

    def on_clicked_rotate_window(self, widget: Gtk.Button):
        self.normalize(angle=int(self.builder.get_object('window-rot-entry').get_text()))

    def normalize(self, angle: float):
        print('self.normalize:')
        window_size = (self.world_window.width, self.world_window.height)
        print(f'window: {self.world_window}')
        normalized = [
            obj.normalize(angle, window=self.world_window)
            for obj in self.display_file
        ]


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        builder = Gtk.Builder.new_from_file('ui/mainwindow.ui')

        self.window = builder.get_object('main_window')

        builder.connect_signals(MainWindowHandler(builder))
