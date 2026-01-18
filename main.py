from jwc import *
from setting import *

def main():
    drop_classes = []
    add_classes = ["AI1001A.02"]
    multi_session_solution(start_time="07:59:59", stop_time="08:00:05", min_interval=0.1, drop_codes=drop_classes, add_codes=add_classes, session_number=5, username=username, password=password)

if __name__ == '__main__':
    main()
