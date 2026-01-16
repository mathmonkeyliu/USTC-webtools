from jwc import *
from setting import *

def main():
    # 示例：使用单个session一键选课
    
    clear_invalid_cookies()
    
    # 1. 获取Cookies并登录
    cookies_list = get_cookies()

    if not cookies_list:
        login_by_selenium(username, password, save_cookies=True)
        cookies_list = get_cookies()
        
    session = login_by_cookies(cookies_list[0])

    try:
        # 2. 初始化并一键选课
        selector = CourseSelector(session)
        selector.select_courses(['HS1648.03'])

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == '__main__':
    main()
