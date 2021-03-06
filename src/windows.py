from enum import auto, Enum

import gi
from gi.repository import Gtk, Gdk

from clipping import LineClippingMethod
from graphics import (
    GraphicObject,
    Line,
    Point,
    Polygon,
    Curve,
    Rect,
    Vec2,
    Window,
)
from graphics3d import GraphicObject3D, Vec3
from cgcodecs import load_scene, save_scene
from scene import Scene
from transformations import rotation_matrix, viewport_matrix

gi.require_version('Gtk', '3.0')
gi.require_foreign('cairo')


NB_PAGES = {
    0: 'point',
    1: 'line',
    2: 'polygon',
    3: 'curve',
}

BUTTON_EVENTS = {
    1: 'left',
    2: 'middle',
    3: 'right',
}


def entry_text(handler, entry_id: str) -> str:
    return handler.builder.get_object(entry_id).get_text()


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
        name = entry_text(self, 'entry_name')

        if NB_PAGES[page_num] == 'point':
            x = float(entry_text(self, 'entryX'))
            y = float(entry_text(self, 'entryY'))

            self.dialog.new_object = Point(Vec2(x, y), name=name)
        elif NB_PAGES[page_num] == 'line':
            y2 = float(entry_text(self, 'entryY2'))
            x1 = float(entry_text(self, 'entryX1'))
            y1 = float(entry_text(self, 'entryY1'))
            x2 = float(entry_text(self, 'entryX2'))

            self.dialog.new_object = Line(
                Vec2(x1, y1),
                Vec2(x2, y2),
                name=name
            )
        elif NB_PAGES[page_num] == 'polygon':
            if len(self.vertices) >= 3:
                filled = self.builder.get_object('switch_filled').get_active()

                self.dialog.new_object = Polygon(
                    self.vertices,
                    name=name,
                    filled=filled
                )
        elif NB_PAGES[page_num] == 'curve':
            if self.builder.get_object('btn_bezier').get_active():
                type = 'bezier'
            elif self.builder.get_object('btn_b-spline').get_active():
                type = 'b-spline'

            if len(self.vertices) >= 4:
                self.dialog.new_object = Curve.from_control_points(
                    self.vertices,
                    type=type,
                    name=name,
                )
        else:
            raise ValueError('No page with given index.')

        window.destroy()

    def on_cancel(self, widget):
        window = self.builder.get_object('new_object_window')
        window.destroy()

    def on_add_point(self, widget):
        notebook = self.builder.get_object('notebook1')
        page_num = notebook.get_current_page()
        vertice_store = self.builder.get_object('vertice_store')

        if NB_PAGES[page_num] == 'polygon':
            x = float(entry_text(self, 'entryX3'))
            y = float(entry_text(self, 'entryY3'))
        elif NB_PAGES[page_num] == 'curve':
            x = float(entry_text(self, 'entryX4'))
            y = float(entry_text(self, 'entryY4'))

        vertice_store.append([x, y, 1])
        self.vertices.append(Vec2(x, y))

    def on_switch_filled_active(self, widget, active: bool):
        label_wireframe = self.builder.get_object('label_wireframe')
        label_filled = self.builder.get_object('label_filled')
        if widget.get_active():
            label_wireframe.set_markup(
                '<span weight="normal">Wireframe</span>'
            )
            label_filled.set_markup('<span weight="bold">Filled</span>')
        else:
            label_wireframe.set_markup('<span weight="bold">Wireframe</span>')
            label_filled.set_markup('<span weight="normal">Filled</span>')


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
        self.scene = Scene()
        self.output_buffer = builder.get_object('outputbuffer')
        self.press_start = None
        self.old_size = None
        self.rotation_ref = RotationRef.CENTER
        self.current_file = None
        self.clipping_method = LineClippingMethod.COHEN_SUTHERLAND
        self.pressed_keys = set()

        # 3D Tests
        obj = GraphicObject3D(
            vertices=[
                Vec3(0, 0, 0, ),
                Vec3(0, 0, 1, ),
                Vec3(1, 0, 1, ),
                Vec3(1, 0, 0, ),

                Vec3(0, 0, 0, ),
                Vec3(0, 1, 0, ),
                Vec3(1, 1, 0, ),
                Vec3(1, 0, 0, ),

                Vec3(0, 0, 0, ),
                Vec3(0, 0, 1, ),
                Vec3(0, 1, 1, ),
                Vec3(0, 1, 0, ),

                Vec3(0, 0, 0, ),
                Vec3(0, 0, 1, ),

                Vec3(0, 0, 1, ),
                Vec3(0, 1, 1, ),
                Vec3(1, 1, 1, ),
                Vec3(1, 0, 1, ),

                Vec3(0, 0, 1, ),
                Vec3(0, 1, 1, ),

                Vec3(0, 1, 1, ),
                Vec3(1, 1, 1, ),
                Vec3(1, 1, 0, ),
                Vec3(0, 1, 0, ),
            ],
            name='hmmm',
        )

        obj.rotate(30, 30, 30, reference=obj.centroid)

        self.add_object(obj)

    def log(self, msg: str):
        self.output_buffer.insert_at_cursor(f'{msg}\n')
        scrollwindow = self.builder.get_object('output_scrollwindow')
        adjustment = scrollwindow.get_vadjustment()
        adjustment.set_value(adjustment.get_upper())

    def on_destroy(self, *args):
        self.window.get_application().quit()

    def on_resize(self, widget: Gtk.Widget, allocation: Gdk.Rectangle):
        if self.scene.window is None:
            w, h = allocation.width, allocation.height
            self.old_size = allocation
            self.scene.window = Window(
                Vec2(-w / 2, -h / 2),
                Vec2(w / 2, h / 2)
            )

        w_proportion = allocation.width / self.old_size.width
        h_proportion = allocation.height / self.old_size.height

        self.scene.window.max = Vec2(
            self.scene.window.max.x * w_proportion,
            self.scene.window.max.y * h_proportion
        )
        self.scene.window.min = Vec2(
            self.scene.window.min.x * w_proportion,
            self.scene.window.min.y * h_proportion
        )
        self.old_size = allocation

        self.scene.update_ndc()

    def viewport(self) -> Rect:
        widget = self.builder.get_object('drawing_area')
        return Rect(
            min=Vec2(0, 0),
            max=Vec2(
                widget.get_allocated_width(),
                widget.get_allocated_height(),
            )
        ).with_margin(10)

    def on_draw(self, widget, cr):
        viewport = self.viewport()
        vp_matrix = viewport_matrix(viewport)

        cr.set_line_width(2.0)
        cr.paint()
        cr.set_source_rgb(0.8, 0.0, 0.0)

        for obj in self.scene.objs:
            clipped = obj.clipped(
                method=self.clipping_method
            )
            if clipped:
                clipped.draw(cr, vp_matrix)

        cr.set_source_rgb(0.4, 0.4, 0.4)
        viewport.draw(cr, vp_matrix)

    def on_new_object(self, widget):
        dialog = NewObjectDialog()
        response = dialog.dialog_window.run()

        if response == Gtk.ResponseType.OK:
            if dialog.new_object is not None:
                self.add_object(dialog.new_object)
                self.builder.get_object('drawing_area').queue_draw()
            else:
                self.log('ERROR: invalid object')

    def on_quit(self, widget):
        self.window.close()

    def on_about(self, widget):
        about_dialog = Gtk.AboutDialog(
            None,
            authors=['Arthur Bridi Guazzelli', 'João Paulo T. I. Z.'],
            version='1.5.0',
            program_name='Rudolph'
        )
        about_dialog.run()
        about_dialog.close()

    def on_key_press(self, widget, event):
        '''
        Returns: False if event can propagate, True otherwise.
        '''
        DIRECTIONS = {
            Gdk.KEY_Up: Vec2(0, -10),
            Gdk.KEY_Down: Vec2(0, 10),
            Gdk.KEY_Left: Vec2(10, 0),
            Gdk.KEY_Right: Vec2(-10, 0),
        }

        self.pressed_keys |= {event.keyval}

        for key in self.pressed_keys:
            if key in DIRECTIONS:
                self.world_window.offset(DIRECTIONS[key])

        self.window.queue_draw()

        return True

    def on_key_release(self, widget, event):
        '''
        Returns: False if event can propagate, True otherwise.
        '''

        self.pressed_keys -= {event.keyval}

        return False

    def on_button_press(self, widget, event):
        if BUTTON_EVENTS[event.button] == 'left':
            # register x, y
            self.press_start = Vec2(-event.x, event.y)
            self.dragging = True

    def on_motion(self, widget, event):
        def viewport_to_window(v: Vec2):
            viewport = self.viewport()

            return Vec2(
                (v.x / viewport.width) * self.scene.window.width,
                (v.y / viewport.height) * self.scene.window.height
            )

        # register x, y
        # translate window
        if self.dragging:
            current = Vec2(-event.x, event.y)
            delta = viewport_to_window(current - self.press_start)

            window = self.scene.window

            m = rotation_matrix(window.angle)

            delta = delta @ m

            self.scene.translate_window(delta)
            self.press_start = current
            widget.queue_draw()

    def on_button_release(self, widget, event):
        if BUTTON_EVENTS[event.button] == 'left':
            self.dragging = False

    def on_scroll(self, widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self.scene.zoom_window(0.5)
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.scene.zoom_window(2.0)

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
        if op == 'translate':
            args[0] = (
                args[0] @ rotation_matrix(self.scene.window.angle)
            )

        for obj in self.selected_objs():
            if op == 'translate':
                obj.translate(*args)
            elif op == 'scale':
                obj.scale(*args)
            elif op == 'rotate':
                try:
                    abs_x = int(entry_text(self, 'rotation-ref-x'))
                    abs_y = int(entry_text(self, 'rotation-ref-y'))
                except ValueError:
                    abs_x = 0
                    abs_y = 0

                ref = {
                    RotationRef.CENTER: obj.centroid,
                    RotationRef.ORIGIN: Vec2(0, 0),
                    RotationRef.ABSOLUTE: Vec2(float(abs_x), float(abs_y)),
                }[self.rotation_ref]

                if isinstance(obj, GraphicObject3D):
                    obj.rotate(args[0], 0, 0, ref)
                else:
                    obj.rotate(*args, ref)
            obj.update_ndc(self.scene.window)

        self.window.queue_draw()

    def selected_objs(self):
        tree = self.builder.get_object('tree-displayfiles')
        store, rows = tree.get_selection().get_selected_rows()

        return (self.scene.objs[int(str(index))] for index in rows)

    def add_object(self, obj: GraphicObject):
        self.log(f'Object added: <{type(obj).__name__}>')
        self.scene.add_object(obj)
        self.add_to_treeview(obj)

    def add_to_treeview(self, obj: GraphicObject):
        self.object_store.append([
            obj.name,
            str(f'<{type(obj).__name__}>')
        ])

    def remove_selected_objects(self, widget):
        tree = self.builder.get_object('tree-displayfiles')
        store, paths = tree.get_selection().get_selected_rows()

        for path in reversed(paths):
            iter = store.get_iter(path)
            store.remove(iter)
            self.scene.remove_objects([int(str(path))])
        self.window.queue_draw()

    def on_change_rotation_ref(self, widget: Gtk.RadioButton):
        for w in widget.get_group():
            if w.get_active():
                self.rotation_ref = {
                    'rotate-ref-obj-center': RotationRef.CENTER,
                    'rotate-ref-origin': RotationRef.ORIGIN,
                    'rotate-ref-abs': RotationRef.ABSOLUTE,
                }[w.get_name()]
                if w.get_name() == 'rotate-ref-abs':
                    for _id in 'rotation-ref-x', 'rotation-ref-y':
                        self.builder.get_object(_id).set_editable(True)

    def on_new_file(self, item):
        self.log('NEW FILE')
        old_window = self.scene.window
        self.scene = Scene(window=old_window)
        self.object_store.clear()
        self.current_file = None
        self.builder.get_object('drawing_area').queue_draw()

    def on_open_file(self, item):
        file_chooser = self.new_file_chooser(Gtk.FileChooserAction.OPEN)

        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            path = file_chooser.get_filename()
            self.log(f'OPEN FILE: {path}')

            old_window = self.scene.window
            self.scene = load_scene(path)
            self.scene.window = old_window
            self.scene.update_ndc()

            self.object_store.clear()
            for obj in self.scene.objs:
                self.add_to_treeview(obj)

            self.current_file = path
            self.builder.get_object('drawing_area').queue_draw()
        file_chooser.destroy()

    def on_save_file(self, item):
        label = item.get_label()
        if label == 'gtk-save' and self.current_file is not None:
            self.save_scene()

        elif label == 'gtk-save-as' or self.current_file is None:
            file_chooser = self.new_file_chooser(Gtk.FileChooserAction.SAVE)

            response = file_chooser.run()
            if response == Gtk.ResponseType.OK:
                path = file_chooser.get_filename()
                self.log(path)
                self.save_scene()
                self.current_file = path
            file_chooser.destroy()

    def save_scene(self):
        save_scene(self.scene, self.current_file)
        self.log(f'SAVE FILE: {self.current_file}')

    def new_file_chooser(self, action):
        file_chooser = Gtk.FileChooserDialog(
            parent=self.window,
            action=action,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )

        if action == Gtk.FileChooserAction.OPEN:
            file_chooser.title = 'Open file'

        elif action == Gtk.FileChooserAction.SAVE:
            file_chooser.title = 'Save file'
            file_chooser.set_current_name('untitled.obj')

        filter = Gtk.FileFilter()
        filter.set_name('CG OBJ')
        filter.add_pattern('*.obj')
        file_chooser.add_filter(filter)

        return file_chooser

    def on_clicked_rotate_window(self, widget: Gtk.Button):
        rotation_angle = int(entry_text(self, 'window-rot-entry'))
        self.scene.window.angle += rotation_angle
        for obj in self.scene.objs:
            obj.update_ndc(self.scene.window)
        self.log(f'Window rotated {rotation_angle} degrees')
        self.window.queue_draw()

    def on_change_clipping_method(self, widget: Gtk.ComboBoxText):
        METHODS = {
            'Cohen Sutherland': LineClippingMethod.COHEN_SUTHERLAND,
            'Liang Barsky': LineClippingMethod.LIANG_BARSKY,
        }
        self.clipping_method = METHODS[widget.get_active_text()]
        self.window.queue_draw()


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        builder = Gtk.Builder.new_from_file('ui/mainwindow.ui')

        self.window = builder.get_object('main_window')

        builder.connect_signals(MainWindowHandler(builder))
