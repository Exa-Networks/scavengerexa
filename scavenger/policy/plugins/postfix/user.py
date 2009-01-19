#!/usr/bin/env python
# encoding: utf-8
"""
user.py

Created by Thomas Mangin on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

DEFAULT_PENALTY = 7

import random
import time

from recipient.ld import RecipientChecker as LDChecker
from recipient.vm import RecipientChecker as VMChecker

from twisted.python import log

from scavenger.policy.plugin import PostfixPlugin
from scavenger.policy.plugin import PluginDatabase
from scavenger.policy.plugin import response

tables = {
	'table_guesser':	'user_guesses',
	'table_recipient':	'user_recipient',
}

create_guesser = """
create table if not exists %(table_guesser)s (
	ip                  varchar(40) primary key,
	number_right        smallint default 0,
	number_wrong        smallint default 0,
	first_seen_right    timestamp default null,
	first_seen_wrong    timestamp default null,
	last_seen_right     timestamp default null,
	last_seen_wrong     timestamp default null,
	
	block_right         smallint default 0,
	block_wrong         smallint default 0,
	block_from          timestamp default null,
	block_to            timestamp default null
)
""".strip() % tables

create_recipient = """
create table if not exists %(table_recipient)s (
	queue_id            varchar(15) not null,
	recipient           varchar(256) not null,
	exist               boolean not null,
	time                timestamp not null
)
""".strip() % tables


# -------------------------------------------------------------------


class NoSuchUser (response.ResponseFail):
	web_code = '2.1.1'

class TooManyBadUser (response.ResponseTempFail):
	web_code = '2.1.2'


class UserDB(PluginDatabase):
	def add_recipient(self, queue_id, recipient, exist):
		# time should be taken from the message
		query = "INSERT INTO %(table_recipient)s (queue_id,recipient,exist,time) VALUES (?, ?, ?, datetime('now'))" % tables
		return self.insert(query, queue_id, recipient, exist)

	def select_recipients(self, queue_id):
		query = "SELECT recipient,exist FROM %(table_recipient)s WHERE queue_id = ?" % tables
		return self.fetchall(query, queue_id)

	def del_recipient(self, queue_id):
		query = "DELETE FROM %(table_recipient)s WHERE queue_id = ? or time < datetime('now','-30 minutes')" % tables
		return self.delete(query, queue_id)

	def insert_new_ip(self, client_address):
		query = "INSERT INTO %(table_guesser)s (ip) values (?)" % tables
		return self.insert(query, client_address)

	def add_right_update(self, client_address):
		query = "UPDATE %(table_guesser)s SET number_right = number_right+1, first_seen_right = coalesce(first_seen_right,datetime('now')), last_seen_right = datetime('now') WHERE ip = ?" % tables
		return self.update(query, client_address)

	def add_wrong_update(self, client_address):
		query = "UPDATE %(table_guesser)s SET number_wrong = number_wrong+1, first_seen_wrong = coalesce(first_seen_right,datetime('now')), last_seen_wrong = datetime('now') WHERE ip = ?" % tables
		return self.update(query, client_address)

	def select_numbers(self, client_address):
		query = "SELECT number_right,number_wrong from %(table_guesser)s where ip = ?" % tables
		return self.fetchone(query, client_address)

	def delete_ip(self,penalty):
		query = """DELETE FROM %(table_guesser)s where
		(
				(last_seen_right is null or last_seen_right < datetime('now','-8 days'))
			and
				(last_seen_wrong is null or last_seen_wrong < datetime('now','-8 days'))
		)
		or
		(
				(first_seen_right is null or first_seen_right < datetime('now','-1 months'))
			or
				(first_seen_wrong is null or first_seen_wrong < datetime('now','-1 months'))
		)
		or
		(
				(first_seen_wrong is not null and first_seen_wrong < datetime('now','-6 hours'))
			and 
				(last_seen_wrong is not null and last_seen_wrong < datetime('now', '-30 minutes'))
			and
				(number_right-(number_wrong*?) <= 0)
		)
		""" % tables
		return self.delete(query,penalty)



class User (PostfixPlugin):
	debug = False
	database_factory = UserDB
	schema = [create_guesser, create_recipient]

	def onInitialisation (self):
		self.vmchecker = VMChecker(self.configuration)
		self.ldchecker = LDChecker(self.configuration)
		self.penalty = self.configuration.get('penalty', str(DEFAULT_PENALTY))
		return True

	def requiredAttributes (self):
		# Do not check for sender as we must allow bounces, which have empty sender
		return ['client_address','recipient']

	def check (self, message):
		state = message.get('protocol_state','').upper()
		message.update(tables)
		if state == 'RCPT':
			return self.check_rcpt(message)
		if state == 'DATA':
			return self.check_data(message)
		# This plugin should only be called at DATA level ATM even if the config include RCPT as well
		return response.ResponseContinue

	def check_rcpt (self,message):
		recipient = message['recipient']
		client_address = message['client_address']
		
		try:
			user, domain = recipient.split('@')
		except ValueError:
			return response.DataError('invalid email address: %s' % recipient)
		
		exist = self.vmchecker.exists(user,domain) or self.ldchecker.exists(user,domain)
		
		# XXX: we should not alter message
		message['exist'] = exist
		
		try:
			self.database.insert_new_ip(client_address)
		except self.databasepool.module.IntegrityError:
			# XXX: making sure the raw exists before anything
			pass
			
		if exist:
			#print add_right_update % message
			self.database.add_right_update(client_address)
			return response.ResponseContinue
		else:
			#print add_wrong_update % message
			self.database.add_wrong_update(client_address)
			return NoSuchUser('The recipient <%s> does not exist' % recipient)
		
	def check_data (self,message):
		client_address = message['client_address']

		answer = self.database.select_numbers(client_address)
		if self.debug: log.msg('pluging grey : the db is returning for ip %s : %s' % (client_address,str(answer)))

		if not answer or not (answer.has_key('number_right') and answer.has_key('number_wrong')):
			# something unexpected happened, don't hold the mail up because we made a mistake
			if self.debug: log.logerr.write('pluging grey : the valid user checker had no information for the sending ip')
			return response.ResponseContinue

		try:
			right = int(answer['number_right'])
			wrong = int(answer['number_wrong'])
		except TypeError:
			log.logerr.write('plugin grey : the value returned for the spam score was of a type that we cannot convert to an int')
			return response.ResponseContinue
		except ValueError:
			log.logerr.write('plugin grey : junk value returned instead of the spam score')
			return response.ResponseContinue

		if right - (wrong*self.penalty) > 0:
			return response.ResponseContinue
		else:
			sender = message.get('sender','')
			recipient = message.get('recipient','')
			if sender == '':
				sender = 'this bounce message'
			else:
				sender = '<%s>' % sender
			return TooManyBadUser('%s tried to contact <%s>, but previously your mail server (%s) tried to send us too many mails to accounts which do not exist. This server is now blocked for up to 6 hours (existing emails:%d / invalid emails:%d / score %d)' % (sender,recipient,client_address,right,wrong, right-(wrong*self.penalty)))


	def cleanup(self):
		if random.randint(0,100) == 100:
			self.database.delete_ip(self.penalty)

plugin = User('user', '2.1')
