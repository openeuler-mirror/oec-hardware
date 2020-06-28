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
import base64
try:
    from urllib.parse import urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError


class Client(object):
    """
    upload client
    """
    def __init__(self, host, oec_id):
        self.host = host
        self.id = oec_id
        self.form = {}

    def upload(self, files, server='localhost'):
        """
        upload client request
        :param files:
        :param server:
        :return:
        """
        filename = os.path.basename(files)
        try:
            job = filename.split('.')[0]
            with open(files, 'rb') as f:
                filetext = base64.b64encode(f.read())
        except IOError as e:
            print(e)
            return False

        if not self.host or not self.id:
            print("Missing host({0}) or id({1})".format(self.host, self.id))
            return False
        self.form['host'] = self.host
        self.form['id'] = self.id
        self.form['job'] = job
        self.form['filetext'] = filetext

        url = 'http://{}/api/job/upload'.format(server)
        data = urlencode(self.form).encode('utf8')
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }
        try:
            # print(url)
            req = Request(url, data=data, headers=headers)
            res = urlopen(req)
            if res.code != 200:
                print("Error: upload failed, %s" % res.msg)
                return False
            return True
        except HTTPError as e:
            print(e)
            return False


if __name__ == '__main__':
    c = Client(' Taishan 2280', ' Testid-123523')
    import sys
    file_name = sys.argv[1]
    c.upload(file_name)
