# Ansible Autoconfig
![Ansible Logo](https://www.learnlinux.tv/wp-content/uploads/2020/12/ansible-e1607524003363.png)

This repository contains the code that Jay Lacroix (LearnLinuxTV) worked on from the Ansible Desktop tutorial [here](https://youtu.be/gIDywsGBqf4).

It was improved with the Ansible-pull tutorial and then coding was improved with ChatGPT's Codex.

## Usage
run with 
>   sudo ansible-pull -U https://github.com/djspatule/ansible-autoconfig.git --vault-password-file ~/secret.txt -C main

# ToDo

[X] install espanso's latest .deb & move espanso "config" with FR keyboard from files to ~/.config/espanso/config/default.yml
[X] protect against useless downloads (fonts, etc.) to limit the number of "changes" when running


[] automate the execution of a script stating "espanso stop; sleep 1; espanso start" whenever a new USB keyboard is connected.
[] differentiate a desktop use-case on Gnome from a server use case (vars, tasks, etc.) both running a "base" set of tasks
[] try to "import" the files for the GUI apps (InSync, Betterbird, LibreOffice, etc.)
[] Adjust locale when needed in the system settings (for french numbers and dates)  
[] find inspiration in jaylacroix's code : https://github.com/LearnLinuxTV/personal_ansible_desktop_configs/tree/main and eventually omakub's code
  [] use tags to only test/execute parts of the script... that should accelerate dev and limit need for protection against downloads.
