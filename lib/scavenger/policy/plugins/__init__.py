#!/usr/bin/env python
# encoding: utf-8
"""
__init__.py

Created by Thomas Mangin on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

import os, sys

__path1 = [os.path.abspath(os.path.join(p, 'scavenger', 'policy', 'plugins','postfix'))  for p in sys.path]
__path2 = [os.path.abspath(os.path.join(p, 'scavenger', 'policy', 'plugins','scavenger'))  for p in sys.path]
__path1 = list(set([p for p in __path1 if os.path.isdir(p)]))
__path2 = list(set([p for p in __path2 if os.path.isdir(p)]))

__path__ = list(set(__path1 + __path2))

#for p in __path:
#	for w in [f for _,f,_ in os.walk(p)]:
#		for f in w:
#			d = os.path.join(p,f)
#			if os.path.isdir(d) and not d.startswith('.'):
#				__path__.append(d)
#	break
#del os, sys, __path, p, f, d, w

__all__ = []
