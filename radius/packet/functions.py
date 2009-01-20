import md5
from struct import pack,unpack


def encrypt_radius_password(clear_password, secret, authenticator):
	last = authenticator
	clear = clear_password + (16-(len(clear_password)%16))*'\0'
	crypted = ''

	for part in (clear[i:i+16] for i in xrange(0, len(clear), 16)):
		digest = md5.new(secret+last).digest()
		crypted += pack('iiii', *(a^b for a,b in zip(*(unpack('iiii', p) for p in (digest, part)))))
		last = crypted

	return crypted

def decrypt_radius_password(crypted, secret, authenticator):
	if crypted.__len__() % 16:
		raise "invalid crypted password"

	clear = []

	for part, todo in [(crypted[i-16:i], crypted[:i-16]) for i in range(len(crypted), 16, -16)] + [(crypted[:16], authenticator)]:
		digest = md5.new(secret+todo).digest()
		clear.append(pack('iiii', *(a^b for a,b in zip(*(unpack('iiii', p) for p in (digest, part))))))

		
#	print ''.join(clear[::-1]).rstrip('\0').encode('hex'), len(''.join(clear[::-1]).rstrip('\0').encode('hex'))
	return ''.join(clear[::-1]).rstrip('\0')




def compare_chap_password(password, chap_password, chap_challenge):
	check_passwd = md5.new()
	check_passwd.update(chap_password[0])
	check_passwd.update(password)
	check_passwd.update(chap_challenge)
	string = chap_password[0] + check_passwd.digest()
	return string == chap_password






if __name__ == '__main__':
	passwd = 'thisismypasswordaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
	secret = 'thisismysecretdslkdjskldjskldjklsjdklsjdklsjdkljsdklj'
	crypted = encrypt_radius_password(passwd, secret, 'aaaaaaaaaaaaaaaa')
	decrypted = decrypt_radius_password(crypted, secret, 'aaaaaaaaaaaaaaaa')
	print len(crypted)
	print len(passwd), passwd
	print len(decrypted), decrypted
	print passwd == decrypted

