#!/bin/bash
## An executable file that will install the required software

red="\e[1;31m"  # Red B
blue="\e[1;34m" # Blue B
green="\e[0;32m"
bwhite="\e[47m" # white background
rst="\e[0m"     # Text reset
## @value current directory path
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

main(){
     apt-get update
     apt-get install python-socketio
     apt-get install redis-server
     apt-get install python-gevent
     apt-get install python-sqlalchemy
     apt-get install python-MySQLdb
     apt-get install sqlite3 libsqlite3-dev
}

main