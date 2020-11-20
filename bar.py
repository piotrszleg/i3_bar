import tkinter as tk
from functools import partial
from i3ipc import Connection, Event
import threading, queue
from time import sleep

i3 = Connection()
q = queue.Queue()
ui = tk.Tk()
ui.title("pybar")
offset_x=0
offset_y=0
down=False

def motion(event):
    if not down:
        return
    x=event.x+ui.winfo_x()-offset_x
    y=event.y+ui.winfo_y()-offset_y
    ui.geometry(f"+{x}+{y}")

def mouse_down(event):
    global down, offset_x, offset_y
    down=True
    offset_x=event.x
    offset_y=event.y

def mouse_up(_):
    global down
    down=False

ui.bind('<Motion>', motion)
ui.bind('<ButtonPress>', mouse_down)
ui.bind('<ButtonRelease>', mouse_up)

def switch_to_workspace(workspace_index):
    i3.command(f"move container to workspace {workspace_index}")
    i3.command(f"workspace {workspace_index}")

def filter_for_tk(text):
    return "".join([text[j] for j in range(len(text)) if ord(text[j]) in range(65536)])

def update_ui(workspaces):
    for child in ui.winfo_children():
        child.destroy()
    for workspace in workspaces:
        if workspace.focused:
            state="disabled"
        else:
            state="normal"
        callback=partial(switch_to_workspace, workspace.num)
        button = tk.Button(ui, pady=2, padx=5, text=filter_for_tk(workspace.name or ""), command = callback, state=state)
        button.pack(side="left")

def i3_update():
    q.put(i3.get_workspaces())

def i3_thread():
    i3.on(Event.WORKSPACE_FOCUS, (lambda _, __: i3_update()))
    # TOFIX: actually wait for the app
    sleep(1)
    i3.command("[title=\"pybar\"] floating enable, sticky enable")
    i3_update()
    i3.main()

threading.Thread(target=i3_thread).start()
while True:
    ui.update()
    try:
        update_ui(q.get_nowait())
    except queue.Empty:
        pass