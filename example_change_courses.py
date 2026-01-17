from jwc import *
from setting import *

def main():
    # 清空失效的Cookies
    clear_invalid_cookies()
    
    cookies_list = get_cookies()

    if not cookies_list:
        load_cookies(username, password, num=1)
        cookies_list = get_cookies()
        
    session = login_by_cookies(cookies_list[0])

    # 换课
    selector = CourseSelector(session)
    prev_course = ['MARX1013.18']
    new_course = ['MARX1013.02']
    selector.change_course(prev_course, new_course)

if __name__ == '__main__':
    main()

