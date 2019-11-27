import random
import string
from multiprocessing import Process

def generate_random_token(length=32, character_set=string.ascii_letters + string.digits + '-_'):
    return ''.join([random.choice(character_set) for _ in range(length)])

def send_email_async(email):
    Process(target=email.send).start()