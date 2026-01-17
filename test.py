from jwc import *
from setting import *

clear_invalid_cookies()

cookies_list = get_cookies()

if not cookies_list:
    load_cookies(username, password, num=1)
    cookies_list = get_cookies()
    
session = login_by_cookies(cookies_list[0])
selector = CourseSelector(session)

selector.change_course(['MARX1013.18'], ['MARX1013.02'])
