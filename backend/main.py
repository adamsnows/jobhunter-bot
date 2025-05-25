import time, random, os, csv
import logging
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

from bs4 import BeautifulSoup
import pickle
import pandas as pd
from urllib.request import urlopen
import urllib.parse

import re
import yaml
from datetime import datetime, timedelta

log = logging.getLogger(__name__)
retrieveCookies = False

# LINUX BOX:
# from pyvirtualdisplay import Display
# display = Display(visible=1, size=(1920, 1080))
# display.start()
# s = webdriver.chrome.service.Service('/usr/bin/chromedriver')
# driver = webdriver.Chrome(service=s)

driver = webdriver.Chrome()

stealth(
    driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

def setupLogger():
    dt = datetime.strftime(datetime.now(), "%m_%d_%y %H_%M_%S ")

    if not os.path.isdir("./logs"):
        os.mkdir("./logs")

    logging.basicConfig(
        filename=("./logs/" + str(dt) + "applyJobs.log"),
        filemode="w",
        format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
        datefmt="./logs/%d-%b-%y %H:%M:%S",
    )

    log.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    c_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S"
    )
    c_handler.setFormatter(c_format)
    log.addHandler(c_handler)


class EasyApplyBot:
    setupLogger()
    # MAX_SEARCH_TIME is 10 hours by default, feel free to modify it
    MAX_SEARCH_TIME = 10 * 60 * 60

    def __init__(
        self,
        username=None,
        password=None,
        filename="output.csv",
        blacklistCompanies=[],
        blackListTitles=[],
        positions=[],
        locations=[],
        keywords=[],
    ):

        log.info("LinkedIn JobAlert Bot by Landon Crabtree.")
        log.info("Forked from LinkedIn-Easy-Apply-Bot by nicolomantini")

        self.appliedJobIDs = self.get_appliedIDs(filename) if self.get_appliedIDs(filename) != None else []
        self.filename = filename
        self.options = self.browser_options()
        self.browser = driver
        self.wait = WebDriverWait(self.browser, 5)
        self.blacklistCompanies = blacklistCompanies
        self.blackListTitles = blackListTitles
        self.positions = positions
        self.locations = locations
        self.keywords = keywords
        self.collected_emails = []  # Lista para armazenar e-mails coletados

        log.info(f"Loaded {len(self.appliedJobIDs)} applied job IDs from {filename}")

        self.authenticate(username, password)

    def get_appliedIDs(self, filename):
        try:
            df = pd.read_csv(
                filename,
                header=None,
                names=["timestamp", "jobID", "job", "company", "matches", "result"],
                lineterminator="\n",
                encoding="utf-8",
            )

            df["timestamp"] = pd.to_datetime(
                df["timestamp"], format="%Y-%m-%d %H:%M:%S"
            )
            df = df[df["timestamp"] > (datetime.now() - timedelta(days=7))]
            jobIDs = list(df.jobID)
            return jobIDs
        except Exception as e:
            return None

    def browser_options(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        return options

    def authenticate(self, username, password):
        # Try to load existing cookies first
        if self.load_cookies():
            log.info("Loaded saved cookies, checking if still logged in...")
            self.browser.get("https://www.linkedin.com/feed/")
            time.sleep(3)

            # Check if we're successfully logged in with cookies
            if "feed" in self.browser.current_url:
                log.info("Successfully logged in using saved cookies!")
                return
            else:
                log.info("Saved cookies are expired or invalid, need manual login...")

        # If no cookies or cookies expired, proceed with manual login
        log.info("Please login manually to LinkedIn...")
        self.browser.get(
            "https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin"
        )

        # Wait for manual login by checking for the presence of the feed page
        while True:
            try:
                # Check if we're on the feed page or jobs page
                if "feed" in self.browser.current_url or "jobs" in self.browser.current_url:
                    log.info("Successfully logged in!")
                    # Save cookies after successful login
                    self.save_cookies()
                    break
                time.sleep(2)  # Check every 2 seconds
            except:
                continue

        time.sleep(3)  # Give a little extra time for the page to fully load

    def fill_data(self):
        self.browser.set_window_position(1, 1)
        self.browser.maximize_window()

    def start_apply(self):
        self.fill_data()
        log.info("Starting feed search for 'hiring full stack developer'...")

        # Go directly to content search URL
        search_query = "hiring full stack developer"
        encoded_query = urllib.parse.quote(search_query)
        self.browser.get(f"https://www.linkedin.com/search/results/content/?keywords={encoded_query}&origin=GLOBAL_SEARCH_HEADER&sortBy=%22date_posted%22")
        time.sleep(3)

        try:
            # Wait for the content to load
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-results-container"))
            )

            self.scroll_and_collect_posts()

        except Exception as e:
            log.error(f"Error during feed search: {str(e)}")

    def scroll_and_collect_posts(self):
        log.info("Collecting posts from feed...")
        posts_processed = set()
        scroll_count = 0
        max_scrolls = 10  # Adjust this number to control how many times to scroll

        while scroll_count < max_scrolls:
            try:
                # Wait for posts to load
                WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ember-view"))
                )

                # Find all post containers
                posts = self.browser.find_elements(By.CSS_SELECTOR, ".ember-view .feed-shared-update-v2")

                if not posts:
                    # Try alternative selectors
                    posts = self.browser.find_elements(By.CSS_SELECTOR, ".ember-view .update-components-actor")

                log.info(f"Found {len(posts)} posts in current view")

                for post in posts:
                    try:
                        # Try to get a unique identifier
                        try:
                            post_id = post.get_attribute("data-urn") or post.get_attribute("id")
                        except:
                            # If we can't get an ID, use the full post text as an identifier
                            post_id = post.text[:100]

                        if post_id in posts_processed:
                            continue

                        posts_processed.add(post_id)

                        # Try to expand the post content by clicking "see more" button
                        try:
                            see_more_button = post.find_element(By.CSS_SELECTOR,
                                ".feed-shared-inline-show-more-text__see-more-less-toggle.see-more.t-14.t-black--light.t-normal.hoverable-link-text.feed-shared-inline-show-more-text__dynamic-more-text.feed-shared-inline-show-more-text__dynamic-bidi-text")
                            if see_more_button and see_more_button.is_displayed():
                                self.browser.execute_script("arguments[0].click();", see_more_button)
                                time.sleep(0.5)  # Wait for content to expand
                                log.info("Expanded post content by clicking 'see more'")
                        except Exception as e:
                            # If "see more" button doesn't exist or can't be clicked, continue normally
                            pass

                        # Get post content - try multiple possible selectors
                        post_text = ""
                        for selector in [
                            ".feed-shared-update-v2__description-wrapper",
                            ".feed-shared-text",
                            ".update-components-text",
                            ".update-components-actor--feed-update-text"
                        ]:
                            try:
                                elements = post.find_elements(By.CSS_SELECTOR, selector)
                                if elements:
                                    post_text = elements[0].text
                                    break
                            except:
                                continue

                        if not post_text:
                            continue

                        # Check for job-related keywords
                        job_keywords = ["hiring", "job", "position", "opportunity", "remote", "full stack", "developer",
                                      "opening", "looking for", "join our team", "apply", "application", "react", "node"]
                        matches = sum(1 for keyword in job_keywords if keyword.lower() in post_text.lower())

                        if matches >= 2:  # If at least 2 job-related keywords are found
                            try:
                                # Extract emails from post content
                                emails_found = self.extract_emails_from_text(post_text)
                                if emails_found:
                                    self.collected_emails.extend(emails_found)
                                    log.info(f"Found {len(emails_found)} email(s) in post: {', '.join(emails_found)}")
                                
                                # Try various selectors for company name
                                company_name = "Unknown Company"
                                for selector in [
                                    ".update-components-actor__name",
                                    ".feed-shared-actor__title",
                                    ".update-components-actor__meta-link"
                                ]:
                                    try:
                                        elements = post.find_elements(By.CSS_SELECTOR, selector)
                                        if elements:
                                            company_name = elements[0].text
                                            break
                                    except:
                                        continue

                                # Try to get the post URL
                                post_link = "URL not found"
                                try:
                                    link_element = post.find_element(By.CSS_SELECTOR, "a.app-aware-link")
                                    post_link = link_element.get_attribute("href")
                                except:
                                    pass

                                log.info(f"\nFound potential job post:")
                                log.info(f"Company: {company_name}")
                                log.info(f"Post URL: {post_link}")
                                log.info(f"Content preview: {post_text[:200]}...")
                                if emails_found:
                                    log.info(f"Emails found: {', '.join(emails_found)}")

                                # Save to file
                                self.write_to_file(matches, post_id, f"Feed Post | {company_name}", True)

                            except Exception as e:
                                log.error(f"Error processing post details: {str(e)}")

                    except Exception as e:
                        log.error(f"Error processing post: {str(e)}")
                        continue

                # Scroll down
                self.browser.execute_script("window.scrollTo(0, window.pageYOffset + 1000)")
                time.sleep(2)  # Wait for new content to load
                scroll_count += 1
                log.info(f"Scrolled {scroll_count} times, found {len(posts_processed)} posts so far")

            except Exception as e:
                log.error(f"Error during scroll: {str(e)}")
                scroll_count += 1
                continue
        
        # Save collected emails to file at the end
        self.save_emails_to_file()
        self.show_email_statistics()
        log.info(f"Finished collecting posts. Total unique emails found: {len(set(self.collected_emails))}")
    # self.finish_apply() --> this does seem to cause more harm than good, since it closes the browser which we usually don't want, other conditions will stop the loop and just break out

    def applications_loop(self, position, location):

        count_application = 0
        count_job = 0
        jobs_per_page = 0
        start_time = time.time()

        self.browser, _ = self.next_jobs_page(position, location, jobs_per_page)
        log.info("Looking for jobs.. Please wait..")

        no_jobs_found = 0

        while time.time() - start_time < self.MAX_SEARCH_TIME:
            # Keep track of how many time 0 jobs are found to skip to the next role.
            if no_jobs_found > 1:
                # Start application process over.
                log.info("No more jobs, going to next role.")
                self.start_apply()
            try:
                log.info(
                    f"{(self.MAX_SEARCH_TIME - (time.time() - start_time)) // 60} minutes left in this search"
                )

                # sleep to make sure everything loads, add random to make us look human.
                # randoTime = random.uniform(3.5, 4.9)
                # log.debug(f"Sleeping for {round(randoTime, 1)}")
                # time.sleep(randoTime)
                self.load_page(sleep=0.25)

                # LinkedIn displays the search results in a scrollable <div> on the left side, we have to scroll to its bottom
                try:
                    scrollresults = self.browser.find_element(By.CLASS_NAME, "jobs-search-results-list")
                except NoSuchElementException:
                    log.info("An error occured while searching for jobs, going to next role.")
                    self.start_apply()

                # Selenium only detects visible elements; if we scroll to the bottom too fast, only 8-9 results will be loaded into IDs list
                for i in range(300, 3000, 100):
                    self.browser.execute_script(
                        "arguments[0].scrollTo(0, {})".format(i), scrollresults
                    )

                time.sleep(0.25)

                # get job links
                links = self.browser.find_elements("xpath", "//div[@data-job-id]")

                if len(links) == 0:
                    log.info("No more jobs, going to next role.")
                    self.start_apply()

                # get job ID of each job link
                IDs = []
                blacklistCompaniesLower = [x.lower() for x in self.blacklistCompanies]
                blackListTitlesLower = [x.lower() for x in self.blackListTitles]
                for link in links:
                    jobID = link.get_attribute("data-job-id").split(":")[-1]
                    if jobID in self.appliedJobIDs:
                        continue
                    name = link.find_element(By.CLASS_NAME, "job-card-list__title").text
                    employer = link.find_element(By.CLASS_NAME, "job-card-container__primary-description").text
                    if (name.lower() in blackListTitlesLower or employer.lower() in blacklistCompaniesLower):
                        #log.info(f"Ignoring job posting from blacklist {name} @ {employer}.")
                        continue

                    # You could add conditions here to filter out jobs that don't match your criteria
                    # if "intern" not in name.lower():
                    #     #log.info(f"Ignoring non-internship job posting {name} @ {employer}.")
                    #     continue

                    IDs.append(int(jobID))

                # remove duplicates
                IDs = set(IDs)

                # remove already applied jobs
                jobIDs = [x for x in IDs if x not in self.appliedJobIDs]
                after = len(jobIDs)
                print("JOBS FOUND: " + str(after))
                if len(jobIDs) == 0:
                    no_jobs_found += 1

                # it assumed that 25 jobs are listed in the results window
                if len(jobIDs) == 0 and len(IDs) > 23:
                    jobs_per_page = jobs_per_page + 25
                    count_job = 0
                    self.avoid_lock()
                    self.browser, jobs_per_page = self.next_jobs_page(
                        position, location, jobs_per_page
                    )
                # loop over IDs to apply
                zero_matches = 0
                for i, jobID in enumerate(jobIDs):
                    if zero_matches > 10:
                        log.info("Looks like jobs are no longer relevant, going to next role.")
                        return self.start_apply()
                    count_job += 1
                    self.get_job_page(jobID)

                    # Check for keywords
                    keywords = self.keywords

                    matches = 0
                    matched_keywords = []
                    time.sleep(0.1)
                    show_more = self.browser.find_element(By.CLASS_NAME, "jobs-description__footer-button")
                    show_more.click()

                    company_name = self.browser.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__company-name").text

                    job_subtitle = self.browser.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__primary-description-container").text
                    job_location = job_subtitle.split(" · ")[0].strip()

                    job_title = self.browser.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title").text
                    job_description = self.browser.find_element(By.CLASS_NAME, "jobs-description-content__text").text
                    #company_logo_url = self.browser.find_element(By.XPATH, "//img[contains(@alt, 'company logo')]").get_attribute("src")
                    #company_logo_url = self.browser.find_element(By.XPATH, f"//img[contains(@alt, '{company_name} Company logo')]").get_attribute("src")
                    # find by XPATH with height of 40
                    company_logo_url = self.browser.find_element(By.XPATH, f"//img[contains(@height, '40')]").get_attribute("src")
                    posting_url = "https://www.linkedin.com/jobs/view/" + str(jobID)

                    # try to get salary
                    try:
                        salary = self.browser.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-insight").text
                        if salary.startswith("$"):
                            salary = salary.split(" ")[0]
                        else:
                            salary = "Unknown"
                    except:
                        salary = "Unknown"

                    for keyword in keywords:
                        if keyword.lower() in job_description.lower():
                            matches += 1
                            matched_keywords.append(keyword)
                    if matches >= 3:
                        log.info("Job posting matches keywords.")
                        string_easy = "* " + str(matches) + " matches"
                        result = True
                        matched_formatted = ",".join(matched_keywords)
                        log.info(f"Found matching job: {job_title} @ {company_name}")
                        log.info(f"Location: {job_location}")
                        log.info(f"Salary: {salary}")
                        log.info(f"URL: {posting_url}")
                        log.info(f"Matched keywords: {matched_formatted}")
                    else:
                        log.info("Job posting has <3 keywords.")
                        string_easy = "* " + str(matches) + "  matches"
                        result = False
                        if matches == 0:
                            zero_matches += 1
                    position_number = str(count_job + jobs_per_page)
                    log.info(f"\nPosition {position_number}:\n {self.browser.title} \n {string_easy} \n")

                    self.write_to_file(matches, jobID, self.browser.title, result)
                    self.appliedJobIDs = self.get_appliedIDs(self.filename)  # Reinitialize applied JobIDS

                    # go to new page if all jobs are done
                    if count_job == len(jobIDs):
                        jobs_per_page = jobs_per_page + 25
                        count_job = 0
                        log.info("Finished page, going to next page.")
                        self.avoid_lock()
                        self.browser, jobs_per_page = self.next_jobs_page(
                            position, location, jobs_per_page
                        )
            except Exception as e:
                print(e)

    def write_to_file(self, matches, jobID, browserTitle, result):
        def re_extract(text, pattern):
            target = re.search(pattern, text)
            if target:
                target = target.group(1)
            return target

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # attempted = False if button == False else True
        job = re_extract(browserTitle.split(" | ")[0], r"\(?\d?\)?\s?(\w.*)")
        company = re_extract(browserTitle.split(" | ")[1], r"(\w.*)")

        toWrite = [timestamp, jobID, job, company, str(matches), result]
        with open(self.filename, "a") as f:
            writer = csv.writer(f)
            writer.writerow(toWrite)

    def get_job_page(self, jobID):
        jobURL = "https://www.linkedin.com/jobs/view/" + str(jobID)
        self.browser.get(jobURL)
        self.job_page = self.load_page(sleep=0.25)
        return self.job_page

    def load_page(self, sleep=0.25):
        scroll_page = 0
        while scroll_page < 4000:
            self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 200
            time.sleep(0.1)

        if sleep != 1:
            self.browser.execute_script("window.scrollTo(0,0);")
            time.sleep(sleep * 3)

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page

    def avoid_lock(self):
        # x, _ = pyautogui.position()
        # pyautogui.moveTo(x + 200, pyautogui.position().y, duration=0.1)
        # pyautogui.moveTo(x, pyautogui.position().y, duration=0.1)
        # pyautogui.keyDown('ctrl')
        # pyautogui.press('esc')
        # pyautogui.keyUp('ctrl')
        # time.sleep(0.1)
        # pyautogui.press('esc')
        pass

    def next_jobs_page(self, position, location, jobs_per_page):
        # Easy Apply: ?f_LF=f_AL
        # Some other things you can do:
        # - Internships: &f_E=1
        # - Entry Level: &f_E=2

        self.browser.get(
            "https://www.linkedin.com/jobs/search/"
            + f"?keywords={position}"
            + f"&location={location}"
            + f"&f_E=2"
            + f"&f_TPR=r2592000" # r2592000 for 30 days | #r604800 for 7 days
            + f"&start={str(jobs_per_page)}"
        )
        # self.avoid_lock()
        self.load_page(sleep=0.25)
        return (self.browser, jobs_per_page)

    def finish_apply(self):
        self.browser.close()

    def save_cookies(self):
        """Save current browser cookies to file"""
        try:
            cookies = self.browser.get_cookies()
            with open("cookies.pkl", "wb") as f:
                pickle.dump(cookies, f)
            log.info("Cookies saved successfully!")
        except Exception as e:
            log.error(f"Error saving cookies: {str(e)}")

    def load_cookies(self):
        """Load cookies from file and add them to browser"""
        try:
            if not os.path.exists("cookies.pkl"):
                return False

            with open("cookies.pkl", "rb") as f:
                cookies = pickle.load(f)

            # First navigate to LinkedIn domain so we can add cookies
            self.browser.get("https://www.linkedin.com")
            time.sleep(1)

            # Add each cookie
            for cookie in cookies:
                try:
                    self.browser.add_cookie(cookie)
                except Exception as e:
                    # Some cookies might not be valid anymore, just skip them
                    continue

            log.info("Cookies loaded successfully!")
            return True

        except Exception as e:
            log.error(f"Error loading cookies: {str(e)}")
            return False

    def clear_cookies(self):
        """Clear saved cookies file"""
        try:
            if os.path.exists("cookies.pkl"):
                os.remove("cookies.pkl")
                log.info("Cookies cleared successfully!")
            else:
                log.info("No cookies file found to clear.")
        except Exception as e:
            log.error(f"Error clearing cookies: {str(e)}")

    def extract_emails_from_text(self, text):
        """Extract email addresses from text using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails
    
    def save_emails_to_file(self):
        """Save all collected emails to a file"""
        if self.collected_emails:
            try:
                with open("collected_emails.txt", "w") as f:
                    for email in set(self.collected_emails):  # Remove duplicates
                        f.write(email + "\n")
                log.info(f"Saved {len(set(self.collected_emails))} unique emails to collected_emails.txt")
            except Exception as e:
                log.error(f"Error saving emails: {str(e)}")
        else:
            log.info("No emails collected to save")

    def show_email_statistics(self):
        """Show statistics about collected emails"""
        if self.collected_emails:
            unique_emails = set(self.collected_emails)
            log.info(f"\n=== EMAIL COLLECTION STATISTICS ===")
            log.info(f"Total emails found: {len(self.collected_emails)}")
            log.info(f"Unique emails: {len(unique_emails)}")
            
            # Show domains statistics
            domains = {}
            for email in unique_emails:
                domain = email.split('@')[1].lower()
                domains[domain] = domains.get(domain, 0) + 1
            
            log.info(f"Domains found: {len(domains)}")
            for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
                log.info(f"  {domain}: {count} email(s)")
            
            log.info(f"===================================\n")
        else:
            log.info("No emails collected during this session")

if __name__ == "__main__":
    with open("config.yaml", "r") as file:
        try:
            config = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            raise exc

    assert len(config["positions"]) > 0
    assert len(config["locations"]) > 0
    assert config["username"] is not None
    assert config["password"] is not None

    output_filename = "output.csv"
    blacklistCompanies = config.get("blacklistCompanies", [])
    blackListTitles = config.get("blackListTitles", [])
    keywords = config.get("keywords", [])

    locations = [l for l in config["locations"] if l != None]
    positions = [p for p in config["positions"] if p != None]

    log.info(f"Applying to {', '.join(positions)} positions in {', '.join(locations)} locations.")
    log.info(f"[CONFIG] Blacklisted companies: {', '.join(blacklistCompanies)}")
    log.info(f"[CONFIG] Blacklisted titles: {', '.join(blackListTitles)}")

    bot = EasyApplyBot(
        config["username"],
        config["password"],
        filename=output_filename,
        blacklistCompanies=blacklistCompanies,
        blackListTitles=blackListTitles,
        positions=positions,
        locations=locations,
        keywords=keywords,
    )
    bot.start_apply()
