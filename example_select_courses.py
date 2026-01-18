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

    # 选课
    selector = CourseSelector(session)
    courses = ["BIO3501.01", "AI1001A.02", "PE00139.01", "022118.01", "008185.02", "008144.01", "022062.07", "AI1001A.02", "008187.02"]
    selector.select_courses(courses)

if __name__ == '__main__':
    main()

    # 如果想使用抢课，注释掉main()，在抢课前约5分钟提前运行如下命令完成登录，并在抢课开始前几秒钟回车
    # username = "username"
    # password = "password"
    # drop_classes = ["AI1001A.02"]
    # add_classes = ["BIO3501.01"]
    # multi_session_solution(start_time="11:59:58", stop_time="12:00:05", min_interval=0.1, drop_codes=drop_classes, add_codes=add_classes, session_number=10, username=username, password=password)
