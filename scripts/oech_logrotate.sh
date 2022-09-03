# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @meitingli/bubble_mt@outlook.com
# Create: 2022-08-09
# Desc: oech log rotate and delete

TEST_LOG_PATH="/usr/share/oech/logs"

function backup_active_log() {
    cur_date=$(date -d "yesterday" +"%Y%m%d%H")
    cd ${TEST_LOG_PATH}
    zip_file="oech-logrotate-${cur_date}.zip"
    zip -qmo ${zip_file} ./*.tar
}

function delete_test_log() {
    max_count=30
    log_count=$(ls ${TEST_LOG_PATH} | wc -l)
    delete_count=$((log_count - max_count))
    if [ ${delete_count} -le 0 ]; then
        return
    fi
    delete_files=$(ls -rt ${TEST_LOG_PATH} | head -${delete_count})
    for file in ${delete_files}; do
        rm -rf ${TEST_LOG_PATH}/${file}
    done
}

function start_logrotate() {
    while true; do
        sleep 1d
        backup_active_log
        delete_test_log
    done
}

function stop_logrotate() {
    ps -ef | grep oech_logrotate.sh | grep -v grep | awk '{print $2}' | xargs killall >/dev/null 2>&1
    return 0
}

function main() {
    func_name=$1
    if [[ $func_name == "start_logrotate" ]]; then
        start_logrotate &
    elif [[ $func_name == "stop_logrotate" ]]; then
        stop_logrotate
    else
        echo "The function doesn't exist, please check!"
        return 1
    fi
}

main "$@"
