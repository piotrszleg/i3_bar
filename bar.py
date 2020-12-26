import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk
from gi.repository import Gtk

from functools import partial
from i3ipc import Connection, Event
import threading, queue
from time import sleep

q = queue.Queue()

BUTTON_SIZE=30

class Bar():
    def __init__(self):
        super().__init__()
        CSS = b"""
        #toplevel {
            background-color: rgba(0, 0, 0, 0);
            min-height:0px;
            padding:0;
            margin:0;
        }
        button {
            background-image: none;
            background-color: rgba(0, 0, 0, 0.7);
            padding:0px;
            margin:0px;
            border:0px;
            min-height:0px;
        }
        """

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(CSS)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        window = Gtk.Window(title="pybar", name="toplevel")
        screen = window.get_screen()
        visual = screen.get_rgba_visual()
        window.set_visual(visual)
        self.box=Gtk.Box(spacing=0)
        window.add(self.box)
        window.show_all()
        window.connect("destroy", Gtk.main_quit)
        self.window=window
        self.screen=screen
    
    def motion(self, event):
        if not self.down:
            return
        x=event.x+self.winfo_x()-self.offset_x
        y=event.y+self.winfo_y()-self.offset_y
        self.geometry(f"+{x}+{y}")

    def mouse_down(self, event):
        self.down=True
        self.offset_x=event.x
        self.offset_y=event.y

    def mouse_up(self, _):
        self.down=False

    def update(self):
        Gtk.main_iteration()

    @staticmethod
    def filter_for_tk(text):
        return "".join([text[j] for j in range(len(text)) if ord(text[j]) in range(65536)])

    def update_buttons(self, workspaces, callback):
        for child in self.box.get_children():
            self.box.remove(child)
        for workspace in workspaces:
            button1 = Gtk.Button(label=self.filter_for_tk(workspace.name or ""))
            button1.set_margin_bottom(0)
            button1.set_margin_top(0)
            button1.num=workspace.num
            
            button1.connect("clicked", lambda button: callback(button.num))
            self.box.pack_start(button1, True, True, 0)

        width=len(workspaces)*BUTTON_SIZE
        height=BUTTON_SIZE
        self.box.set_size_request(width, height)
        self.window.move(self.screen.get_width()-width, 0)
        self.window.set_size_request(width, height)
        self.window.set_resizable(False)
        self.window.show_all()

class I3Thread(threading.Thread):
    def __init__(self, queue):
        self.queue=queue
        self.i3 = Connection()
        super().__init__()

    def i3_update(self):
        self.queue.put(self.i3.get_workspaces())
    
    def run(self):
        self.i3.on(Event.WORKSPACE_FOCUS, (lambda _, __: self.i3_update()))
        # TOFIX: actually wait for the app
        sleep(1)
        self.i3.command("[title=\"pybar\"] floating enable, sticky enable")
        self.i3_update()
        self.i3.main()
    
    def switch_to_workspace(self, workspace_index):
        self.i3.command(f"move container to workspace {workspace_index}")
        self.i3.command(f"workspace {workspace_index}")

bar=Bar()
i3=I3Thread(q)
i3.start()
while True:
    bar.update()
    try:
        bar.update_buttons(q.get_nowait(), i3.switch_to_workspace)
    except queue.Empty:
        pass