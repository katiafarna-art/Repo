#!/bin/bash

/usr/bin/ps axf | /usr/bin/grep $1 | /usr/bin/grep -v grep | /usr/bin/awk '{print $1}'