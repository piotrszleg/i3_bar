# Python I3 Bar

Opinionated i3 window manager bar dedicated for small laptops.

Currently displays workspaces, highlights active workspace, shows workspace windows in its tooltip and shows time. When time label is clicked it switches to date. It also stays on top and independent of workspaces as you'd expect from a bar window.

Written using i3ipc and gtk, should be also compatible with swaywm.

# Setup
1. Open ~/.config/i3/config".
2. Comment out the stuff related to your previous bar.
3. Add the following line:
```
exec_always --no-startup-id "<path to bar file>"
```
4. Reload i3, by default it can be done using: `$mod+Shift+c`