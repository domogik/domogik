#!/bin/bash
wget -qO - http://wgetpaste.zlin.dk/wgetpaste-2.18.bz2 | bunzip2 - > /usr/bin/wgetpaste && chmod +x /usr/bin/wgetpaste
rm "$0"
