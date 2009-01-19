#!/usr/bin/env python
# encoding: utf-8
"""
parser.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from scavenger.parser import Parser as BaseParser
from scavenger.dispatch.message import DispatchMessageFactory

class Parser (BaseParser):
	def __init__ (self,debug=False):
		BaseParser.__init__(self,DispatchMessageFactory(),debug)

