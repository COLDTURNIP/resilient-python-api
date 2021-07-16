#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import os

PASSWD_PATTERNS = ['pass', 'secret', 'pin', 'key', 'id']

INBOUND_MSG_DEST_PREFIX = "inbound_destinations"
INBOUND_MSG_APP_CONFIG_Q_NAME = "inbound_destination_api_name"

APP_FUNCTION_PAYLOAD_VERSION = 2.0

MAX_NUM_WORKERS = 500

APP_LOG_DIR = os.environ.get("APP_LOG_DIR", "logs")
CMDS_LOGGER_NAME = "resilient_circuits_cmd_logger"
LOG_DIVIDER = "\n------------------------\n"

DEFAULT_NONE_STR = "Not found"
