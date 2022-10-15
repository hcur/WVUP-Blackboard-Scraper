import calendar
import datetime
import sys
from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from time import sleep

user = ""
password = ""
driver = webdriver.Firefox()

def login():
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
        due_date = due_date.split(":" )[1]
        due_date = due_date.split(", ")[0].strip()
        
        scheduled += due_date

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
        filename = folderpath + "/" + course + ".org"
        if course not in courses:
            courses.append(course)
            f = open(filename, 'w')
        else:
            f = open(filename, 'a')

        f.write(x[0] + "\n")
        f.write(x[1] + "\n")
        f.close()

def get_course_from_entry(entry):
    """
    Parse the course from an already-formatted
    todo entry.
    """
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
    # ex: SCHEDULED: <1-1-22 Fri>
    entry = entry.split("<")[1]
    entry = entry.split(" ")[0]
    # should just be date digits now
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
    # ugly argument parsing, maybe rewrite in the future?
    args = sys.argv
    if len(args) == 3:
        # python3 main.py ~/s/org/agenda <username> <password>
        path = args[0]
        id = args[1]
        password = args[2]
    else:
        print("Incorrect number of arguments. Exiting...")

    login()
    (a, c, d) = scrape()
    entries = create_org_todo_entries(a, c, d)
    # print_to_terminal(entries)
    organize_org_files(path, entries)

main()
driver.quit()
