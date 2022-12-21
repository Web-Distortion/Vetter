#! /bin/bash

rm -rf amazon.com nonexistent
mm-webrecord amazon.com /usr/bin/google-chrome --disable-fre --no-default-browser-check --no-first-run --window-size=1920,1080 --ignore-certificate-errors --user-data-dir=./nonexistent/$(date +%s%N) https://www.amazon.com/