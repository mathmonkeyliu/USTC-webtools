import datetime
import re
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor
from .login import login_check, login_by_cookies, get_cookies, clear_invalid_cookies, login_by_selenium, load_cookies
from urllib.parse import urlencode, urljoin

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
    _change_class_url = "https://jw.ustc.edu.cn/for-std/course-adjustment-apply/change-class-request"

    def __init__(self, session: requests.Session):
        self.session = session
        if not login_check(self.session):
            raise Exception("Session invalid")
        
        # Initialize selection info (Student ID and Turn ID)
        next_url = self.session.get(url=self._course_select_url, allow_redirects=False).next.url
        self.student_assoc = int(re.search(r'\d+', next_url).group())
        
        response = self.session.post(url=self._open_turn_url, data={'bizTypeId': 2, 'studentId': self.student_assoc})
        # Check if response is valid JSON array
        try:
            data = json.loads(response.text)
            if data and isinstance(data, list):
                self.turn_assoc = data[0].get('id')
            else:
                raise Exception(f"Failed to get turn info: {response.text}")
        except json.JSONDecodeError:
            raise Exception(f"Failed to parse turn response: {response.text}")

        # get semester assoc
        select_url = f"https://jw.ustc.edu.cn/for-std/course-select/{self.student_assoc}/turn/{self.turn_assoc}/select"
        response = self.session.get(url=select_url)

        try:
            self.semester_assoc = int(re.findall(r'semesterId: (\d*),', response.text)[0])
        except Exception as e:
            raise Exception(f"Failed to get semester info: {e}")

    def get_class_info(self, class_codes: list[str], value: str = "id") -> list:
        """
        获取课程信息
        :param class_codes: 课程代码列表，如 ['BIOL5121P.02', '008704.02']
        :param value: 需要获取的键，如 'id' 或 'limitCount'
        :return: 键对应的值的列表，如 [123456, 123457]
        """
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
        return result

    def add_class(self, lesson_assoc: str | int) -> tuple[int, str]:
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

            # weird thing in 2026.1.17
            if res.status_code == 200 and res.text == "null":
                return 1, "Success submit, but result unknown"
            
            response_data = json.loads(res.text)
            if response_data.get('success'):
                return 0, None
            
            error_message = response_data.get('errorMessage')
            if error_message:
                return 1, error_message.get('text', "Unknown Error")
            return 1, "Unknown Error"
        except Exception as e:
            return 2, str(e)


    def drop_class(self, lesson_assoc: str | int) -> tuple[int, str]:
        try:
            data = {
                'studentAssoc': self.student_assoc, 
                'lessonAssoc': lesson_assoc, 
                'courseSelectTurnAssoc': self.turn_assoc
            }
            ticket = self.session.post(url=self._drop_class_url, data=data).text
            res = self.session.post(url=self._confirm_url, data={'studentId': self.student_assoc, 'requestId': ticket}).text
            
            # weird thing in 2026.1.17
            if res.status_code == 200 and res.text == "null":
                return 1, "Success submit, but result unknown"
            
            response_data = json.loads(res)
            if response_data.get('success'):
                return 0, None
            
            error_message = response_data.get('errorMessage')
            if error_message:
                return 1, error_message.get('text', "Unknown Error")
            return 1, "Unknown Error"
        except Exception as e:
            return 2, str(e)


    def select_courses(self, course_codes: list[str]) -> None:
        """
        批量选课便捷方法
        :param course_codes: 课程代码列表，如 ['BIOL5121P.02', '008704.02']
        """
        if not course_codes:
            return
        
        course_ids = self.get_class_info(course_codes, 'id')
        
        for i, code in enumerate(course_codes):
            course_id = course_ids[i]
            if course_id:
                print(f"正在尝试选择 {code} (ID: {course_id})...")
                status, msg = self.add_class(course_id)
                if status == 0:
                    print(f"成功选择 {code}")
                else:
                    print(f"选择 {code} 失败: {msg}")
            else:
                print(f"未找到课程 {code} 的信息")
            time.sleep(0.5)


    def change_course(self, prev_course: list[str], new_course: list[str], reason: str = "换课") -> None:
        prev_id = self.get_class_info(prev_course, 'id')
        new_id = self.get_class_info(new_course, 'id')

        self.semester_assoc = 421

        for prev_id, new_id in zip(prev_id, new_id):
            if prev_id is None or new_id is None:
                continue
            
            data = {
                "saveCmds": [{
                    "oldLessonAssoc": prev_id,
                    "newLessonAssoc": new_id,
                    "studentAssoc": self.student_assoc,
                    "semesterAssoc": self.semester_assoc,
                    "bizTypeAssoc": 2,
                    "applyReason": reason,
                    "applyTypeAssoc": 5,
                    "scheduleGroupAssoc": None
                }],
                "studentAssoc": self.student_assoc,
                "semesterAssoc": self.semester_assoc,
                "bizTypeAssoc": 2,
                "applyTypeAssoc": 5,
                "courseSelectTurnAssoc": self.turn_assoc
            }

            params = {
                "lessonAssoc": new_id,
                "oldLessonId": prev_id,
                "turnId": self.turn_assoc,
                "bizTypeAssoc": 2,
                "semesterAssoc": self.semester_assoc,
                "studentAssoc": self.student_assoc,
                "applyTypeAssoc": 5,
                "REDIRECT_URL": f"/for-std/course-adjustment-apply/change-class-apply/apply?turnId={self.turn_assoc}&lessonId={prev_id}&studentId={self.student_assoc}&semesterId={self.semester_assoc}&bizTypeId=2&REDIRECT_URL=null"
            }

            headers = {
                "referer": urljoin(self._change_class_url, "?" + urlencode(params))
            }

            try:
                res = self.session.post(url=self._change_class_url, json=data, headers=headers)

                if res.status_code != 200:
                    print(f"{prev_course} -> {new_course} 出现异常: {res.status_code}")
                    continue

                res = json.loads(res.text)

                if res.get('verifySuccess'):
                    print(f"{prev_course} -> {new_course} 换课成功")

                else:
                    print(f"{prev_course} -> {new_course} 换课失败，原因: {res.get('errors').get('allErrors')[0].get('text')}")

            except Exception as e:
                print(f"{prev_course} -> {new_course} 出现异常: {e}")
                continue

        return

    def wait_courses(self, course_codes: list[str], time_interval: int = 5, update_interval: int = 3600) -> None:
        """
        等待课程
        :param course_codes: 课程代码列表，如 ['BIOL5121P.02', '008704.02']
        :param time_interval: 等待时间间隔
        :param update_interval: 更新时间间隔
        """
        def update():
            course_ids = self.get_class_info(course_codes, 'id')
            limit_counts = self.get_class_info(course_codes, 'limitCount')

            for index, course_id in enumerate(course_ids):
                if course_id is None:
                    print(f"课程 {course_codes[index]} 不存在")
                    course_codes.pop(index)
                    course_ids.pop(index)
                    limit_counts.pop(index)
                    continue

            return course_ids, limit_counts

        course_ids, limit_counts = update()
        last_update = time.time()
        data = {'lessonIds[]': course_ids}
        while True:
            response = self.session.post(url=self._std_count_url, data=data)
            response_data = json.loads(response.text)
            try:
                for index, course_id in enumerate(course_ids):
                    if response_data.get(str(course_id)) < limit_counts[index]:
                        _, msg = self.add_class(course_id)
                        print(f"课程 {course_codes[index]} 出现空位，完成抢课：{msg}")
                        course_codes.pop(index)
                        course_ids.pop(index)
                        limit_counts.pop(index)
                print(f"剩余课程：{course_codes}")
                
            except Exception as e:
                print(f"出现异常: {e}")

            if time.time() - last_update > update_interval:
                course_ids, limit_counts = update()
                print(f"更新课程信息: {course_codes}")
                last_update = time.time()

            time.sleep(time_interval)



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
