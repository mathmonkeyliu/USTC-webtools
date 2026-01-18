import time
import requests
import pickle
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from typing import List, Dict

COOKIES_FILE = "cookies.pkl"


def get_cookies() -> List[Dict[str, str]]:
    """从pickle文件读取cookies"""
    if not os.path.exists(COOKIES_FILE):
        return []
    with open(COOKIES_FILE, 'rb') as f:
        return pickle.load(f)


def save_cookies_to_file(cookies_list: List[Dict[str, str]]) -> None:
    """保存cookies列表到pickle文件"""
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(cookies_list, f)


def add_cookies(new_cookies: Dict[str, str]) -> None:
    """添加新的cookie字典到存储"""
    current_cookies = get_cookies()
    current_cookies.append(new_cookies)
    save_cookies_to_file(current_cookies)


def clear_invalid_cookies() -> int:
    cookies_list = get_cookies()
    valid_cookies = []
    removed_count = 0
    
    for index, cookies in enumerate(cookies_list):
        if login_check(login_by_cookies(cookies)):
            valid_cookies.append(cookies)
        else:
            print(f"{index}号cookie失效")
            removed_count += 1
            
    save_cookies_to_file(valid_cookies)
    return removed_count


def load_cookies(username: str, password: str, num: int) -> None:
    """批量登录并保存cookies"""
    for i in range(num):
        login_by_selenium(username, password, save_cookies=True)
        print(f"{i}号cookie保存完成")


def login_by_selenium(username: str, password: str, save_cookies: bool = False) -> requests.Session | None:
    options = Options()
    
    # options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    # options.add_argument(f"--user-data-dir=D:/Code/ChromeCache/default")

    
    name_path = "#nameInput"
    password_path = "#normalLoginForm > div.login-normal-item.passwordInput.ant-row > nz-input-group > input"
    login_path = "#submitBtn"
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://id.ustc.edu.cn/cas/login?service=https:%2F%2Fjw.ustc.edu.cn%2Fucas-sso%2Flogin")
    driver.implicitly_wait(120)

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


    # 将获取的cookie和header加入session中
    result_session = requests.Session()
    try:
        cookies = driver.get_cookies()
        user_agent = driver.execute_script("return navigator.userAgent;")
        result_session.headers.update({"User-Agent": user_agent})
        
        cookie_dict = {}
        for cookie in cookies:
            result_session.cookies.set(name=cookie["name"], value=cookie["value"], domain=cookie["domain"].lstrip("."), path=cookie["path"], secure=cookie.get("secure", False))
            cookie_dict[cookie["name"]] = cookie["value"]
            
        if save_cookies:
            # 保存所有cookie的键值对
            add_cookies(cookie_dict)
            
    finally:
        driver.quit()
        return result_session


def login_by_cookies(cookies: Dict[str, str]) -> requests.Session:
    result_session = requests.Session()
    for key, value in cookies.items():
        result_session.cookies.set(key, value)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"
    result_session.headers.update({"User-Agent": user_agent})
    return result_session


def login_check(session: requests.Session) -> bool:
    response = session.get("https://jw.ustc.edu.cn/home", allow_redirects=False)
    if response.status_code == 200:
        return True
    elif response.status_code == 302:
        return False
    else:
        return False


class LoginBy:
    cookies = "cookies"
    selenium = "selenium"
