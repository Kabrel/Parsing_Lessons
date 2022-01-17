from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

# while True:
#     try:
#         wait = WebDriverWait(driver, 10)
#         cancel_btn = wait.until(EC.visibility_of_element_located((By.XPATH, "//button[contains(@data-test-id, "
#                                                                             "'recovery-addPhone-cancel')]")))
#         cancel_btn.click()
#     except:
#         break


def get_url():
    mail_list = []
    mails = driver.find_elements(By.XPATH, "//a[contains(@class, 'js-letter-list-item')]")
    for mail in mails:
        mail_url = mail.get_attribute('href')
        mail_list.append(mail_url)
    return mail_list


def scroll_page(site):
    site.execute_script("window.scrollTo(0, 768)")


mails_urls = []

while True:
    tries = 0
    mails_urls.extend(get_url())
    scroll_page(driver, tries, scroll_val)
    tries += 1
    #

print()
