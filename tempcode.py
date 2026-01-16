import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from typing import List, Dict
import sqlite3

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