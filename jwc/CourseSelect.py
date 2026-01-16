import datetime
import re
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor
from .login import login_check, login_by_cookies, get_cookies, clear_invalid_cookies, login_by_selenium

def get_time():
    return datetime.datetime.now().strftime('%H:%M:%S.%f')


class enforce_min_duration:
    def __init__(self, min_duration):
        self.min_duration = min_duration

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        if elapsed < self.min_duration:
            time.sleep(self.min_duration - elapsed)


class CourseSelector:
    _course_select_url = "https://jw.ustc.edu.cn/for-std/course-select"
    _open_turn_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/open-turns"
    _add_class_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-request"
    _drop_class_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/drop-request"
    _confirm_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-drop-response"
    _std_count_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/std-count"
    _addable_classes_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/addable-lessons"

    def __init__(self, session: requests.Session):
        self.session = session
        if not login_check(self.session):
            raise Exception("Session invalid")
        
        # Initialize selection info (Student ID and Turn ID)
        next_url = self.session.get(url=self._course_select_url, allow_redirects=False).next.url
        self.student_assoc = int(re.search(r'\d+', next_url).group())
        
        response = self.session.post(url=self._open_turn_url, 
                                   data={'bizTypeId': 2, 'studentId': self.student_assoc})
        # Check if response is valid JSON array
        try:
            data = json.loads(response.text)
            if data and isinstance(data, list):
                self.turn_assoc = data[0].get('id')
            else:
                raise Exception(f"Failed to get turn info: {response.text}")
        except json.JSONDecodeError:
            raise Exception(f"Failed to parse turn response: {response.text}")

    def get_class_info(self, class_codes: list[str], value: str = "id") -> list:
        temp_codes = class_codes.copy()
        remaining = len(temp_codes)
        result = [None] * remaining
        
        data = {
            'turnId': self.turn_assoc,
            'studentId': self.student_assoc
        }
        res = self.session.post(self._addable_classes_url, data=data)
        try:
            classes_list = json.loads(res.text)
        except json.JSONDecodeError:
            print(f"Error parsing class list: {res.text}")
            return result

        for class_info in classes_list:
            for idx, code in enumerate(temp_codes):
                if class_info.get('code') == code:
                    result[idx] = class_info.get(value)
                    remaining -= 1
                    break
            if remaining == 0:
                break
        return result

    def add_class(self, lesson_assoc: str | int) -> bool:
        try:
            data = {
                'studentAssoc': self.student_assoc, 
                'lessonAssoc': lesson_assoc, 
                'courseSelectTurnAssoc': self.turn_assoc, 
                'scheduleGroupAssoc': '', 
                'virtualCost': '0'
            }
            ticket = self.session.post(url=self._add_class_url, data=data).text
            res = self.session.post(url=self._confirm_url, data={'studentId': self.student_assoc, 'requestId': ticket})
            return json.loads(res.text).get('success')
        except (AttributeError, json.JSONDecodeError):
            return False


    def drop_class(self, lesson_assoc: str | int) -> bool:
        try:
            data = {
                'studentAssoc': self.student_assoc, 
                'lessonAssoc': lesson_assoc, 
                'courseSelectTurnAssoc': self.turn_assoc
            }
            ticket = self.session.post(url=self._drop_class_url, data=data).text
            res = self.session.post(url=self._confirm_url, 
                                  data={'studentId': self.student_assoc, 'requestId': ticket}).text
            return json.loads(res).get('success')
        except (AttributeError, json.JSONDecodeError):
            return False


    def select_courses(self, course_codes: list[str]) -> None:
        """
        批量选课便捷方法
        :param course_codes: 课程代码列表，如 ['BIOL5121P.02', '008704.02']
        """
        if not course_codes:
            return

        print(f"正在获取课程ID: {course_codes}")
        course_ids = self.get_class_info(course_codes, 'id')
        
        for i, code in enumerate(course_codes):
            course_id = course_ids[i]
            if course_id:
                print(f"正在尝试选择 {code} (ID: {course_id})...")
                if self.add_class(course_id):
                    print(f"成功选择 {code}")
                else:
                    print(f"选择 {code} 失败")
            else:
                print(f"未找到课程 {code} 的信息")



def multi_session_solution(start_time: str, stop_time: str, 
                         min_interval: int | float, 
                         drop_codes: list[str], add_codes: list[str], 
                         login_method='selenium', **kwargs) -> None:
    """基于多浏览器的抢课方案"""
    selectors = [] 
    
    if login_method == 'cookies':
        clear_invalid_cookies()
        cookies_list = get_cookies()
        for idx, cookies in enumerate(cookies_list):
            try:
                sess = login_by_cookies(cookies)
                selector = CourseSelector(sess)
                selectors.append({'selector': selector, 'id': idx})
                print(f"{idx}号浏览器登录完成")
            except Exception as e:
                print(f"{idx}号浏览器初始化失败: {e}")
                
    elif login_method == 'selenium':
        username = kwargs.get("username")
        password = kwargs.get("password")
        count = kwargs.get("session_number")
        for i in range(count):
            try:
                sess = login_by_selenium(username, password)
                selector = CourseSelector(sess)
                selectors.append({'selector': selector, 'id': i})
                print(f"{i}号浏览器登录完成")
            except Exception as e:
                print(f"{i}号浏览器登录/初始化失败: {e}")
    else:
        raise ValueError("method is not supported")

    if not selectors:
        print("无可用session")
        return

    # Use first selector to resolve IDs
    main_selector = selectors[0]['selector']
    drop_assocs = main_selector.get_class_info(drop_codes, 'id')
    add_assocs = main_selector.get_class_info(add_codes, 'id')
    
    drop_codes_copy = drop_codes.copy()
    add_codes_copy = add_codes.copy()

    input("按回车键开始")
    executor = ThreadPoolExecutor(max_workers=len(drop_codes) + len(add_codes))

    while get_time() < start_time:
        pass

    while get_time() < stop_time:
        if not selectors:
            break
            
        dead_selectors = []
        for item in selectors:
            selector = item['selector']
            browser_id = item['id']
            print(get_time(), f"{browser_id}号浏览器，启动！")
            try:
                with enforce_min_duration(min_interval):
                    drop_res = list(executor.map(selector.drop_class, drop_assocs))
                    add_res = list(executor.map(selector.add_class, add_assocs))
                    
                    # Process results
                    to_remove_drop = []
                    to_remove_add = []
                    
                    for i, success in enumerate(drop_res):
                        if success:
                            print(f"{get_time()} {drop_codes_copy[i]} 退课成功")
                            to_remove_drop.insert(0, i)
                            
                    for i, success in enumerate(add_res):
                        if success:
                            print(f"{get_time()} {add_codes_copy[i]} 抢课成功")
                            to_remove_add.insert(0, i)

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
