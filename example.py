from jwc import *
from setting import *

if __name__ == '__main__':
    add_list = ['BIOL5121P.02', '008704.02', 'BIO2001.04']
    drop_list = []
    # init_cookies() # 清空数据库中的cookie数据
    # load_cookies(username, password, 10)
    cookies_list = get_cookies()
    # Robot = RobClass(Login_by_cookies(cookies_list[0]))
    # add = Robot.get_class_info(add_list)
    # print(Robot.add_class(add[0]))
    # print(add)
    multi_session_solution("17:59:58", "18:00:03", 0.1,
                           drop_list, add_list, LoginBy.cookies)
