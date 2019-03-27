import gi
gi.require_version('Gtk', '3.0')
gi.require_foreign("cairo")
from gi.repository import Gtk
from graphics import Point, Line, Polygon, Vec2


nb_pages = {
    0: "point",
    1: "line",
    2: "polygon"
}


class NewObjectDialogHandler:
    def __init__(self, dialog, builder):
        self.dialog = dialog
        self.builder = builder
        self.vertices = []

    def on_ok(self, widget):
        window = self.builder.get_object("new_object_window")
        notebook = self.builder.get_object("notebook1")

        page_num = notebook.get_current_page()

        name = self.builder.get_object("entry_name").get_text()
        if nb_pages[page_num] == "point":
            x = self.builder.get_object("entryX").get_text()
            y = self.builder.get_object("entryY").get_text()

            self.dialog.new_object = Point(float(x), float(y), name=name)

        elif nb_pages[page_num] == "line":
            x1 = self.builder.get_object("entryX1").get_text()
            y1 = self.builder.get_object("entryY1").get_text()
            x2 = self.builder.get_object("entryX2").get_text()
            y2 = self.builder.get_object("entryY2").get_text()

            self.dialog.new_object = Line(
                float(x1), float(y1),
                float(x2), float(y2),
                name=name
            )

        elif nb_pages[page_num] == "polygon":
            if len(self.vertices) >= 3:
                self.dialog.new_object = Polygon(self.vertices, name=name)
        else:
            raise ValueError("No page with given index.")

        window.destroy()

    def on_cancel(self, widget):
        window = self.builder.get_object("new_object_window")
        window.destroy()

    def on_add_point(self, widget):
        vertice_store = self.builder.get_object("vertice_store")

        x = float(self.builder.get_object("entryX3").get_text())
        y = float(self.builder.get_object("entryY3").get_text())

        vertice_store.append([x, y, 1])
        self.vertices.append(Vec2(x, y))


class NewObjectDialog(Gtk.Dialog):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

        self.builder = Gtk.Builder.new_from_file("ui/newobjectdialog.ui")
        self.builder.connect_signals(
            NewObjectDialogHandler(self, self.builder)
        )
        self.new_object = None

        self.dialog_window = self.builder.get_object("new_object_window")


class MainWindowHandler:
    def __init__(self, builder):
        self.builder = builder
        self.window = self.builder.get_object("main_window")
        self.object_store = self.builder.get_object("object_store")
        self.display_file = []

    def on_destroy(self, *args):
        Gtk.main_quit()

    def on_draw(self, widget, cr):
        print(f"{len(self.display_file)} objects to draw")
        cr.set_line_width(2.0)
        cr.paint()
        cr.set_source_rgb(0.8, 0.0, 0.0)

        for object in self.display_file:
            if object:
                object.draw(cr)

        cr.stroke()

    def on_new_object(self, widget):
        dialog = NewObjectDialog()
        response = dialog.dialog_window.run()

        if response == Gtk.ResponseType.OK:
            self.display_file.append(dialog.new_object)
            self.object_store.append([
                dialog.new_object.name,
                str(f"<{type(dialog.new_object).__name__}>")
            ])

            self.builder.get_object("drawing_area").queue_draw()

        elif response == Gtk.ResponseType.CLOSE:
            print("CANCEL")

    def on_quit(self, widget):
        self.window.close()

    def on_about(self, widget):
        about_dialog = Gtk.AboutDialog(
            None,
            authors=["Arthur Bridi Guazzelli", "João Paulo T. I. Z."],
            version="1.0.0",
            program_name="Rudolph"
        )
        about_dialog.run()


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        builder = Gtk.Builder.new_from_file("ui/mainwindow.ui")

        self.window = builder.get_object("main_window")

        builder.connect_signals(MainWindowHandler(builder))
