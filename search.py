import requests
import time
import random
import re
from progress.bar import Bar
from bs4 import BeautifulSoup

SIGN_IN_URL = "https://www.goodreads.com/user/sign_in"
HOME_URL = "https://www.goodreads.com/"
COMPARE_URL = "https://www.goodreads.com/user/compare/{USER}"
SIGN_OUT_URL = "https://www.goodreads.com/user/sign_out?ref=nav_profile_signout"
FRIENDS_URL = "https://www.goodreads.com/friend/user/{USER}?page={page_num}"


username, password = "", ""
session = requests.session()


def send_request(url, post=False, data=None, retry=7):
    while retry:
        try:
            if post:
                res = session.post(url, data=data, timeout=20)
            else:
                res = session.get(url, timeout=20)
            return res
        except:
            retry -= 1
    return ""


def parse(data):
    user_regex = r'(?:/user/show/)(\d+-[a-zA-Z0-9-]+)'
    users = re.findall(user_regex, data)
    users = [user for user in users if len(user) > 5]
    return set(users)


def rand_sleep():
    time.sleep(random.randint(00, 150) / 100)


def compare(user):
    try:
        rand_sleep()
        res = send_request(COMPARE_URL.replace("{USER}", user))
        # print(res.status_code)
        soup = BeautifulSoup(res.text, "html.parser")
        book_stats = soup.findAll("div", class_="readable")
        taste_stats = soup.findAll("p", class_="readable")
        # when there is a number in name, it gets added. remove that
        # No common books
        if not book_stats or not taste_stats:
            return "*", "*", "0", "0", "0", "*", "*"
        if "don't have" in taste_stats[0].text:
            return "*", "*", "0", "0", "0", "*", "*"

        user_books = re.findall(r'(\d+)(?:\n)', book_stats[0].text) or ["", ""]
        books_common = re.findall(r'(\d+)(?: )', book_stats[1].text) or [""]
        common_percent = re.findall(r'([\d.]+)(?:%)', book_stats[1].text) or ["", ""]
        my_books = re.findall(r'\d+', book_stats[2].text) or ["", ""]
        taste_percent = re.findall(r'([\d.]+)(?:%)', taste_stats[0].text) or [""]

        return *user_books, *books_common, *common_percent, *my_books, *taste_percent
    except:
        return "", "", "", "", "", "", "", ""


def get_form_details(form):
    inputs = []
    for input_tag in form.find_all("input"):
        # get type of input form control
        input_type = input_tag.attrs.get("type", "text")
        # get name attribute
        input_name = input_tag.attrs.get("name")
        # get the default value of that input tag
        input_value = input_tag.attrs.get("value", "")
        # add everything to that list
        inputs.append({"type": input_type, "name": input_name, "value": input_value})
    return inputs


def login_with_cookies():
    """
    In case captcha blocks login, maybe we can login in browser and use those cookies to bypass it ?
    :return:
    """
    pass


def login(username, password):
    res = send_request(SIGN_IN_URL)
    soup = BeautifulSoup(res.text, "html.parser")
    form = soup.find_all("form")[0]
    inputs = get_form_details(form)
    # print(inputs)
    data = {}
    for input_tag in inputs:
        if (tag_name := input_tag['name']) == 'user[email]':
            data[tag_name] = username
        elif (tag_name := input_tag['name']) == 'user[password]':
            data[tag_name] = password
        elif (tag_name := input_tag['name']) == 'remember_me':
            data[tag_name] = 'on'
        else:
            data[input_tag['name']] = input_tag['value']
    rand_sleep()
    res = send_request(SIGN_IN_URL, data=data, post=True)
    if "Sorry, that email or password isn't right" not in res.text and \
            "Please enter your password and complete the captcha to continue." not in res.text:
        print("[+] Login successful")


def get_friends(user):
    print(f"[+]Enumerating {user.strip()}")
    page_no = 1
    users = set()
    while True:
        fr_url = FRIENDS_URL.replace("{USER}", user).replace("{page_num}", str(page_no))
        print(f"\t[*] {page_no}   \r", end="")
        rand_sleep()
        res = send_request(fr_url)
        if not res:
            print(f"\n\t[+]{len(users)} users enumerated. Aborting")
            return users
        users.update(parse(res.text))
        soup = BeautifulSoup(res.text, "html.parser")
        page_end = soup.findAll("span", class_="next_page disabled")
        if page_end or "no friends yet!" in res.text:
            print(f"\n\t[+]{len(users)} users enumerated")
            return users
        page_no += 1


def main():
    users_file = r'users.txt'
    login(username, password)
    users = open(users_file, 'r', encoding='utf-8').readlines()
    print(f"[+]{len(users)} Users loaded")
    friends = set()
    fp = open('friends.txt', 'w')
    for user in users:
        friends.update(user)
        friends.update(get_friends(user))
    fp.write("\n".join(friends))
    fp.close()
    print(f"[+]Getting compare data for {len(friends)} users")
    bar = Bar(max=len(friends))
    with open('output.csv', 'w') as fp:
        fp.write("User,Users books,Users books not in common,Books in common,% of my library,% of users library,"
                 "My books, My books not in common,taste%\n")
        for user in friends:
            fp.write(f"{user.strip()}," + ",".join(compare(user.strip()))+"\n")
            bar.next()
    bar.finish()
    send_request(SIGN_OUT_URL)
    print("[+] Output written to file")


main()
