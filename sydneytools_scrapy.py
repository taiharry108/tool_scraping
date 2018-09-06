from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import re, math, json, time, os

CONFIG_F = "config/sydneytools_config.json"
JOIN = os.path.join

def load_config():
	with open(CONFIG_F) as config_f:
		return json.load(config_f)

def get_chrome_driver():
	chrome_options = Options()  
	chrome_options.add_argument("--headless")
	chrome_options.add_argument("--window-size=1920x1080")
	driver = webdriver.Chrome(executable_path="chromedriver.exe", chrome_options=chrome_options)
	driver.maximize_window()
	return driver

def go_first_page(driver, home_url, timeout):
	driver.get(home_url)
	try:
		myElem = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'content-wrapper')))
		print("Page is ready!")
		return True
	except TimeoutException:
		print("Loading took too much time!")
		return False

def get_type_pages(driver):
	subcat_div = driver.find_element_by_id('subcategory')
	a_tags = subcat_div.find_elements_by_tag_name("a")
	type_pages = [a.get_attribute('href') for a in a_tags]
	return type_pages


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

def get_prod_page_links_in_type(driver, type_page, debug_list, timeout):
	print('going to page ' + type_page)
	driver.get(type_page)	
	try:
		myElem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CLASS_NAME, 'product-border')))
		print("Page {} is ready!".format(type_page))
		product_pages = get_product_pages(driver)
		for product_page in product_pages:
			debug_list.append((type_page, product_page))
		return product_pages
	except TimeoutException:
		print("Loading page {} took too much time!".format(type_page))

def check_has_next_page(driver):
	try:
		ul = driver.find_element_by_class_name('pagination')
		a = ul.find_elements_by_class_name('page-link')[-1]
		if a.get_attribute('title') == 'Next':
			return a.get_attribute('href')
	except:
		return False

def get_prod_page_links(driver, type_pages, timeout, debug_filename):
	product_page_links = []
	debug_list = []
	for type_page in type_pages:
		product_pages = get_prod_page_links_in_type(driver, type_page, debug_list, timeout)
		product_page_links.extend(product_pages)
		next_page = check_has_next_page(driver)
		while next_page:
			product_pages = get_prod_page_links_in_type(driver, next_page, debug_list, timeout)
			product_page_links.extend(product_pages)
			next_page = check_has_next_page(driver)
	with open(debug_filename, 'w') as f:
		json.dump(debug_list, f)
	return product_page_links

def get_product_pages(driver):
	border_divs = driver.find_elements_by_class_name('product-border')
	return [ele.find_element_by_tag_name('a').get_attribute('href') for ele in border_divs]

def get_product_details(driver, field_dict):
	product_details = {key: driver.find_element_by_css_selector(sel).text for key, sel in field_dict.items()}
	try:
		product_id = driver.find_element_by_class_name('pmatch-product-id').get_attribute('value')
		product_details['Price'] = driver.find_element_by_id('product-price-' + product_id).text
	except:
		print("Cannot find product price")
		product_details['Price'] = 0
	try:		
		product_details["Description"] = driver.find_element_by_id('description').text
	except:
		product_details["Description"] = ""
	print(product_details)
	return product_details

def main():

	config_dict = load_config()

	field_dict = config_dict["FIELD_DICT"]
	home_url = config_dict["HOME_URL"]
	timeout = config_dict["TIMEOUT"]
	prefix = config_dict["PREFIX"]
	is_test = config_dict["TEST"]

	if is_test:
		prefix += "test_"

	prod_p_link_filename = JOIN('temp', prefix + "product_page_links.json")
	result_filename = JOIN('result', prefix + "result.json")
	failed_link_filename = JOIN('temp', prefix + "failed_link.txt")
	debug_filename = JOIN('temp', prefix + "debug_list.json")

	result_dict = have_result_f(result_filename)
	if not result_dict:
		print("no prev result dict, going to create empty dict")
		result_dict = {}
	driver = get_chrome_driver()

	if not go_first_page(driver, home_url, timeout):
		return

	type_pages = get_type_pages(driver)

	if is_test:
		type_pages = type_pages[:2]

	product_page_links = have_prod_page_links(prod_p_link_filename)
	if not product_page_links:
		print("cannot find product page link file, going to get it")
		product_page_links = get_prod_page_links(driver, type_pages, timeout, debug_filename)
		with open(prod_p_link_filename, 'w') as prod_links_f:
			json.dump(product_page_links, prod_links_f)

	for page_link in product_page_links:
		if page_link in result_dict.keys():
			continue
		print("going to sleep for 1s")
		time.sleep(1)
		print("trying to go to {}".format(page_link))
		driver.get(page_link)
		try:
			myElem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#product-tabs > li:nth-child(1)")))
			print("{} is ready!".format(page_link))
			product_details = get_product_details(driver, field_dict)
			result_dict[page_link] = product_details
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