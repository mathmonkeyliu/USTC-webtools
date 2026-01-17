from jwc import *
from setting import *

def main():
    # 示例：使用单个session一键选课
    
    clear_invalid_cookies()
    
    # 1. 获取Cookies并登录
    cookies_list = get_cookies()

    if not cookies_list:
        load_cookies(username, password, num=1)
        cookies_list = get_cookies()
        
    session = login_by_cookies(cookies_list[0])

    try:
        selector = CourseSelector(session)
        courses = ["BIO3501.01", "AI1001A.02", "PE00139.01", "022118.01", "008185.02", "008144.01", "022062.07", "AI1001A.02", "008187.02"]
        selector.select_courses(courses)

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == '__main__':
    main()
