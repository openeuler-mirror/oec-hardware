#!/usr/bin/env python
# coding: utf-8

# Copyright (c) 2020 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01

import os
import json
import time
import subprocess
import base64
try:
    from urllib.parse import urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError

from flask import Flask, render_template, redirect, url_for, abort, request, \
                  make_response, send_from_directory, flash
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.secret_key = os.urandom(24)
bootstrap = Bootstrap(app)

dir_server = os.path.dirname(os.path.realpath(__file__))
dir_results = os.path.join(dir_server, 'results')
dir_files = os.path.join(dir_server, 'files')


@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', error='400 - Bad Request'), 400


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error='404 - Page Not Found'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error='500 - Internal Server Error'), 500


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results')
def get_results():
    results = {}
    for host in next(os.walk(dir_results))[1]:
        dir_host = os.path.join(dir_results, host)
        results[host] = {}
        for id in next(os.walk(dir_host))[1]:
            dir_id = os.path.join(dir_host, id)
            results[host][id] = next(os.walk(dir_id))[1]
    return render_template('results.html', results=results)


@app.route('/results/<host>/<id>/<job>')
def get_job(host, id, job):
    dir_job = os.path.join(dir_results, host, id, job)
    json_info = os.path.join(dir_job, 'compatibility.json')
    json_results = os.path.join(dir_job, 'factory.json')
    try:
        with open(json_info, 'r') as f:
            info = json.load(f)
        with open(json_results, 'r') as f:
            results = json.load(f)
    except Exception as e:
        abort(404)
    return render_template('job.html', host=host, id=id, job=job, info=info, results=results)


@app.route('/results/<host>/<id>/<job>/devices/<interface>')
def get_device(host, id, job, interface):
    dir_job = os.path.join(dir_results, host, id, job)
    json_results = os.path.join(dir_job, 'factory.json')
    try:
        with open(json_results, 'r') as f:
            results = json.load(f)
    except Exception as e:
        abort(404)
    for testcase in results:
        device = testcase.get('device')
        if device and device.get('INTERFACE') == interface:
            return render_template('device.html', device=device, interface=interface)
    else:
        abort(404)


@app.route('/results/<host>/<id>/<job>/devices')
def get_devices(host, id, job):
    dir_job = os.path.join(dir_results, host, id, job)
    json_devices = os.path.join(dir_job, 'device.json')
    try:
        with open(json_devices, 'r') as f:
            devices = json.load(f)
    except Exception as e:
        abort(404)
    return render_template('devices.html', devices=devices)


@app.route('/results/<host>/<id>/<job>/attachment')
def get_attachment(host, id, job):
    dir_job = os.path.join(dir_results, host, id, job)
    attachment = dir_job + '.tar.gz'
    filedir = os.path.dirname(attachment)
    filename = os.path.basename(attachment)
    return send_from_directory(filedir, filename, as_attachment=True)


@app.route('/results/<host>/<id>/<job>/logs/<name>')
def get_log(host, id, job, name):
    dir_job = os.path.join(dir_results, host, id, job)
    logpath = os.path.join(dir_job, name + '.log')
    if not os.path.exists(logpath):
        logpath = os.path.join(dir_job, 'job.log')
    try:
        with open(logpath, 'r') as f:
            log = f.read().split('\n')
    except Exception as e:
        abort(404)
    return render_template('log.html', name=name, log=log)


@app.route('/results/<host>/<id>/<job>/submit')
def submit(host, id, job):
    dir_job = os.path.join(dir_results, host, id, job)
    tar_job = dir_job + '.tar.gz'
    json_cert = os.path.join(dir_job, 'compatibility.json')
    try:
        with open(json_cert, 'r') as f:
            cert = json.load(f)
        with open(tar_job, 'rb') as f:
            attachment = base64.b64encode(f.read())
    except Exception as e:
        print(e)
        abort(500)

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
    except HTTPError as e:
        print(e)
        res = e

    if res.code == 200:
        flash('Submit Successful', 'success')
    else:
        flash('Submit Failed - {} {}'.format(res.code, res.msg),
              'danger')
    return redirect(request.referrer or url_for('get_job', host=host, id=id, job=job))


@app.route('/api/job/upload', methods=['GET', 'POST'])
def upload_job():
    host = request.values.get('host', '').strip().replace(' ', '-')
    id = request.values.get('id', '').strip().replace(' ', '-')
    job = request.values.get('job', '').strip().replace(' ', '-')
    filetext = request.values.get('filetext', '')

    if not(all([host, id, job, filetext])):
        return render_template('upload.html', host=host, id=id, job=job,
                                filetext=filetext, ret='Failed'), 400

    dir_job = os.path.join(dir_results, host, id, job)
    tar_job = dir_job + '.tar.gz'
    if not os.path.exists(dir_job):
        os.makedirs(dir_job)
    try:
        with open(tar_job, 'wb') as f:
            f.write(base64.b64decode(filetext))
        os.system("tar xf '%s' -C '%s'" % (tar_job, os.path.dirname(dir_job)))
    except Exception as e:
        print(e)
        abort(400)
    return render_template('upload.html', host=host, id=id, job=job,
                           filetext=filetext, ret='Successful')


@app.route('/files')
def get_files():
    files = os.listdir(dir_files)
    return render_template('files.html', files=files)


@app.route('/files/<path:path>')
def download_file(path):
    return send_from_directory('files', path, as_attachment=True)


@app.route('/api/file/upload', methods=['GET', 'POST'])
def upload_file():
    filename = request.values.get('filename', '')
    filetext = request.values.get('filetext', '')
    if not(all([filename, filetext])):
        return render_template('upload.html', filename=filename, filetext=filetext,
                               ret='Failed'), 400

    filepath = os.path.join(dir_files, filename)
    if not os.path.exists(dir_files):
        os.makedirs(dir_files)
    try:
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(filetext))
    except Exception as e:
        print(e)
        abort(400)
    return render_template('upload.html', filename=filename, filetext=filetext,
                           ret='Successful')


@app.route('/api/<act>', methods=['GET', 'POST'])
def test_server(act):
    valid_commands = ['rping', 'rcopy', 'ib_read_bw', 'ib_write_bw', 'ib_send_bw',
                      'qperf']
    cmd = request.values.get('cmd', '')
    cmd = cmd.split()
    if (not cmd) or (cmd[0] not in valid_commands + ['all']):
        print("Invalid command: {0}".format(cmd))
        abort(400)

    if act == 'start':
        if 'rping' == cmd[0]:
            cmd = ['rping', '-s']

        if 'ib_' in cmd[0]:
            ib_server_ip = request.values.get('ib_server_ip', '')
            if not ib_server_ip:
                print("No ib_server_ip assigned.")
                abort(400)
            ibdev, ibport = __get_ib_dev_port(ib_server_ip)
            if not all([ibdev, ibport]):
                print("No ibdev or ibport found.")
                abort(400)
            cmd.extend(['-d', ibdev, '-i', ibport])
    elif act == 'stop':
        if 'all' == cmd[0]:
            cmd = ['killall', '-9'] + valid_commands
        else:
            cmd = ['killall', '-9', cmd[0]]
    else:
        abort(404)

    print(' '.join(cmd))
    # pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pipe = subprocess.Popen(cmd)
    time.sleep(3)
    if pipe.poll():   ## supposed to be 0(foreground) or None(background)
        abort(400)
    else:
        return render_template('index.html')


def __get_ib_dev_port(ib_server_ip):
    try:
        cmd = "ip -o a | grep -w %s | awk '{print $2}'" % ib_server_ip
        # print(cmd)
        netdev = os.popen(cmd).read().strip()

        cmd = "udevadm info --export-db | grep DEVPATH | grep -w %s | awk -F= '{print $2}'" % netdev
        # print(cmd)
        path_netdev = ''.join(['/sys', os.popen(cmd).read().strip()])
        path_pci = path_netdev.split('net')[0]
        path_ibdev = 'infiniband_verbs/uverb*/ibdev'
        path_ibdev = ''.join([path_pci, path_ibdev])

        cmd = "cat %s" % path_ibdev
        # print(cmd)
        ibdev = os.popen(cmd).read().strip()

        path_ibport = '/sys/class/net/%s/dev_id' % netdev
        cmd = "cat %s" % path_ibport
        # print(cmd)
        ibport = os.popen(cmd).read().strip()
        ibport = int(ibport, 16) + 1
        ibport = str(ibport)

        return ibdev, ibport
    except Exception as e:
        print(e)
        return None, None


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

