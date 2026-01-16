import requests.exceptions
import time
from jwc import *
from setting import *

if __name__ == '__main__':
    test_list = ['MED3019.01', '001664KS.01', '206708.01', 'BIO2002.01', 'ESS1507.01', 'HS1612.03',
                 'HS1658.01', '001665KS.01', 'PHYS1005A.09', 'PHYS4703.01']
    
    # 加载/登录获取Cookies
    load_cookies(username, password, 1)
    cookies_list = get_cookies()
    
    if not cookies_list:
        print("未找到可用Cookie")
        exit()

    session = login_by_cookies(cookies_list[0])
    
    try:
        # 初始化选课状态
        student_id, turn_id = init_course_select(session)
        
        # 获取课程ID
        assocs = get_class_info(session, student_id, turn_id, test_list, 'id')
        
        # 循环抢课
        while True:
            for assoc in assocs:
                # 尝试选课
                result = add_class(session, student_id, turn_id, assoc)
                print(f"选课结果: {result}")
                
    except requests.exceptions.ConnectionError:
        print("连接错误")
        print(f"当前登录状态: {login_check(session)}")
        time.sleep(10)
    except Exception as e:
        print(f"发生错误: {e}")
