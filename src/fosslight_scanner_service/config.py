#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os


class Config(object):
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 5001
    ROOT = "./web_data"

    ROOT_PATH = os.path.join(ROOT, "osc")
    OUTPUT_DIR_NAME = "output"
    RESULT_URL_PREFIX = "http://"+SERVER_IP+":"+str(SERVER_PORT)+"/download?"
    RETURN_OK = 200
    RETURN_NOK = 500  # Internal server error

    MAIL_SERVER = SERVER_IP
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_SENDER = 'no-reply@fosslight.com'
    UPLOAD_EXTENSIONS = ['.log', '.xlsx', '.html']
    MAX_CONTENT_LENGTH = 1000 * 1024 * 1024

    CELERY_BROKER_URL = 'redis://127.0.0.1:6379'
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379'
    CELERY_REDIRECT_STDOUTS = False
    worker_redirect_stdouts = False

    FL_HUB_TOKEN = "eyJhABCD***"
    FL_HUB_REGISTER_URL = "https://demo.fosslight.org/api/v1/oss_report_selfcheck"


class ProductionConfig(Config):
    pass


class DevelopmentConfig(Config):
    pass


class TestingConfig(Config):
    pass
