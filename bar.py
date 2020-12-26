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

class Bar(Gtk.Window):
    def __init__(self):
        super().__init__(title="pybar", name="toplevel")

        style_provider = Gtk.CssProvider()
        style_provider.load_from_path("style.css")

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        self.set_visual(visual)
        self.box=Gtk.Box(spacing=0)
        self.add(self.box)
        self.show_all()
        self.connect("destroy", Gtk.main_quit)
        self.screen=screen
    
    def update(self):
        Gtk.main_iteration()

    @staticmethod
    def filter_for_tk(text):
        return ("".join([text[j] for j in range(len(text)) if ord(text[j]) in range(65536)]))

    def update_buttons(self, workspaces, callback):
        for child in self.box.get_children():
            self.box.remove(child)
        buttons_count=0
        for workspace in workspaces:
            if workspace.type!="workspace" or workspace.name=="__i3_scratch":
                continue
            button1 = Gtk.Button(label=self.filter_for_tk(workspace.name or ""))
            button1.set_margin_bottom(0)
            button1.set_margin_top(0)
            button1.num=workspace.num
            
            children="\n".join((self.filter_for_tk(child.name or "") for child in workspace.descendants() if child.name))
            button1.set_tooltip_text(children)
            
            button1.connect("clicked", lambda button: callback(button.num))
            self.box.pack_start(button1, True, True, 0)
            
            buttons_count+=1
        
        width=buttons_count*BUTTON_SIZE
        height=BUTTON_SIZE
        self.box.set_size_request(width, height)
        self.move(self.screen.get_width()-width, 0)
        self.set_size_request(width, height)
        self.set_resizable(False)
        self.show_all()

class I3Thread(threading.Thread):
    def __init__(self, queue):
        self.queue=queue
        self.i3 = Connection()
        super().__init__()

    def i3_update(self):
        self.queue.put(self.i3.get_tree().descendants())
    
    def run(self):
        self.i3.on(Event.WORKSPACE, (lambda _, __: self.i3_update()))
        self.i3.on(Event.WINDOW_NEW, (lambda _, __: self.i3_update()))
        self.i3.on(Event.WINDOW_CLOSE, (lambda _, __: self.i3_update()))
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