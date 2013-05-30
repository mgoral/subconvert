#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import subconvert.apprunner as apprunner

try:
    apprunner.main()
except KeyboardInterrupt:
    raise SystemExit(0)
