#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
sys.path.append(sys.path[0] + '/subconvert')

from subconvert import subconvert

try:
    subconvert.main()
except KeyboardInterrupt:
    raise SystemExit(0)
