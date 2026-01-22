from .CourseSelect import *
from .login import *
from .const import SLEEP_TIME
from concurrent.futures import ThreadPoolExecutor


def multi_session_solution(start_time: str, stop_time: str, min_interval: int | float, drop_codes: list[str], add_codes: list[str], session_number=1, username=None, password=None) -> None:
    """
    基于多浏览器的抢课方案
    :param start_time: 开始时间
    :param stop_time: 结束时间
    :param min_interval: 最小间隔时间
    :param drop_codes: 退课课程代码列表
    :param add_codes: 抢课课程代码列表
    :param session_number: 浏览器数量
    :param username: 用户名
    :param password: 密码
    """
    selectors = []
    
    clear_invalid_cookies()
    cookies_list = get_cookies()

    load_cookies(username, password, session_number - len(cookies_list))

    clear_invalid_cookies()
    cookies_list = get_cookies()
    print(f"使用{len(cookies_list)}个浏览器")
    
    for idx, cookies in enumerate(cookies_list):
        try:
            sess = login_by_cookies(cookies)
            selector = CourseSelector(sess)
            selectors.append({'selector': selector, 'id': idx})
            print(f"{idx}号浏览器登录完成")
        except Exception as e:
            print(f"{idx}号浏览器初始化失败: {e}")

    # Use first selector to resolve IDs
    main_selector = selectors[0]['selector']
    drop_assocs = main_selector.get_class_info(drop_codes, 'id')
    add_assocs = main_selector.get_class_info(add_codes, 'id')
    
    drop_codes_copy = drop_codes.copy()
    add_codes_copy = add_codes.copy()

    input("按回车键开始")
    executor = ThreadPoolExecutor(max_workers=len(drop_codes) + len(add_codes))

    while get_time() < start_time:
        time.sleep(SLEEP_TIME)

    while get_time() < stop_time:
        if not selectors:
            break
            
        dead_selectors = []
        for item in selectors:
            selector = item['selector']
            browser_id = item['id']
            try:
                with enforce_min_duration(min_interval):
                    drop_res = list(executor.map(selector.drop_class, drop_assocs))
                    add_res = list(executor.map(selector.add_class, add_assocs))
                    
                    # Process results
                    to_remove_drop = []
                    to_remove_add = []
                    
                    for i, (status, msg) in enumerate(drop_res):
                        if status == 0:
                            print(f"{get_time()} {drop_codes_copy[i]} 退课成功")
                            to_remove_drop.insert(0, i)
                        else:
                             print(f"{get_time()} {drop_codes_copy[i]} 退课失败: {msg}")
                            
                    for i, (status, msg) in enumerate(add_res):
                        if status == 0:
                            print(f"{get_time()} {add_codes_copy[i]} 抢课成功")
                            to_remove_add.insert(0, i)
                        else:
                            print(f"{get_time()} {add_codes_copy[i]} 抢课失败: {msg}")

                    # Update lists
                    for i in to_remove_drop:
                        drop_assocs.pop(i)
                        drop_codes_copy.pop(i)
                    for i in to_remove_add:
                        add_assocs.pop(i)
                        add_codes_copy.pop(i)

            except requests.exceptions.ConnectionError:
                dead_selectors.append(item)
                print(get_time(), f"{browser_id}号浏览器，超载/关闭！")
            except Exception as e:
                print(f"{browser_id}号浏览器异常: {e}")
                dead_selectors.append(item)
            
            if not add_codes_copy and not drop_codes_copy:
                executor.shutdown()
                return

        for r in dead_selectors:
            if r in selectors:
                selectors.remove(r)

    executor.shutdown()


def simple_solution(start_time: str, drop_codes: list[str], add_codes: list[str], username=None, password=None) -> None:
    # 清空失效的Cookies
    clear_invalid_cookies()
    
    cookies_list = get_cookies()

    if not cookies_list:
        load_cookies(username, password, num=1)
        cookies_list = get_cookies()
        
    session = login_by_cookies(cookies_list[0])

    # 选课
    selector = CourseSelector(session)

    input("按回车键开始")
    
    while get_time() < start_time:
        time.sleep(SLEEP_TIME)
    selector.drop_courses(drop_codes)
    selector.select_courses(add_codes)