from jwc import *
from setting import *

def main():
    drop_classes = []
    add_classes = ["001139.02"]
    clear_invalid_cookies()
    
    cookies_list = get_cookies()

    if not cookies_list:
        load_cookies(username, password, num=1)
        cookies_list = get_cookies()
        
    session = login_by_cookies(cookies_list[0])

    # 选课
    selector = CourseSelector(session)

    input("按回车键开始")
    
    while True:
        time.sleep(3)
        selector.select_courses(add_classes)

if __name__ == '__main__':
    main()
