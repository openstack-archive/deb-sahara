#!/bin/bash

if [[ $1 == *"Ubuntu"* ]]; then
    sudo apt-get install --force-yes -y mysql-client libmysql-java
elif [[ $1 == *"CentOS"* ]] || [[ $1 == *"Red Hat Enterprise Linux"* ]]; then
    sudo yum install -y mysql mysql-connector-java
elif [[ $1 == *"SUSE"* ]]; then
    sudo zypper install mysql-community-server-client mysql-connector-java
else
    echo "Unknown distribution"
    exit 1
fi
