#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) 2020-2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01
# Desc: oech server url

import os
import json
import sys
import time
import subprocess
import base64
import re
import operator
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from flask import Flask, render_template, redirect, url_for, abort, request, send_from_directory, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)

dir_server = os.path.dirname(os.path.realpath(__file__))
dir_results = os.path.join(dir_server, 'results')
dir_files = os.path.join(dir_server, 'files')
DPDK_DRIVER = "uio_pci_generic"


@app.errorhandler(400)
def bad_request():
    """
    bad request
    """
    return render_template('error.html', error='400 - Bad Request'), 400


@app.errorhandler(404)
def page_not_found(e):
    """
    page not fount
    """
    return render_template('error.html', error='404 - Page Not Found'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """
    internal server error
    """
    return render_template('error.html', error='500 - Internal Server Error'), 500


@app.route('/')
def index():
    """
    index
    """
    return render_template('index.html')


@app.route('/results')
def get_results():
    """
    get results
    """
    results = {}
    for host in next(os.walk(dir_results))[1]:
        dir_host = os.path.join(dir_results, host)
        results[host] = {}
        for oec_id in next(os.walk(dir_host))[1]:
            dir_id = os.path.join(dir_host, oec_id)
            results[host][oec_id] = next(os.walk(dir_id))[1]
    return render_template('results.html', results=results)


@app.route('/results/<host>/<oec_id>/<job>')
def get_job(host, oec_id, job):
    """
    get job information
    :param host:
    :param oec_id:
    :param job:
    :return:
    """
    host = secure_filename(host)
    oec_id = secure_filename(oec_id)
    job = secure_filename(job)
    dir_job = os.path.join(dir_results, host, oec_id, job)
    json_info = os.path.join(dir_job, 'compatibility.json')
    files = os.listdir(dir_job)
    for file in files:
        if "factory.json" in file:
            json_results = os.path.join(dir_job, file)
    if not os.path.exists(json_info) or not os.path.exists(json_results):
        abort(404)

    try:
        with open(json_info, 'r') as file_content:
            info = json.load(file_content)
        with open(json_results, 'r') as file_content:
            results = json.load(file_content)
    except json.decoder.JSONDecodeError as error:
        sys.stderr.write("The file %s is not json file.\n")
        return False

    return render_template('job.html', host=host, id=oec_id, job=job, info=info, results=results,
                           json_results=json_results)


@app.route('/results/<host>/<oec_id>/<job>/devices/<interface>')
def get_device(host, oec_id, job, interface):
    """
    Get hardware device information
    :param host:
    :param oec_id:
    :param job:
    :param interface:
    :return:
    """
    host = secure_filename(host)
    oec_id = secure_filename(oec_id)
    job = secure_filename(job)
    dir_job = os.path.join(dir_results, host, oec_id, job)
    files = os.listdir(dir_job)
    for file in files:
        if "factory.json" in file:
            json_results = os.path.join(dir_job, file)
    if not os.path.exists(json_results):
        abort(404)

    try:
        with open(json_results, 'r') as file_content:
            results = json.load(file_content)
    except json.decoder.JSONDecodeError as error:
        sys.stderr.write("The file %s is not json file.\n")
        return False

    for testcase in results:
        device = testcase.get('device')
        if device and device.get('INTERFACE') == interface:
            return render_template('device.html', host=host, id=oec_id, job=job, device=device, interface=interface)
    else:
        abort(404)


@app.route('/results/<host>/<oec_id>/<job>/devices')
def get_devices(host, oec_id, job):
    """
    Get hardware devices information
    :param host:
    :param oec_id:
    :param job:
    :return:
    """
    host = secure_filename(host)
    oec_id = secure_filename(oec_id)
    job = secure_filename(job)
    dir_job = os.path.join(dir_results, host, oec_id, job)
    files = os.listdir(dir_job)
    for file in files:
        if "factory.json" in file:
            json_devices = os.path.join(dir_job, file)
    if not os.path.exists(json_devices):
        abort(404)

    try:
        with open(json_devices, 'r') as file_content:
            devices = json.load(file_content)
    except json.decoder.JSONDecodeError as error:
        sys.stderr.write("The file %s is not json file.\n")
        return False

    return render_template('devices.html', host=host, id=oec_id, job=job, devices=devices)


@app.route('/results/<host>/<oec_id>/<job>/attachment')
def get_attachment(host, oec_id, job):
    """
    Get result attachment
    :param host:
    :param oec_id:
    :param job:
    :return:
    """
    dir_job = os.path.join(dir_results, host, oec_id, job)
    attachment = dir_job + '.tar'
    filedir = os.path.dirname(attachment)
    filename = os.path.basename(attachment)
    return send_from_directory(filedir, filename, as_attachment=True)


@app.route('/results/<host>/<oec_id>/<job>/logs/<name>')
def get_log(host, oec_id, job, name):
    """
    Get log
    :param host:
    :param oec_id:
    :param job:
    :param name:
    :return:
    """
    host = secure_filename(host)
    oec_id = secure_filename(oec_id)
    job = secure_filename(job)
    dir_job = os.path.join(dir_results, host, oec_id, job)
    logpath = os.path.join(dir_job, name + '.log')
    if not os.path.exists(logpath):
        logpath = os.path.join(dir_job, 'job.log')

    with open(logpath, 'r') as file_content:
        log = file_content.read().split('\n')

    return render_template('log.html', host=host, id=oec_id, job=job, name=name, log=log)


@app.route('/results/<host>/<oec_id>/<job>/submit')
def submit(host, oec_id, job):
    """
    Submit test result
    :param host:
    :param oec_id:
    :param job:
    :return:
    """
    dir_job = os.path.join(dir_results, host, oec_id, job)
    tar_job = dir_job + '.tar'
    json_cert = os.path.join(dir_job, 'compatibility.json')
    if not os.path.exists(json_cert) or not os.path.exists(tar_job):
        abort(500)

    cert = ""
    try:
        with open(secure_filename(json_cert), 'r') as file_content:
            cert = json.load(file_content)
    except json.decoder.JSONDecodeError:
        sys.stderr.write("The file %s is not json file.\n")
        return False

    attachment = ""
    with open(secure_filename(tar_job), 'rb') as file_content:
        attachment = base64.b64encode(file_content.read())

    form = {}
    form['certid'] = cert.get('certid')
    form['attachment'] = attachment

    server = cert.get('server')
    url = 'http://{}/api/job/upload'.format(server)
    data = urlencode(form).encode('utf8')
    headers = {
        'Content-type': 'application/x-www-form-urlencoded',
        'Accept': 'text/plain'
    }
    try:
        req = Request(url, data=data, headers=headers)
        res = urlopen(req)
    except HTTPError as concrete_error:
        sys.stderr.write("Submit result execute failed.\n")
        res = concrete_error

    if res.code == 200:
        flash('Submit test result successfully.', 'success')
    else:
        flash('Submit test result failed - {} {}'.format(res.code, res.msg), 'danger')
    return redirect(request.referrer or url_for('get_job', host=host, id=id, job=job))


@app.route('/api/job/upload', methods=['GET', 'POST'])
def upload_job():
    """
    Upload job
    :return:
    """
    host = secure_filename(request.values.get('host', '').strip().replace(' ', '-'))
    oec_id = secure_filename(request.values.get('id', '').strip().replace(' ', '-'))
    job = secure_filename(request.values.get('job', '').strip().replace(' ', '-'))
    filetext = request.values.get('filetext', '')
    if not (all([host, oec_id, job, filetext])):
        return render_template('upload.html', host=host, id=id, job=job,
                               filetext=filetext, ret='Failed'), 400

    ori_file = base64.b64decode(filetext)
    filesize = len(ori_file)
    if filesize > 1073741824:
        sys.stderr.write(
            "The file size is more than 1GB, upload file failed.\n")
        return render_template('upload.html', host=host, id=id, job=job,
                               filetext=filetext, ret='Failed'), 500

    dir_job = os.path.join(dir_results, host, oec_id, job)
    if not os.path.exists(dir_job):
        os.makedirs(dir_job)

    tar_job = dir_job + '.tar'
    with open(tar_job, 'wb') as file_content:
        file_content.write(ori_file)
    result = subprocess.getstatusoutput(
        "tar xf '%s' -C '%s'" % (tar_job, os.path.dirname(dir_job)))
    if result[0] != 0:
        sys.stderr.write("Decompress log file failed.\n")

    return render_template('upload.html', host=host, id=oec_id, job=job,
                           filetext=filetext, ret='Successful')


@app.route('/files')
def get_files():
    """
    Get files
    """
    files = os.listdir(dir_files)
    return render_template('files.html', files=files)


@app.route('/files/<path:path>')
def download_file(path):
    """
    Download file
    """
    return send_from_directory('files', path, as_attachment=True)


@app.route('/api/file/upload', methods=['GET', 'POST'])
def upload_file():
    """
    Upload_file
    """
    filename = secure_filename(request.values.get('filename', ''))
    filetext = request.values.get('filetext', '')
    if not (all([filename, filetext])):
        return render_template('upload.html', filename=filename, filetext=filetext,
                               ret='Failed'), 400

    filepath = os.path.join(dir_files, filename)
    if not os.path.exists(dir_files):
        os.makedirs(dir_files)

    with open(filepath, 'wb') as file_content:
        file_content.write(base64.b64decode(filetext))

    return render_template('upload.html', filename=filename, filetext=filetext,
                           ret='Successful')


@app.route('/api/config/ip', methods=['GET', 'POST'])
def config_ip():
    """
    config server ip
    """
    sever_ip = request.values.get('serverip', '')
    card_id = request.values.get('cardid', '')
    cmd_result = subprocess.getoutput("ip link show up | grep 'state UP'")

    ports = []
    for port in cmd_result.split('\n'):
        ports.append(port.split(':')[1].strip())

    for pt in ports:
        cmd_result = subprocess.getoutput("ethtool -i %s" % pt)
        for data in cmd_result.split('\n'):
            if "bus-info" in data:
                pci_num = data.split(':', 1)[1].strip()
                quad = __get_quad(pci_num)
                if operator.eq(quad, eval(card_id)):
                    subprocess.getoutput(
                        "ifconfig %s:0 %s/24" % (pt, sever_ip))
                    break
        else:
            continue
        break

    return render_template('index.html')


@app.route('/api/get/ethpeer', methods=['GET', 'POST'])
def get_ethpeer():
    """
    get ethpeer
    """
    dic = {}
    card_id = request.values.get('cardid', '')
    __setting_dpdk_env()
    interface = __get_server_port(card_id)
    ethpeer = subprocess.getoutput("ip link show dev %s | grep 'link/ether' | awk '{print $2}'" % interface)
    dic = {'ethpeer': ethpeer}

    return dic


@app.route('/api/bind/server', methods=['GET', 'POST'])
def bind_server_card():
    """
    Bind server card
    """
    interface = ""
    card_id = request.values.get('cardid', '')
    interface = __get_server_port(card_id)
    pci_num = subprocess.getoutput("ethtool -i %s | grep 'bus-info' | awk '{print $2}'" % interface) 
    subprocess.getoutput("ip link set down %s" % interface)
    cmd = subprocess.getstatusoutput("dpdk-devbind -b %s %s" % (DPDK_DRIVER, pci_num))
    if cmd[0] != 0:
        sys.stderr.write("Bind server card failed.\n")

    return render_template('index.html')


@app.route('/api/unbind/server', methods=['GET', 'POST'])
def unbind_server_card():
    """
    Unbind server card
    """
    card_id = request.values.get('cardid', '')
    pci_num = subprocess.getoutput("dpdk-devbind  -s | grep 'drv=%s' | awk '{print $1}'" % DPDK_DRIVER)
    quad = __get_quad(pci_num)
    kernel_driver = subprocess.getoutput("lspci -s %s -v | grep 'Kernel modules' | awk '{print $3}'" % pci_num)
    if operator.eq(quad, eval(card_id)):
        subprocess.getoutput("dpdk-devbind -b %s %s" % (kernel_driver, pci_num))
        result = subprocess.getoutput(("dpdk-devbind -s | grep {0}").format(pci_num))
        interface = re.search(r'if=(\S*)', result).group(1)
        subprocess.getoutput("ip link set up %s") % interface

    return render_template('index.html')


@app.route('/api/<act>', methods=['GET', 'POST'])
def test_server(act):
    """
    test server
    """
    valid_commands = ['rping', 'rcopy', 'ib_read_bw',
                      'ib_write_bw', 'ib_send_bw', 'qperf', 'dpdk-testpmd']
    cmd = request.values.get('cmd', '')
    pci_num = ""
    interface = ""
    card_id = request.values.get('cardid', '')
    cmd = cmd.split()
    if (not cmd) or (cmd[0] not in valid_commands + ['all']):
        sys.stdout.write("Invalid command: {0}.\n".format(cmd))
        abort(400)
    if act == 'start':
        if cmd[0] == 'rping':
            cmd = ['rping', '-s']
        if 'ib_' in cmd[0]:
            ib_server_ip = request.values.get('ib_server_ip', '')
            if not ib_server_ip:
                sys.stdout.write("No ib_server_ip assigned.\n")
                abort(400)
            ibdev, ibport = __get_ib_dev_port(ib_server_ip)
            if not all([ibdev, ibport]):
                sys.stderr.write("No ibdev or ibport found.\n")
                abort(400)
            cmd.extend(['-d', ibdev, '-i', ibport])
        if 'dpdk' in cmd[0]:
            result = subprocess.getstatusoutput("dpdk-devbind -s | grep 'drv=%s'" % DPDK_DRIVER)
            if result[0] == 0:
                pci_num = subprocess.getoutput("dpdk-devbind -s | grep 'drv=%s' | awk '{print $1}'" % DPDK_DRIVER)
            else:
                __setting_dpdk_env()
                interface = __get_server_port(card_id)
                pci_num =  subprocess.getoutput("ethtool -i %s | grep 'bus-info' | awk '{print $2}'"
                        % interface)
            cmd = ['dpdk-testpmd', '-l', '0-1', '-n', '1', '-a', pci_num, '--', '--forward-mode=rxonly']
            time.sleep(3)
        __execute_cmd(cmd)

    elif act == 'stop':
        if cmd[0] == 'all':
            for process_name in valid_commands:
                __stop_process(process_name)
        else:
            __stop_process(cmd[0])
    else:
        abort(404)

    return render_template('index.html')


def __get_server_port(card_id):
    """
    get server interface
    """
    ports = []
    interface = ""
    ports = subprocess.getoutput("ip link show up | grep 'state UP' | awk -F ': ' '{print $2}'").split('\n')
    for pt in ports:
        pci_num = subprocess.getoutput("ethtool -i %s | grep 'bus-info' | awk '{print $2}'" % pt)
        quad = __get_quad(pci_num)
        if operator.eq(quad, eval(card_id)):
            result = subprocess.getoutput(("dpdk-devbind -s | grep {0}").format(pci_num))
            interface = re.search(r'if=(\S*)', result).group(1)
            break

    return interface


def __stop_process(process_name):
    check_cmd = subprocess.getstatusoutput(
        "ps -ef | grep %s | grep -v grep" % process_name)
    if check_cmd[0] != 0:
        return
    kill_cmd = ['killall', '-9', process_name]
    __execute_cmd(kill_cmd)


def __execute_cmd(cmd):
    pipe = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf8')
    time.sleep(3)
    if pipe.poll():  # supposed to be 0(foreground) or None(background)
        abort(400)


def __get_ib_dev_port(ib_server_ip):
    try:
        cmd = "ip -o a | grep -w %s | awk '{print $2}'" % ib_server_ip
        netdev = subprocess.getoutput(cmd)

        cmd = "udevadm info --export-db | grep DEVPATH | grep -w %s | awk -F= '{print $2}'" % netdev
        path_netdev = ''.join(['/sys', subprocess.getoutput(cmd).strip()])
        path_pci = path_netdev.split('net')[0]
        path_ibdev = 'infiniband_verbs/uverb*/ibdev'
        path_ibdev = ''.join([path_pci, path_ibdev])

        cmd = "cat %s" % path_ibdev
        ibdev = subprocess.getoutput(cmd).strip()

        path_ibport = '/sys/class/net/%s/dev_id' % netdev
        cmd = "cat %s" % path_ibport
        ibport = subprocess.getoutput(cmd).strip()

        ibport = int(ibport, 16) + 1
        ibport = str(ibport)

        return ibdev, ibport
    except Exception as concrete_error:
        sys.stderr.write("Get ibdev, ibport failed.\n")
        return None, None


def __get_quad(pci_num):
    """
    Get network card quad
    """
    cmd_result = subprocess.getoutput("lspci -xs %s" % pci_num).split('\n')

    quad = []
    for ln in cmd_result:
        if re.match("00: ", ln):
            tmp = ln.split(" ")[1:5]
            quad.extend([tmp[1] + tmp[0], tmp[3] + tmp[2]])
        if re.match("20: ", ln):
            tmp = ln.split(" ")[-4:]
            quad.extend([tmp[-3] + tmp[-4], tmp[-1] + tmp[-2]])
    return quad


def __setting_dpdk_env():
    """
    Dpdk server environment setting
    """
    subprocess.getoutput("modprobe uio; modprobe %s" % DPDK_DRIVER)
    if subprocess.getstatusoutput("lsmod | grep %s" % DPDK_DRIVER)[0] != 0:
        sys.stderr.write("Dpdk driver moprobe failed.\n")
        return False
    subprocess.getoutput("dpdk-hugepages.py -u")
    subprocess.getoutput("dpdk-hugepages.py -c")
    subprocess.getoutput("dpdk-hugepages.py --setup 2G")

    return True

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
