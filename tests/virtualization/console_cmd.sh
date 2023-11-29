#!/usr/bin/bash

name=$1
passwd=$2
cmd=$3
expect <<-SSHEOF
    spawn virsh console $name
        send "\r"
        expect "login:"
        send "root\r"
        expect "assword:"
        send "$passwd\r"
        expect "*]#"
        send "$cmd\r"
        expect "*]#"
SSHEOF
return $?
