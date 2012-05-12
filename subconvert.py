#!/usr/bin/env python
#-*- coding: utf-8 -*-

from subconvert import subconvert
try:
    subconvert.main()
except KeyboardInterrupt:
    raise SystemExit(0)
