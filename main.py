from jwc import *
from setting import *

def main():
    drop_classes = ["AI1001A.02"]
    add_classes = ["BIO3501.01"]
    multi_session_solution(start_time="11:59:58", stop_time="12:00:05", min_interval=0.1, drop_codes=drop_classes, add_codes=add_classes, login_method='selenium', session_number=10, username=username, password=password)

if __name__ == '__main__':
    main()
