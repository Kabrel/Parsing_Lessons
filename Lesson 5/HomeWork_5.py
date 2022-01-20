from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pymongo

client = pymongo.MongoClient('localhost', 27017)
db = client.mails_db
mails_collection = db.mail_collection

user_login = 'study.ai_172'
user_pass = 'NextPassword172#'
mail_width = 48  # Pixel height
mail_page_count = 16
scroll_val = mail_width * mail_page_count

driver = webdriver.Chrome()
driver.implicitly_wait(5)
driver.get('https://mail.ru/')

login = driver.find_element(By.XPATH, "//input[contains(@class, 'email-input')]")
login.send_keys(f"{user_login}\n")

password = driver.find_element(By.XPATH, "//input[contains(@class, 'password-input')]")
password.send_keys(f"{user_pass}\n")

mails = {}
no_mails_exist = False

while not no_mails_exist:
    mails_loaded = False
    mails_container = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
        [By.XPATH, "//a[contains(@href, '/inbox/') and contains(@class, 'llc')]"]))
    mails_size_before_add = len(mails)
    for mail in mails_container:
        mail_url = mail.get_attribute('href')
        mails[mail_url] = {}
    if len(mails) == mails_size_before_add:
        no_mails_exist = True
    mails_container[len(mails_container)//2].send_keys(Keys.PAGE_DOWN)
    time.sleep(0.5)

for url in mails.keys():
    mail_db_elem = {}
    driver.get(url)
    mail_body = WebDriverWait(driver, 10).until( EC.presence_of_element_located((By.XPATH, "//div[contains(@class, "
                                                                                           "'letter-body')]")))
    mail_db_elem['_id'] = url
    mail_db_elem['data'] = mail_body.text
    mails_collection.insert_one(mail_db_elem)
    driver.back()
driver.close()
