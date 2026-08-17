-- Extra autostart processes.
-- o.launch_on_start("my-service")

hl.on("hyprland.start", function()
  hl.exec_cmd("[workspace 1 silent] " .. o.launch("thunderbird"))
  hl.exec_cmd("[workspace 2 silent] " .. o.launch("chromium"))
  hl.exec_cmd("[workspace 3 silent] " .. o.launch("beeper"))
  hl.exec_cmd("[workspace 4 silent] " .. o.launch("alacritty"))
  hl.exec_cmd("[workspace 6 silent] " .. o.launch("nautilus"))
  hl.exec_cmd(o.launch('bash "$HOME/rclone_mount.sh"'))
  hl.exec_cmd(o.launch('bash "$HOME/serverannah_mount.sh"'))
  hl.exec_cmd(o.launch("kdeconnectd"))
  hl.exec_cmd(o.launch("kdeconnect-indicator"))
end)
