from jwc.login import *
from setting import *

import pickle
with open('cookies.pkl', 'rb') as f:
    cookies = pickle.load(f)
print(cookies)
# login_by_selenium(username, password, save_cookies=True)