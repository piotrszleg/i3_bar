import tkinter as tk
import os
import json
from functools import partial

top = tk.Tk()
top.title("pybar")

def read_workspaces():
    stream = os.popen("i3-msg -t get_workspaces")
    workspaces=json.load(stream)
    return workspaces

def switch_to_workspace(workspace_index):
    os.system(f"i3-msg move container to workspace {workspace_index}")
    os.system(f"i3-msg workspace {workspace_index}")

for workspace in read_workspaces():
    # if workspace["focused"]:
    #     state="disabled"
    # else:
    #     state="normal"
    callback=partial(switch_to_workspace, workspace["num"])
    button = tk.Button(top, text=workspace["name"], command = callback)
    button.pack(side="left")

os.popen("sleep 2 && i3-msg '[title=\"pybar\"] floating enable, sticky enable'")
top.mainloop()