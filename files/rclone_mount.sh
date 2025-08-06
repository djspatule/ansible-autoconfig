#!/bin/bash

#Bash script to run rclone and sync my google drives automatically. 

# --vfs-cache-mode writes = These flags control the VFS file caching options. File caching is necessary to make the VFS layer appear compatible with a normal file system. It can be disabled at the cost of some compatibility. For example you'll need to enable VFS caching if you want to read and write simultaneously to a file. 
# mount = the most reliable option to do bidirectionnal sync.

rclone --vfs-cache-mode writes mount Google\ Drive\ Perso: ~/Google\ Drive\ Perso &
