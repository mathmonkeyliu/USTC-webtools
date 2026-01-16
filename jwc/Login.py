import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from typing import List, Dict
import sqlite3

database_name = "jwc_cookies.db"


def init_cookies():
    """初始化数据库和表结构"""
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            SESSION TEXT,
            SVRNAME TEXT,
            fine_auth_token TEXT,
            fine_remember_login TEXT
        )
    ''')
    cursor.execute('DELETE FROM records')
    conn.commit()
    conn.close()


def add_cookies(data: Dict[str, str]) -> None:
    """
    插入字典数据到数据库
    :param data: 必须包含且仅包含 SESSION, SVRNAME, fine_auth_token, fine_remember_login 四个键的字典
    :return: 插入行的ID
    """
    required_keys = {'SESSION', 'SVRNAME', 'fine_auth_token', 'fine_remember_login'}
    if set(data.keys()) != required_keys:
        raise ValueError("字典必须且只能包含 SESSION, SVRNAME, fine_auth_token, fine_remember_login 四个键")
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO records (SESSION, SVRNAME, fine_auth_token, fine_remember_login)
        VALUES (:SESSION, :SVRNAME, :fine_auth_token, :fine_remember_login)
    ''', data)
    conn.commit()
    conn.close()


def get_cookies() -> List[Dict[str, str]]:
    """
    查询数据库记录
    :return: 返回cookies的字典列表
    """
    conn = sqlite3.connect(database_name)
    conn.row_factory = sqlite3.Row  # 将结果转换为字典格式
    cursor = conn.cursor()
    base_query = "SELECT SESSION, SVRNAME, fine_auth_token, fine_remember_login FROM records"
    cursor.execute(base_query)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def delete_cookies(row_number: int) -> bool:
    """
    根据主键ID删除指定行数据
    :param row_number: 要删除记录的主键ID（正整数）
    :return: 是否成功删除（True表示有数据被删除）
    """
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM records WHERE ROWID = ?', (row_number,))
    conn.commit()
    conn.close()


def load_cookies(username: str, password: str, number: int) -> None:
    for i in range(number):
        Login_by_selenium(username, password, save_cookies=True)
        print(f"{i}号cookie保存完成")


def clear_invalid_cookies() -> int:
    cookies_list = get_cookies()
    remove_list = []
    for index, cookies in enumerate(cookies_list):
        if not LoginCheck(Login_by_cookies(cookies)):
            remove_list.insert(0, index)
            print(f"{index}号cookie失效")
    for index in remove_list:
        delete_cookies(index + 1)
        print(f"{index}号cookie已清除")
    return len(remove_list)


def Login_by_selenium(username: str, password: str, save_cookies: bool = False) -> requests.Session | None:
    """
    USTC统一身份认证自动登录
    :param username: 用户名
    :param password: 密码
    :param save_cookies: 是否保存cookie以便下次快捷登录
    :return: 可用于后续操作的session
    """
    options = Options()
    options.add_argument(f"--user-data-dir=D:/Code/ChromeCache/default")
    # options.add_argument('--headless')
    # options.add_argument('--disable-gpu')

    name_path = "#nameInput"
    password_path = "#normalLoginForm > div.login-normal-item.passwordInput.ant-row > nz-input-group > input"
    login_path = "#submitBtn"
    driver = webdriver.Chrome(options=options)
    driver.get("https://id.ustc.edu.cn/cas/login?service=https:%2F%2Fjw.ustc.edu.cn%2Fucas-sso%2Flogin")
    driver.implicitly_wait(60)

    # 输入用户名密码并点击登录
    password_input = driver.find_element(By.CSS_SELECTOR, password_path)
    password_input.clear()
    password_input.send_keys(password)
    name_input = driver.find_element(By.CSS_SELECTOR, name_path)
    name_input.clear()
    name_input.send_keys(username)
    driver.find_element(By.CSS_SELECTOR, login_path).click()

    # 确保fine_auth_token已加载出来
    while True:
        b = False
        for c in driver.get_cookies():
            if 'fine_auth_token' == c.get('name'):
                b = True
        if b:
            break
        else:
            time.sleep(1)

    # 将获取的cookie和header加入session中，然后返回
    result_session = requests.Session()
    try:
        cookies = driver.get_cookies()
        user_agent = driver.execute_script("return navigator.userAgent;")
        result_session.headers.update({"User-Agent": user_agent})
        for cookie in cookies:
            result_session.cookies.set(
                name=cookie["name"],
                value=cookie["value"],
                domain=cookie["domain"].lstrip("."),  # 移除域名前的点
                path=cookie["path"],
                secure=cookie.get("secure", False)
            )
        if save_cookies:
            insert_data = {}
            for cookie in cookies:
                insert_data[cookie["name"]] = cookie["value"]
            add_cookies(insert_data)
    finally:
        driver.quit()
        return result_session


def Login_by_cookies(cookies: Dict[str, str]) -> requests.Session:
    result_session = requests.Session()
    for key in cookies.keys():
        result_session.cookies.set(key, cookies.get(key))
    User_Agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"
    result_session.headers.update({"User-Agent": User_Agent})
    return result_session


def LoginCheck(session: requests.Session) -> bool:
    """
    检测是否登录成功
    :param session: 待检测的session
    :return: 检测结果
    """
    response = session.get("https://jw.ustc.edu.cn/home", allow_redirects=False)
    if response.status_code == 200:
        return True
    elif requests.status_codes == 302:
        return False
    else:
        return False


class LoginBy:
    cookies = "cookies"
    selenium = "selenium"
