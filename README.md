# Ansible Autoconfig
![Ansible Logo](https://www.learnlinux.tv/wp-content/uploads/2020/12/ansible-e1607524003363.png)

This repository contains the code that Jay Lacroix (LearnLinuxTV) worked on from the Ansible Desktop tutorial [here](https://youtu.be/gIDywsGBqf4).

It was improved with the Ansible-pull tutorial and then coding was improved with ChatGPT's Codex.

## Usage
run with 
> sudo ansible-pull -U https://github.com/djspatule/ansible-autoconfig.git -C main

Todo
[X] move espanso "config" with FR keyboard from files to ~/.config/espanso/config/default.yml
[X] automate the dynamic install of the most recent version of the package for dependency: libwxgtk3.*-dev
[X] automate the execution of a script stating "espanso stop; sleep 1; espanso start" whenever a new USB keyboard is connected.


[] protect against useless downloads (fonts, etc.) to limit the number of "changes" when running