import gi
import sys
gi.require_version('Gtk', '3.0')
gi.require_foreign('cairo')
from gi.repository import Gtk

from windows import MainWindow


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id='ufsc.cg.rudolph',
                         **kwargs)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_activate(self):
        if not self.window:
            main_window = MainWindow(application=self, title='Rudolph')
            self.window = main_window.window

        self.window.present()


if __name__ == '__main__':
    app = Application()
    app.run(sys.argv)
