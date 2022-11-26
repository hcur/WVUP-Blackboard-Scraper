# TODO: package with nix

import calendar
import datetime
#import getpass
import os
import sys
from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from time import sleep

def login(user, password):
    """
    Login to blackboard.
    """
    driver.get('https://blackboard.wvup.edu')
    driver.find_element_by_id("agree_button").click()
    driver.find_element_by_id("user_id").send_keys(user)
    driver.find_element_by_id("password").send_keys(password)
    driver.find_element_by_id("entry-login").click()
    sleep(1)

def scrape():
    """
    Scrape Blackboard's calendar
    for due dates, assignment names, and
    course names.

    (Probably?) Specific to WVUP's Blackboard instance.
    """
    driver.get('https://blackboard.wvup.edu/ultra/calendar')
    # sleep so blackboard can load
    sleep(2)
    driver.find_element_by_id("bb-calendar1-deadline").click()

    # set up beautifulsoup
    sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # we are now on the due dates page

    # get all courses
    attrs = {
        'analytics-id': "components.directives.calendar.deadlines.navigation.openCourseOutline"
        }
    course = soup.find_all('a', attrs=attrs)

    # get all assignments
    attrs = {
        'analytics-id': "components.directives.calendar.deadlines.navigation.openDueDateItem"
        }
    assn = soup.find_all('a', attrs=attrs)

    # get due dates
    due_dates = get_all_due_dates(soup)

    # a, c, d
    return (assn, course, due_dates)

def create_org_todo_entries(a, c, d):
    """
    Given the results of scrape() in the inputs a, c, d,
    generate org agenda compatible todo entries.
    """
    if len(a) != len(c) or len(c) != len(d):
        # each entry in each list corresponds with another.
        # a[0] goes with c[0] goes with d[0] for instance.
        #
        # if these lists are not the same length, there is a
        # problem, so return an err
        print("different lengths. err")
        return -1

    # prep return value
    ret = []

    for x in range(0, len(a)):
        # clean the texts up
        assn = a[x].get_text().strip()
        course = c[x].get_text().strip()
        due_date = d[x]

        # create todo entry
        course = course.split(":")[1]
        course = course.split("-")
        todo = "* TODO " + assn + " - " + course[0] + " " + course[1]

        # create corresponding schedule entry
        scheduled = "SCHEDULED: <"

        due_date = due_date.split(":")[1]
        due_date = due_date.split(",")[0]
        due_date = due_date.lstrip()

        # define things ahead of time
        day, m = "", ""

        # handle date values with 0- prefixes (i.e, 01, 02, etc)
        if "/" in due_date[3:5]:
            day = "0" + due_date[3]
        else:
            day = due_date[3:5]
        if "/" in due_date[0:2]:
            m = "0" + due_date[0]
        else:
            m = due_date[0:2]
        if len(due_date[6:8]) == 2:
            y = due_date[6:8]
        else:
            y = due_date[5:8]

        # create year value
        y = "20" + y
        scheduled += y + "-" + m + "-" + day

        # finalize scheduled value
        day = calendar.day_name[datetime.datetime.strptime(due_date, '%m/%d/%y').weekday()]
        scheduled += " " + day[0:3] + ">"

        # append pairing to return value
        ret.append([todo, scheduled])

    return ret

def write_entries_to_org_file(file, entries):
    """
    Given a filepath and a list of entries
    [todo, scheduled], write to the aforementioned
    filepath.
    """
    f = open(file, 'w')
    f.writelines(entries)
    f.close()

def organize_org_files(folderpath, entries):
    """
    Given a path to a folder, organize due assignments
    into .org files based on the course for which they
    are from.

        Example: folderpath/HIST-152.org
    """
    # create the folder, if needbe
    Path(folderpath).mkdir(parents=True, exist_ok=True)

    courses, f = [], ""
    for x in entries:
        course = get_course_from_entry(x[0])
        filename = folderpath + course + ".org"

        write = True
        iter = 0
        # don't overwrite if folder already exists
        if os.path.isfile(filename):
            f = open(filename, 'r')
            for line in f.readlines():
                # if line already in file, don't write
                if line == x[0] or line == x[1]:
                    write = False

                # handle done markings
                if iter == 0:
                    assn = get_assn_from_entry(x[0])
                    lineassn = get_assn_from_entry(line)

                    course = get_course_from_entry(x[0])
                    linecourse = get_course_from_entry(line)

                    if assn == lineassn:
                        status = get_status_from_entry(x[1])
                        if status == "DONE":
                            # assignment has been completed and is
                            # marked as such in the agenda
                            write = False

                # iterate through non-empty lines
                # hackish, but org-agenda entries come in pairs
                if len(line) > 1:
                    iter = (iter + 1) % 2

            f.close()

            if write:
                f = open(filename, 'a')
        else:
            f = open(filename, 'w')

        if write:
            f.write(x[0] + "\n")
            f.write(x[1] + "\n")

        f.close()

def get_course_from_entry(entry):
    """
    Parse the course from an already-formatted
    todo entry.
    """
    entry = entry.strip()
    # todo assignment - (course) (coursenumber)
    entry = entry.split("- ")[1].strip()
    entry = entry.replace(" ", "-")
    return entry

def get_date_from_entry(entry):
    """
    Parse the date from an already-formatted
    SCHEDULED entry.

    Currently unused. This function was written before
    organization scheme was finalized, and is being left
    here should it be handy in the future.
    """
    entry = entry.strip()
    # ex: SCHEDULED: <1-1-22 Fri>
    entry = entry.split("<")[1]
    entry = entry.split(" ")[0]
    # should just be date digits now
    return entry

def get_assn_from_entry(entry):
    """
    Parse the assignment name from an already-formatted
    SCHEDULED entry.
    """
    entry = entry.strip()
    # "todo assignment - (course) (coursenumber)"
    entry = entry.split(" ")[1].strip()
    # "assignment - (course) (coursenumber)"
    entry = entry.split(" ")[0].strip()
    # "assignment"
    return entry

def get_status_from_entry(entry):
    """
    Parse the completion status from an already-formatted
    SCHEDULED entry.
    """
    # "done assignment - (course) (coursenumber)"
    entry = entry.strip()
    entry = entry.split(" ")[0].strip() # possible extraneous strip() call?
    return entry

def get_all_due_dates(soup):
    """
    Return a list of due dates for every assignment in
    chronological order.
    """
    spans = soup.find_all('span')
    res = []
    for x in spans:
        if "Due date" in x.get_text():
            res.append(x.get_text())
    return res

def print_to_terminal(results):
    """
    Given the results of create_org_todo_entries() in
    results, print each todo entry and corresponding
    SCHEDULED tidbit.
    """
    for x in results:
        print(x[0])
        print(x[1])
        print("")

def main():
    # scrape.py <path> <user> <password>

    args = sys.argv

    # validate arguments
    if len(args) == 1:
        #user = getpass.getuser(prompt="blackboard login id: ")
        #password = getpass.getpass(prompt="password: ")
        print("")
        user = input("blackboard login id: ")
        password = input("password: ")
    elif len(args) < 2:
        print("No path given. Continue in current directory? (y/n) ")
        i = input(" > ")
        if i.strip().lower() == "y":
            path = os.getcwd()
        else:
            print("Exiting...")
            return 0
        #user = getpass.getuser(prompt="blackboard login id: ")
        #password = getpass.getpass(prompt="password: ")
        print("")
        user = input("blackboard login id: ")
        password = input("password: ")
    elif len(args) == 2:
        path = args[1]
        #user = getpass.getuser(prompt="blackboard login id: ")
        #password = getpass.getpass(prompt="password: ")
        print("")
        user = input("blackboard login id: ")
        password = input("password: ")
    elif len(args) < 4:
        print("Invalid number of arguments.")
        print("Ignoring: ", args[2])
        #user = getpass.getuser(prompt="blackboard login id: ")
        #password = getpass.getpass(prompt="password: ")
        print("")
        user = input("blackboard login id: ")
        password = input("password: ")
    else:
        # so as to allow entering username and password through
        # a script
        path = args[1]
        user = args[2]
        password = args[3]
        if len(args) > 4:
            print("Extraneous arguments after " + args[1] + ". Ignoring...")

    # validate path
    if path[len(path)-1] != "/":
        path = path + "/"
    if not os.path.isdir(path):
        pritnt("Given path does not exist. Exiting...")
        return -1

    global driver
    driver = webdriver.Firefox()
    login(user, password)
    (a, c, d) = scrape()
    entries = create_org_todo_entries(a, c, d)
    # print_to_terminal(entries)
    organize_org_files(path, entries)

main()
driver.quit()
