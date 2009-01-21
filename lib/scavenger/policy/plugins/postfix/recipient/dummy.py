#!/usr/bin/env python
# encoding: utf-8
"""
dummy.py

Created by Thomas Mangin on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

class RecipientChecker (object):
	def __init__ (self,configuration):
		pass
	
	def passthrough (self,user,domain):
		return False
	
	def exists (self, username, domain):
		return False
