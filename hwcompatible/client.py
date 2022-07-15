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

import os
import base64
from urllib.parse import urlencode
from urllib.request import urlopen, Request


class Client:
    """
    Client which need upload file to server
    """

    def __init__(self, host, oec_id, logger):
        self.host = host
        self.oec_id = oec_id
        self.logger = logger
        self.form = {}

    def upload(self, files, server='localhost'):
        """
        Upload request to server
        :param files:
        :param server:
        :return:
        """
        filename = os.path.basename(files)
        try:
            job = filename.split('.')[0]
            with open(files, 'rb') as file:
                filetext = base64.b64encode(file.read())
        except Exception as excp:
            self.logger.error("Get files which need to upload failed.")
            return False

        if not self.host or not self.oec_id:
            self.logger.error("Missing host({0}) or id({1})".format(
                self.host, self.oec_id))
            return False
        self.form['host'] = self.host
        self.form['id'] = self.oec_id
        self.form['job'] = job
        self.form['filetext'] = filetext

        url = 'http://{}/api/job/upload'.format(server)
        data = urlencode(self.form).encode('utf8')
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }
        try:
            req = Request(url, data=data, headers=headers)
            res = urlopen(req)
            if res.code != 200:
                self.logger.error("Upload file to server failed. %s" % res.msg)
                return False
            return True
        except Exception as excp:
            self.logger.error("Upload file to server failed.")
            return False
