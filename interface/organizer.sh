#!/bin/bash

$PVE_HOST = "192.168.1.2:8006"

init_role() {

}

create_competitor() {
    local userid=$1
    local password=$2
    
    curl -X POST "http://$PVE_HOST/api2/json/access/users" -d "username=$userid-umd_ccdc_competitor@pve&password=$password" --insecure
}

reset_password() {
    local userid=$1
    local prev_password=$2
    local password=$3
    
    curl -X PUT "http://$PVE_HOST/api2/json/access/password" -d "userid=$userid-umd_ccdc_competitor@pve&confirmation-password=$prev_password&password=$password" --insecure
}