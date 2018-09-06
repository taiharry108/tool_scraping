from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import re, math, json, time, os

CONFIG_F = "config/gettoolsdirect_config.json"
JOIN = os.path.join

def load_config():
	with open(CONFIG_F) as config_f:
		return json.load(config_f)

def get_chrome_driver():
	chrome_options = Options()  
	# chrome_options.add_argument("--headless")
	chrome_options.add_argument("--window-size=1920x1080")
	# driver = webdriver.Chrome(executable_path="chromedriver.exe")
	driver = webdriver.Chrome(executable_path="chromedriver.exe", chrome_options=chrome_options)
	driver.maximize_window()
	return driver

def go_first_page(driver, home_url, timeout):
	driver.get(home_url + '#limit=200')
	try:
		WebDriverWait(driver, timeout)\
			.until(EC.text_to_be_present_in_element(
				(By.CSS_SELECTOR, '#categoryContainer_products_header > div.categoryContainer_toolbar.toolbar > div.paging_qty'),
				'200'
			))
		print("Page is ready!")
		return True
	except TimeoutException:
		print("Loading took too much time!")	
		return False

def have_prod_page_links(prod_p_link_filename):
	try:
		with open(prod_p_link_filename) as prod_links_f:
			return json.load(prod_links_f)
	except:
		return False

def have_result_f(result_filename):
	try:
		with open(result_filename) as result_f:
			return json.load(result_f)
	except:
		return False

def check_has_next_page(driver):
	try:
		div = driver.find_element_by_id('paging_paging')
		a = div.find_elements_by_class_name('button-paging')[-1]
		if a.get_attribute('title') == 'Next':
			return a.get_attribute('href')
	except:
		return False

def get_prod_page_links(driver, timeout, is_test):
	product_page_links = []
	while True:
		product_pages = get_product_pages(driver)
		print(len(product_pages))
		product_page_links.extend(product_pages)
		next_page = check_has_next_page(driver)
		if next_page:
			print("trying to get {}".format(next_page))
			driver.get(next_page)
			try:
				WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#categoryContainer_subcategories_body > div:nth-child(1)')))
				print("Next page {} is ready!".format(next_page))
			except TimeoutException:
				print("Loading took too much time!")
			if is_test:
				break
		else:
			break

	return product_page_links

def get_product_pages(driver):
	ul = driver.find_element_by_id('categoryContainer_products_grid')
	a_tags = ul.find_elements_by_css_selector('a.product-hover_top')
	return [a.get_attribute('href') for a in a_tags]

def get_product_details(driver):
	product_details = {}
	try:
		product_details['Name'] = driver.find_element_by_id('listing-header').text
	except:
		product_details['Name'] = ''
	try:
		product_details['Details'] = driver.find_element_by_id('tab1').text
	except:
		product_details['Details'] = ''	
	try:
		product_details['Price'] = driver.find_element_by_css_selector('#listing-top_addtocart_price > span').text
	except:
		product_details['Price'] = ''
	try:
		product_details['Brand'] = driver.find_element_by_css_selector("#listing-top_details-table > tbody > tr:nth-child(1) > td > span").text
	except:
		product_details['Brand'] = ''
	try:
		product_details['Model'] = driver.find_element_by_css_selector("#listing-top_details-table > tbody > tr:nth-child(2) > td > span").text
	except:
		product_details['Model'] = ''	
	return product_details

def main():
	config_dict = load_config()

	home_url = config_dict["HOME_URL"]
	timeout = config_dict["TIMEOUT"]
	prefix = config_dict["PREFIX"]
	is_test = config_dict["TEST"]

	if is_test:
		prefix += "test_"

	prod_p_link_filename = JOIN('temp', prefix + "product_page_links.json")
	result_filename = JOIN('result', prefix + "result.json")
	failed_link_filename = JOIN('temp', prefix + "failed_link.txt")

	result_dict = have_result_f(result_filename)
	if not result_dict:
		print("no prev result dict, going to create empty dict")
		result_dict = {}
	driver = get_chrome_driver()

	if not go_first_page(driver, home_url, timeout):
		return

	product_page_links = have_prod_page_links(prod_p_link_filename)
	if not product_page_links:
		print("cannot find product page link file, going to get it")
		product_page_links = get_prod_page_links(driver, timeout, is_test)
		with open(prod_p_link_filename, 'w') as prod_links_f:
			json.dump(product_page_links, prod_links_f)

	if is_test:
		product_page_links = product_page_links[:15]

	for page_link in product_page_links:
		if page_link in result_dict.keys() and result_dict[page_link]["Name"] != "":
			continue
		print("going to sleep for 1s")
		time.sleep(1)
		while True:
			print("trying to go to {}".format(page_link))
			driver.get(page_link)
			try:
				myElem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.tabs")))
				print("{} is ready!".format(page_link))
				product_details = get_product_details(driver)
				result_dict[page_link] = product_details
				if product_details['Name'] == "" or product_details["Details"] == "":
					continue
				else:
					break
			except TimeoutException:
				print("Loading took too much time!")
				with open(failed_link_filename, 'a') as failed_link_f:
					failed_link_f.write("{}\n".format(page_link))

		if len(result_dict) % 10 == 0:
			with open(result_filename, 'w') as result_f:
				json.dump(result_dict, result_f)

	with open(result_filename, 'w') as result_f:
		json.dump(result_dict, result_f)

if __name__ == '__main__':
	main()