import datetime
import re
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor
from .Login import LoginCheck
from .Error import *


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


class RobClass(object):
    _course_select_url = "https://jw.ustc.edu.cn/for-std/course-select"
    _open_turn_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/open-turns"
    _add_class_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-request"
    _drop_class_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/drop-request"
    _confirm_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-drop-response"
    _std_count_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/std-count"
    _addable_classes_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/addable-lessons"

    def __init__(self, session: requests.sessions.Session):
        self.session = session
        if not LoginCheck(self.session):
            raise InvalidSessionError()
        next_url = self.session.get(url=self._course_select_url, allow_redirects=False).next.url
        self.studentAssoc: int = int(re.search(r'\d+', next_url).group())
        response = self.session.post(url=self._open_turn_url,
                                     data={'bizTypeId': 2, 'studentId': self.studentAssoc})
        temp_dict = json.loads(response.text)
        self.TurnAssoc: int = temp_dict[0].get('id')

    def get_class_info(self, class_code: list[str], value: str = "id") -> list:
        temp_class_code = class_code.copy()
        l = len(temp_class_code)
        return_list = [None] * l
        data = {
            'turnId': self.TurnAssoc,
            'studentId': self.studentAssoc
        }
        res = self.session.post(self._addable_classes_url, data=data)
        classes_list: list[dict] = json.loads(res.text)
        for class_info in classes_list:
            for index, code in enumerate(temp_class_code):
                if class_info.get('code') == code:
                    return_list[index] = class_info.get(value)
                    l -= 1
                    break
            if l == 0:
                break
        return return_list

    def add_class(self, lessonAssoc: str | int) -> bool:
        try:
            ticket = self.session.post(url=self._add_class_url,
                                       data={'studentAssoc': self.studentAssoc, 'lessonAssoc': lessonAssoc,
                                             'courseSelectTurnAssoc': self.TurnAssoc,
                                             'scheduleGroupAssoc': '', 'virtualCost': '0'}).text
            return json.loads(self.session.post(url=self._confirm_url,
                                                data={'studentId': self.studentAssoc, 'requestId': ticket}).text).get(
                'success')
        except AttributeError:
            return False

    def add_class_quick(self, lessonAssoc: str | int) -> None:
        self.session.post(url=self._add_class_url,
                          data={'studentAssoc': self.studentAssoc, 'lessonAssoc': lessonAssoc,
                                'courseSelectTurnAssoc': self.TurnAssoc,
                                'scheduleGroupAssoc': '', 'virtualCost': '0'})

    def drop_class(self, lessonAssoc: str | int) -> bool:
        try:
            ticket = self.session.post(url=self._drop_class_url,
                                       data={'studentAssoc': self.studentAssoc, 'lessonAssoc': lessonAssoc,
                                             'courseSelectTurnAssoc': self.TurnAssoc}).text
            return json.loads(
                self.session.post(url=self._confirm_url,
                                  data={'studentId': self.studentAssoc, 'requestId': ticket}).text).get('success')
        except AttributeError:
            return False

    def drop_class_quick(self, lessonAssoc: str | int) -> None:
        self.session.post(url=self._drop_class_url,
                          data={'studentAssoc': self.studentAssoc, 'lessonAssoc': lessonAssoc,
                                'courseSelectTurnAssoc': self.TurnAssoc,
                                'scheduleGroupAssoc': '', 'virtualCost': '0'})

    def add_class_on_time(self, start_time: str, lessonAssoc_list: list[str]) -> None:
        with ThreadPoolExecutor(max_workers=len(lessonAssoc_list)) as executor:
            while True:
                if get_time() >= start_time:
                    t1 = time.time()
                    executor.map(self.add_class_quick, lessonAssoc_list)
                    t2 = time.time()
                    print(f"抢课完成，历时{t2 - t1}秒")
                    break

    def drop_class_on_time(self, start_time: str, lessonAssoc_list: list[str]) -> None:
        with ThreadPoolExecutor(max_workers=len(lessonAssoc_list)) as executor:
            while True:
                if get_time() >= start_time:
                    t1 = time.time()
                    executor.map(self.drop_class_quick, lessonAssoc_list)
                    t2 = time.time()
                    print(f"退课完成，历时{t2 - t1}秒")
                    break

    def check_persistently(self, lesson_code_list: list[str], sleep_time: int | float) -> None:
        error_count = 0
        data_list = []
        lessonAssoc_list = self.get_class_info(lesson_code_list, 'id')
        for index, lesson in enumerate(lessonAssoc_list):
            lessonAssoc_list[index] = str(lesson)
            data_list.append(("lessonIds[]", str(lesson)))
        while True:
            try:
                class_info = self.get_class_info(lesson_code_list, 'limitCount')
                res = self.session.post(self._std_count_url, data=data_list)
                res_dict: dict = json.loads(res.text)
                for index, temp_lessonAssoc in enumerate(lessonAssoc_list):
                    if res_dict[temp_lessonAssoc] < class_info[index]:
                        if self.add_class(temp_lessonAssoc):
                            print(f"{get_time()} {lesson_code_list[index]} 选课成功")
                            data_list.remove(("lessonIds[]", temp_lessonAssoc))
                        else:
                            print(f"{get_time()} {lesson_code_list[index]} 选课失败")
                if len(data_list) == 0:
                    break
                else:
                    print(f"{get_time()} {lesson_code_list} 人数已满")
                    time.sleep(sleep_time)
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_count += 1
                print(f"{get_time()} Error {e}")
                if error_count > 10:
                    break
                time.sleep(sleep_time)


def multi_session_solution(start_time: str, stop_time: str,
                           min_interval_time: int | float,
                           drop_lesson_code_list: list[str], add_lesson_code_list: list[str],
                           login_method='selenium', **kwargs) -> None:
    """
    基于多浏览器的抢课方案
    :param start_time: 开始时间（建议比实际开始时间提前）格式为??（时）:??（分）:??（秒）.??????
    :param stop_time: 结束时间（建议比实际结束时间滞后）格式为??（时）:??（分）:??（秒）.??????
    :param min_interval_time: 每个浏览器的最少抢课时间
    :param drop_lesson_code_list: 需退课的课程编号列表
    :param add_lesson_code_list: 需添加的课程编号列表
    :param login_method: 登录方法（可以使用Login库中的LoginBy类）
    """

    # 进行session_number个浏览器的登录
    RobotList = []
    if login_method == 'cookies':
        from .Login import Login_by_cookies, get_cookies, clear_invalid_cookies
        clear_invalid_cookies()
        cookies_list = get_cookies()
        for index in range(len(get_cookies())):
            RobotList.append(RobClass(Login_by_cookies(cookies_list[index])))
            print(f"{index}号浏览器登录完成")
    elif login_method == 'selenium':
        username = kwargs.get("username")
        password = kwargs.get("password")
        session_number = kwargs.get("session_number")
        for index in range(session_number):
            from .Login import Login_by_selenium
            RobotList.append(RobClass(Login_by_selenium(username, password)))
            print(f"{index}号浏览器登录完成")
        # 检查浏览器的状态
        error_list = []
        for index in range(session_number):
            session_status = LoginCheck(RobotList[index].session)
            print(f"{index}号浏览器状态：\t{session_status}")
            if not session_status:
                # 将失效的session的索引倒序存入error_list中
                error_list.insert(0, index)
        # 去除失效的session
        for i in error_list:
            RobotList.pop(i)
    else:
        raise ValueError("method is not supported")

    # 获取课程对应的lessonAssoc
    drop_lesson_code_list_copy = drop_lesson_code_list.copy()
    add_lesson_code_list_copy = add_lesson_code_list.copy()
    drop_lessonAssoc_list = RobotList[0].get_class_info(drop_lesson_code_list_copy, 'id')
    add_lessonAssoc_list = RobotList[0].get_class_info(add_lesson_code_list_copy, 'id')

    # 开始抢课
    input("按回车键开始")
    executor = ThreadPoolExecutor(max_workers=len(drop_lesson_code_list) + len(add_lesson_code_list))

    # 待时间到达start_time后启动
    while True:
        if get_time() >= start_time:
            break

    # 将多个session循环开始抢课
    while get_time() < stop_time:
        remove_list = []
        if len(RobotList) == 0:
            executor.shutdown()
            return None

        for index, RobRobot in enumerate(RobotList):
            print(get_time(), f'{index}号浏览器，启动！')
            try:
                with enforce_min_duration(min_interval_time):
                    drop_results = executor.map(RobRobot.drop_class, drop_lessonAssoc_list)
                    add_results = executor.map(RobRobot.add_class, add_lessonAssoc_list)
                    drop_remove_list = []
                    add_remove_list = []
                    for index2, result in enumerate(drop_results):
                        if result:
                            print(f"{get_time()} {drop_lesson_code_list_copy[index2]} 退课成功")
                            drop_remove_list.insert(0, index2)
                    for index2, result in enumerate(add_results):
                        if result:
                            print(f"{get_time()} {add_lesson_code_list_copy[index2]} 抢课成功")
                            add_remove_list.insert(0, index2)
                    for i in drop_remove_list:
                        drop_lessonAssoc_list.pop(i)
                        drop_lesson_code_list_copy.pop(i)
                    for i in add_remove_list:
                        add_lessonAssoc_list.pop(i)
                        add_lesson_code_list_copy.pop(i)
            except requests.exceptions.ConnectionError:
                remove_list.insert(0, index)
                print(get_time(), f'{index}号浏览器，超载！！！')
                print(get_time(), f'{index}号浏览器，关闭！')
            except Exception as e:
                print(f"{index}号浏览器异常错误{e}")
                print(get_time(), f'{index}号浏览器，关闭！')
            else:
                print(get_time(), f'{index}号浏览器，关闭！')
            if len(add_lesson_code_list_copy) == 0 and len(drop_lesson_code_list_copy) == 0:
                executor.shutdown()
                return None
        for index in remove_list:
            RobotList.pop(index)

    executor.shutdown()
    return None


def multi_session_solution_quick(start_time: str, stop_time: str,
                           min_interval_time: int | float,
                           drop_lesson_code_list: list[str], add_lesson_code_list: list[str],
                           login_method='selenium', **kwargs) -> None:
    """
    基于多浏览器的抢课方案（快速版）
    :param start_time: 开始时间（建议比实际开始时间提前）格式为??（时）:??（分）:??（秒）.??????
    :param stop_time: 结束时间（建议比实际结束时间滞后）格式为??（时）:??（分）:??（秒）.??????
    :param min_interval_time: 每个浏览器的最少抢课时间
    :param drop_lesson_code_list: 需退课的课程编号列表
    :param add_lesson_code_list: 需添加的课程编号列表
    :param login_method: 登录方法（可以使用Login库中的LoginBy类）
    """

    # 进行session_number个浏览器的登录
    RobotList = []
    if login_method == 'cookies':
        from .Login import Login_by_cookies, get_cookies, clear_invalid_cookies
        clear_invalid_cookies()
        cookies_list = get_cookies()
        for index in range(len(get_cookies())):
            RobotList.append(RobClass(Login_by_cookies(cookies_list[index])))
            print(f"{index}号浏览器登录完成")
    elif login_method == 'selenium':
        username = kwargs.get("username")
        password = kwargs.get("password")
        session_number = kwargs.get("session_number")
        for index in range(session_number):
            from .Login import Login_by_selenium
            RobotList.append(RobClass(Login_by_selenium(username, password)))
            print(f"{index}号浏览器登录完成")
        # 检查浏览器的状态
        error_list = []
        for index in range(session_number):
            session_status = LoginCheck(RobotList[index].session)
            print(f"{index}号浏览器状态：\t{session_status}")
            if not session_status:
                # 将失效的session的索引倒序存入error_list中
                error_list.insert(0, index)
        # 去除失效的session
        for i in error_list:
            RobotList.pop(i)
    else:
        raise ValueError("method is not supported")

    # 获取课程对应的lessonAssoc
    drop_lessonAssoc_list = RobotList[0].get_class_info(drop_lesson_code_list, 'id')
    add_lessonAssoc_list = RobotList[0].get_class_info(add_lesson_code_list, 'id')

    input("按回车键开始")
    executor = ThreadPoolExecutor()
    while True:
        if get_time() >= start_time:
            break

    try:
        while True:
            for index, RobRobot in enumerate(RobotList):
                with enforce_min_duration(min_interval_time):
                    print(get_time(), f'{index}号浏览器，启动！')
                    executor.map(RobRobot.drop_class_quick, drop_lessonAssoc_list)
                    executor.map(RobRobot.add_class_quick, add_lessonAssoc_list)
                    print(get_time(), f'{index}号浏览器，关闭！')

    except KeyboardInterrupt:
        executor.shutdown()
        return None

    except Exception as e:
        print(e)
        executor.shutdown()
        return None
