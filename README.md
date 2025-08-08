# Ansible Autoconfig
![Ansible Logo](https://www.learnlinux.tv/wp-content/uploads/2020/12/ansible-e1607524003363.png)

This repository contains the code that Jay Lacroix (LearnLinuxTV) worked on from the Ansible Desktop tutorial [here](https://youtu.be/gIDywsGBqf4).

It was improved with the Ansible-pull tutorial and then coding was improved with ChatGPT's Codex.

## Usage
run with 
> sudo ansible-pull -U https://github.com/djspatule/ansible-autoconfig.git -C main

Todo
[] move espanso "config" with FR keyboard from files to ~/.config/espanso/config/default.yml

[] protect against useless downloads (fonts, etc.) to limit the number of "changes" when 