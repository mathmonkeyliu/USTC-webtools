import requests.exceptions

from jwc import *
from setting import *

if __name__ == '__main__':
    test_list = ['MED3019.01', '001664KS.01', '206708.01', 'BIO2002.01', 'ESS1507.01', 'HS1612.03',
                 'HS1658.01', '001665KS.01', 'PHYS1005A.09', 'PHYS4703.01']
    init_cookies()
    load_cookies(username, password, 1)
    cookies = get_cookies()
    Robot = RobClass(Login_by_cookies(cookies[0]))
    a = Robot.get_class_info(['MED3019.01', '001664KS.01', '206708.01', 'BIO2002.01', 'ESS1507.01', 'HS1612.03', 'HS1658.01', '001665KS.01', 'PHYS1005A.09', 'PHYS4703.01'])
    try:
        while True:
            for i in a:
                print(Robot.add_class(i))
    except requests.exceptions.ConnectionError:
        print("fnaois")
        print(LoginCheck(Robot.session))
        time.sleep(10)
    for i in a:
        print(Robot.add_class(i))

