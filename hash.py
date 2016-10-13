import hmac
import hashlib
import random
from string import letters
#this is the salt for hashing the password cookie
SECRET = 'BLOGINSECRET'
#this function creates a hash and returns it
def hash_str(val):
    hash = hmac.new(SECRET,val).hexdigest()
    return val + "|" + hash
#this function takes a hash and checks to make sure it has not been altered
#otherwise it returns a blank string
def check_hash(hash):
    val = hash.split('|')[0]
    if hash == hash_str(val):
        return val
    else:
        return ""
#this creates a random string made up of upercase and lowercase letters
def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))
#this function takes a password and username and creates a hash
def make_pw_hash(username,password,salt=None):
    if not salt:
        salt = make_salt()

    hash = hashlib.sha256(username+password+salt).hexdigest()
    return salt + "|" + hash
#this function takes a username password and hash inoder to check if a password has was altered
def valid_pw_hash(username,password,hash):
    salt = hash.split('|')[0]
    if hash == make_pw_hash(username,password,salt):
        return True
    else:
        return False


