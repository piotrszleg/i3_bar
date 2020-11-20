import tkinter as tk
from functools import partial
from i3ipc import Connection, Event
import threading, queue
from time import sleep

q = queue.Queue()
ui = tk.Tk()
ui.title("pybar")
offset_x=0
offset_y=0
down=False

class Bar(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.bind('<Motion>', self.motion)
        self.bind('<ButtonPress>', self.mouse_down)
        self.bind('<ButtonRelease>', self.mouse_up)
        self.offset_x=0
        self.offset_y=0
        self.down=False
    
    def motion(self, event):
        if not self.down:
            return
        x=event.x+ui.winfo_x()-offset_x
        y=event.y+ui.winfo_y()-offset_y
        ui.geometry(f"+{x}+{y}")

    def mouse_down(self, event):
        self.down=True
        self.offset_x=event.x
        self.offset_y=event.y

    def mouse_up(self, _):
        self.down=False

    @staticmethod
    def filter_for_tk(text):
        return "".join([text[j] for j in range(len(text)) if ord(text[j]) in range(65536)])

    def update_buttons(self, workspaces, callback):
        for child in self.winfo_children():
            child.destroy()
        for workspace in workspaces:
            if workspace.focused:
                state="disabled"
            else:
                state="normal"
            command=partial(callback, workspace.num)
            button = tk.Button(self, pady=2, padx=5, text=self.filter_for_tk(workspace.name or ""), command = command, state=state)
            button.pack(side="left")

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
        print(workspace_index)
        self.i3.command(f"move container to workspace {workspace_index}")
        self.i3.command(f"workspace {workspace_index}")

i3=I3Thread(q)
i3.start()
bar=Bar(ui)
while True:
    ui.update()
    try:
        bar.update_buttons(q.get_nowait(), i3.switch_to_workspace)
    except queue.Empty:
        pass