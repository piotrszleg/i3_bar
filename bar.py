import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk
from gi.repository import Gtk, GObject

from functools import partial
from i3ipc import Connection, Event
import threading, queue
import time

# forces the time to be displayed in 12h format
import locale
locale.setlocale(locale.LC_TIME, "en_US.utf8")

TITLE="pybar"
SCREEN_PADDING=2
BUTTON_SIZE=28
TIME_WIDTH=70

q = queue.Queue()

class Bar(Gtk.Window):
    def __init__(self):
        super().__init__(title=TITLE, name="toplevel")

        style_provider = Gtk.CssProvider()
        style_provider.load_from_path("style.css")

        self.screen = self.get_screen()

        Gtk.StyleContext.add_provider_for_screen(
            self.screen,
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        visual = self.screen.get_rgba_visual()
        self.set_visual(visual)
        self.box=Gtk.Box(spacing=0)
        self.add(self.box)
        self.show_all()
        self.connect("destroy", Gtk.main_quit)
        self.show_date=False
        self.time_label=None
        GObject.timeout_add(10_000, self.update_time_label)

    def update(self):
        Gtk.main_iteration()

    def new_button(self, name, callback):
        button = Gtk.Button(label=name)
        button.set_margin_bottom(0)
        button.set_margin_top(0)
        button.connect("clicked", lambda _: callback())
        self.box.pack_start(button, True, True, 0)
        return button

    def new_workspace_button(self, name, number, tooltip, callback):
        button = self.new_button(name, lambda: callback(number))
        button.set_tooltip_text(tooltip)
        
    def create_button_for_workspace(self, workspace, callback):
        children=(
            child.name
            for child in workspace.descendants()
            if child.name and child.name!=TITLE)
        tooltip="\n".join(children)
        button = self.new_button(workspace.name or "", lambda: callback(workspace.num))
        button.set_tooltip_text(tooltip)
        
        focused=False
        for child in workspace.descendants():
            # A silly trick I guess?
            # The focused workspace will always contain the bar window,
            # because it's sticky. Other methods didn't work well.
            if child.name==TITLE:
                focused=True
        if focused:
            button.get_style_context().add_class("focused")

    def switch_hour_date(self):
        self.show_date=not self.show_date
        self.update_time_label()

    def update_time_label(self):
        if self.time_label!=None:
            named_tuple = time.localtime() # get struct_time
            if self.show_date:
                time_string = time.strftime("%m/%d/%y", named_tuple)
            else:
                time_string = time.strftime("%H:%M %p", named_tuple)
            self.time_label.set_label(time_string)
            self.show_all()
        return True
    
    def update_buttons(self, containers, callback):
        for child in self.box.get_children():
            self.box.remove(child)
        buttons_count=0
        for container in containers:
            if container.type=="workspace" and container.name!="__i3_scratch":
                self.create_button_for_workspace(container, callback)
                buttons_count+=1
        
        self.time_label=self.new_button("", self.switch_hour_date)
        self.time_label.set_size_request(TIME_WIDTH, BUTTON_SIZE)
        self.update_time_label()

        width=buttons_count*BUTTON_SIZE+TIME_WIDTH
        height=BUTTON_SIZE
        self.box.set_size_request(width, height)
        self.move(self.screen.get_width()-width-SCREEN_PADDING, SCREEN_PADDING)
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

    def on_new_window(self, _, event):
        # when bar window becomes visible 
        if event.container.name==TITLE:    
            # make it floating and sticky
            self.i3.command(f"[title=\"{TITLE}\"] floating enable, sticky enable")
            # send the containers structure to it
            self.i3_update()
            # disable this event handler
            self.i3.off(self.on_new_window)

    def run(self):
        # this event is used to set up the bar window
        self.i3.on(Event.WINDOW_NEW, self.on_new_window)
        def update_on(event):
            self.i3.on(event, (lambda _, __: self.i3_update()))    
        update_on(Event.WORKSPACE)
        update_on(Event.WINDOW_NEW)
        update_on(Event.WINDOW_CLOSE)
        self.i3.main()
    
    def switch_to_workspace(self, workspace_index):
        self.i3.command(f"workspace {workspace_index}")

def run():
    i3=I3Thread(q)
    i3.start()
    bar=Bar()

    while True:
        bar.update()
        try:
            bar.update_buttons(q.get_nowait(), i3.switch_to_workspace)
        except queue.Empty:
            pass

if __name__=="__main__":
    run()