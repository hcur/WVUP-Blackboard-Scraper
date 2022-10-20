# WVUP Blackboard Scraper

This repository contains a script that will login to WVUP's Blackboard instance,
scrape the due dates segment for upcoming assignments, and output these
assignments in .org files compatible with org-agenda. The files are
seperated by course; different courses are wrote to different files, with the
filenames reflecting this. Selenium is used to automate this task and used
in conjunction with BeautifulSoup to scrape the "Due Dates" segment of the calendar.
Your mileage may vary, and this very likely won't work on other Blackboard instances
without some reworking of the `scrape()` function.

This script requires *exactly* 1 argument, as shown below:

    python3 scrape.py <org file output path> 

Note: omit the trailling "/" from the path you input. Example:

    correct: ~/org
    incorrect: ~/org/

The script will then prompt you for your login ID and password and proceed
to generate the results. Note that it will throw an error if you don't have
write permissions for the directory passed.
