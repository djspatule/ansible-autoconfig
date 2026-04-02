# Ansible Autoconfig
![Ansible Logo](https://www.learnlinux.tv/wp-content/uploads/2020/12/ansible-e1607524003363.png)

This repository contains the code that Jay Lacroix (LearnLinuxTV) worked on from the Ansible Desktop tutorial [here](https://youtu.be/gIDywsGBqf4).

It was improved with the Ansible-pull tutorial and then coding was improved with ChatGPT's Codex.

## Usage
run with 
>   sudo ansible-pull -U https://github.com/djspatule/ansible-autoconfig.git --vault-password-file ~/secret.txt -C main

test with (to avoid dealing with Pull Requests)
> sudo ansible-pull -U /chemin/vers/ton/repo_local -d /tmp/ansible-pull-test local.yml
> sudo ansible-playbook -i "localhost," -c local local.yml --check #remember that ansible-pull is just a wrapper for ansible-playbook....And the check option allows to test on a system without implementing anything ('dry run').

# ToDo

[X] install espanso's latest .deb & move espanso "config" with FR keyboard from files to ~/.config/espanso/config/default.yml
[X] protect against useless downloads (fonts, etc.) to limit the number of "changes" when running


[] automate the execution of a script stating "espanso stop; sleep 1; espanso start" whenever a new USB keyboard is connected.
[] differentiate a desktop use-case on Gnome from a server use case (vars, tasks, etc.) both running a "base" set of tasks
[] try to "import" the files for the GUI apps (InSync, Betterbird, LibreOffice, etc.)
[] Adjust locale when needed in the system settings (for french numbers and dates)  
[] find inspiration in jaylacroix's code : https://github.com/LearnLinuxTV/personal_ansible_desktop_configs/tree/main and eventually omakub's code
[] use tags to only test/execute parts of the script... that should accelerate dev and limit need for protection against downloads.

## Guidelines for coding agents
### Objectives

- Use ansible-pull (sudo ansible-pull -U https://github.com/djspatule/ansible-autoconfig.git --vault-password-file ~/secret.txt -C main) to automate the set-up of any of my family’s computer if they ever have to be reinstalled from scratch (on the same or different hardware).
- The set-up must be idem-potent so that it can be set to run automatically once a day on each of these machine (via a crontab job or else)
- I need to be able to “test” on a virtual machine. My dotfiles are currently too specific to Omarchy and managed with stow (https://github.com/djspatule/omarchy-dotfiles).
- Use this for inspiration of structuration, etc. https://github.com/LearnLinuxTV/personal_ansible_desktop_configs/tree/main
- I’m writing this code also as an opportunity to learn about ansible, GNU/linux, networking, etc.
- I would ideally like to lay the foundations of an auto-config script that will be still valid and usable in 20 years….(comment your code profusely)
- The short term priority is to work on the server

### Roles :

- Server (Serverannah) destined to become a homelab that runs Ubuntu server 25.10 (headless Optiplex 3070, accessed via SSH) : It is running both natively (on bare metal) an Nginx server to host 3 websites (including a complex wordpress) and more to come. It's also DNS Filtering with pi-hole (installed on bare metal). last, it's running multiple docker services such as frigate for cameras, N8N, Odoo, bentopdf, Plex, Timeshift (to secure backups on 1 master and 3 different external disks copies), Nextcloud (to manage my data and make it accessible to the whole family) and the like. For now, those functions are managed on a raspi 4B (192.168.1.100) that should be retired soon. You don’t have to keep on serverannah things as they were on the raspi. It’s a good opportunity to “improve”.
- Kids are running Linux Mint (xfce but switch to cinnamon is envisaged) on a very old macbook. Their goal is gaming and learning. Parental control has to be strict
- “Mac” is my wife’s computer (not much to set-up there, she mostly works in a browser + GDrive and Spotify)
- Laptop is on Omarchy (hyprland) but could be switched to KDE or Gnome on Arch or even be switched to an Debian/Ubuntu distro

### Extra instructions

- ask whenever in doubt and ask for feedback (i can run commands for you, etc.)
- verify your work as much as possible
- remember as much as you can of these instructions and the other instructions to come
- Create a “guidelines.md” inside the directory to describe everything the project is about, how it works, terminal commands, etc. Templates on github….

### Do not do

- do not change code without explaining
- do not change multiples files at once when not strictly connected to the same taks/objective at hand
