import re
import sys

user_regex = r'(?:/user/show/)(\d+-[a-zA-Z0-9-]+)'


def parse(data):
    users = re.findall(user_regex, data)
    return set(users)


def main():
    if len(sys.argv) < 3:
        print("[+] Usage: user_parser.py INPUT_FILE OUTPUT_FILE")
        exit()
    users = parse(open(sys.argv[1], 'r', encoding='utf-8').read())
    with open(sys.argv[2], 'w') as fp:
        fp.write("\n".join(users))
    print(f"[+] {len(users)} users found")
    # print(users)


main()
