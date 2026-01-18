from jwc import *
from setting import *

def main():
    clear_invalid_cookies()
    cookies_list = get_cookies()
    if not cookies_list:
        load_cookies(username, password, num=1)
        cookies_list = get_cookies()
    session = login_by_cookies(cookies_list[0])

    # 等待课程
    selector = CourseSelector(session)
    courses = ["AI1001A.02", "008185.02"]
    selector.wait_courses(courses, time_interval=5)

if __name__ == '__main__':
    main()
