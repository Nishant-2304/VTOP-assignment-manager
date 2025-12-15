#Getting needed libraries 
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
from datetime import datetime
from datetime import datetime
from ics import Calendar, Event

#Saving VTOP credentials 
VTOP_USERNAME = "name" 
VTOP_PASSWORD = "password"

#STEP 1: Open VTOP Login Page
driver = webdriver.Chrome()  # make sure chromedriver.exe is in the same folder
driver.get("https://vtop.vit.ac.in/vtop/login")  # VTOP login page

WebDriverWait(driver, 60).until(
    EC.element_to_be_clickable((By.XPATH, "//form[@id='stdForm']//a[1]"))
)
print("Opened VTOP...")

# Step 2 : Click "Student" to go to student login form
driver.find_element(By.XPATH, "//form[@id='stdForm']//a[1]").click()
WebDriverWait(driver, 60).until(
    EC.element_to_be_clickable((By.ID, "username"))
)
print("Signing in as Student")

#Step 3 : Filling in the credentials
# Fill in username and password automatically
driver.find_element(By.ID, "username").send_keys(VTOP_USERNAME)
driver.find_element(By.ID, "password").send_keys(VTOP_PASSWORD)
print("Filled in credentials...")

#Step 4: Handling CAPTCHA
# Prompt user to enter CAPTCHA manually here, and then fill it on vtop page and submit
CAPTCHA = input("Please enter the CAPTCHA as shown on the page: ")
if CAPTCHA.strip() == "":
    driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]").click()
else:
    driver.find_element(By.ID, "captchaStr").send_keys(CAPTCHA)
    driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]").click()

#Step 4.5: Waiting for login to complete
WebDriverWait(driver, 60).until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.px-3.d-flex.flex-nowrap.w-100.overflow-auto.justify-content-center.justify-content-md-start.mx-3 > a"))
)
print("Login Successfull")

#Step 5 : Clicking on Academics Tab
driver.find_element(By.CSS_SELECTOR, "div.px-3.d-flex.flex-nowrap.w-100.overflow-auto.justify-content-center.justify-content-md-start.mx-3 > a").click()
print("Clicked on Academics Tab...")
time.sleep(1)

#Step 6 : Clicking on "Digital Assignment Upload" and Selecting Semester
driver.find_element(By.CSS_SELECTOR, "div.d-flex.flex-wrap.flex-md-nowrap.mb-5.mb-md-2.pb-5.pb-md-2 > div:nth-child(2) a:nth-child(2)").click()
print("Clicked on Digital Assignment Upload...")

WebDriverWait(driver, 60).until(
    EC.visibility_of_element_located((By.ID, "semesterSubId"))
)
print("On Assignment Page...")
driver.find_element(By.ID, "semesterSubId").click()
select = Select(driver.find_element(By.ID, "semesterSubId"))
select.select_by_index(1)   #Change index for different semester, index = semester
print("Selected Semester...")

#Step 7: Opening each course one by one and scraping assignments (with retries in case of stale elements or timeouts)

NUM_COURSES = 6   # number of courses i have
MAX_RETRIES_PER_COURSE = 3

for logical_i in range(1, NUM_COURSES + 1):  # logical_i = 1..6 corresponds to rows 2..7
    attempt = 0
    success = False

    while attempt < MAX_RETRIES_PER_COURSE and not success:
        attempt += 1
        try:
            #Step A: Wait for new table to load
            table_body = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.customTable > tbody"))
            )
            # making sure that the table has atleast enough rows (as first row is header)
            WebDriverWait(driver, 60).until(
                lambda d: len(table_body.find_elements(By.TAG_NAME, "tr")) > logical_i
            )

            # STEP B: Opening the ith course
            # (ith=1 means 2nd row in table, because 1st row is header)
            # XPath chooses row index across the tbody rows directly, avoiding stale row objects
            button_xpath = f"(//table[contains(@class,'customTable')]//tbody//tr)[{logical_i+1}]//button"
            print(f"Opening course {logical_i} (attempt no. {attempt})")

            # Wait until that specific button is visible and clickable
            target_button = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, button_xpath))
            )

            # Click via JS cause this site is just so shitty ki html elements keep going stale
            driver.execute_script("arguments[0].click();", target_button)
            print(f"Clicked button for course {logical_i}")

            #Step C: Wait for assignment page to load
            go_back_button = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(normalize-space(text()), 'Go Back')]"))
            )
            print(f"Assignment table loaded for course {logical_i}")
            time.sleep(2)  # small pause to make sure table loads

            assign_table = WebDriverWait(driver, 60).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.customTable > tbody"))
            )[1]  # second table is the assignments 

            rows = assign_table.find_elements(By.TAG_NAME, "tr")

            #Step D: Process the assignment rows to find the next deadline
            # Find the next upcoming assignment deadline by looking from today's date
            today = datetime.now()
            deadlines = []

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    continue
                
                try:
                    # adjust the column index based on where the date is
                    deadline_text = cells[5].text.strip()
                    deadline = datetime.strptime(deadline_text, "%d-%b-%Y")
                except Exception as e:
                    print("Skipping row, date not in correct format:", e)
                    continue
                
                if deadline > today:
                    deadlines.append((deadline, row))

            # If we found any upcoming assignment
            if deadlines:
                deadlines.sort(key=lambda x: x[0])  # sort by soonest date
                soonest_date = deadlines[0][0]

                # Grab ALL rows with this same soonest date
                soonest_assignments = [r for d, r in deadlines if d == soonest_date]

                for assign_row in soonest_assignments:
                    cols = assign_row.find_elements(By.TAG_NAME, "td")
                    details = [c.text.strip() for c in cols]
                    print("Next Assignment:", details)
            else:
                print("No upcoming assignments for this course.")

            #Step E: Scraping the assigment details to be stored in a list 
            

            #STEP F: Click Go Back and wait for the old table to be removed
            time.sleep(2)
            go_back_button.click()
            print("Clicked Go Back button...")

            # Wait until the old table_body is removed from DOM (ensures refresh)
            WebDriverWait(driver, 60).until(EC.staleness_of(table_body))
            print(f"Returned to course list after course {logical_i}")

            success = True  # we completed this course
            time.sleep(1)   # extra breathing room before next iteration just so that i can see what is happening

        except (TimeoutException, StaleElementReferenceException) as e:
            print(f"Warning: attempt {attempt} for course {logical_i} failed: {type(e).__name__}: {e}")
            # if it's the last attempt, raise so you can see the full traceback; otherwise retry
            if attempt >= MAX_RETRIES_PER_COURSE:
                raise
            else:
                # Another wait before retrying to give VTOP a break
                time.sleep(2)

print("Exiting VTOP")