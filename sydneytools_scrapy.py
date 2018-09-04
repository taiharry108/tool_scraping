from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import re, math, json, time, os

FIELD_DICT = {
	"Name": "#product-shop > div.row.no-gutter > div.product-info.col-sm-6.col-md-12 > h1",
	"Item ID": "#product-shop > div.row.no-gutter > div.product-info.col-sm-6.col-md-12 > div > p.sku > span:nth-child(2)",
	"Model": "#product-shop > div.row.no-gutter > div.product-info.col-sm-6.col-md-12 > div > p.model > span",
}

HOME_URL = 'https://sydneytools.com.au/by-brand/shopby/milwaukee'

TIMEOUT = 20
JOIN = os.path.join
PREFIX = "sydtools_"
PROD_P_LINK_F = JOIN('temp', PREFIX + "product_page_links.json")
RESULT_F = JOIN('result', PREFIX + "result.json")
FAILED_LINK_F = JOIN('temp', PREFIX + "failed_link.txt")
DEBUG_F = JOIN('temp', "debug_list.json")

def get_chrome_driver():
	chrome_options = Options()  
	chrome_options.add_argument("--headless")
	chrome_options.add_argument("--window-size=1920x1080")
	driver = webdriver.Chrome(executable_path="chromedriver.exe", chrome_options=chrome_options)
	driver.maximize_window()
	return driver

def go_first_page(driver):
	driver.get(HOME_URL)
	try:
		myElem = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, 'content-wrapper')))
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


def have_prod_page_links():
	try:
		with open(PROD_P_LINK_F) as prod_links_f:
			return json.load(prod_links_f)
	except:
		return False

def have_result_f():
	try:
		with open(RESULT_F) as result_f:
			return json.load(result_f)
	except:
		return False

def get_prod_page_links_in_type(driver, type_page, debug_list):
	print('going to page ' + type_page)
	driver.get(type_page)	
	try:
		myElem = WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable((By.CLASS_NAME, 'product-border')))
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

def get_prod_page_links(driver, type_pages):
	product_page_links = []
	debug_list = []
	for type_page in type_pages:
		product_pages = get_prod_page_links_in_type(driver, type_page, debug_list)
		product_page_links.extend(product_pages)
		next_page = check_has_next_page(driver)
		while next_page:
			product_pages = get_prod_page_links_in_type(driver, next_page, debug_list)
			product_page_links.extend(product_pages)
			next_page = check_has_next_page(driver)
	with open(DEBUG_F, 'w') as f:
		json.dump(debug_list, f)
	return product_page_links

def get_product_pages(driver):
	border_divs = driver.find_elements_by_class_name('product-border')
	return [ele.find_element_by_tag_name('a').get_attribute('href') for ele in border_divs]

def get_product_details(driver):
	product_details = {key: driver.find_element_by_css_selector(sel).text for key, sel in FIELD_DICT.items()}
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
	result_dict = have_result_f()
	if not result_dict:
		print("no prev result dict, going to create empty dict")
		result_dict = {}
	driver = get_chrome_driver()

	if not go_first_page(driver):
		return

	type_pages = get_type_pages(driver)

	product_page_links = have_prod_page_links()
	if not product_page_links:
		print("cannot find product page link file, going to get it")
		product_page_links = get_prod_page_links(driver, type_pages)
		with open(PROD_P_LINK_F, 'w') as prod_links_f:
			json.dump(product_page_links, prod_links_f)

	for page_link in product_page_links:
		if page_link in result_dict.keys():
			continue
		print("going to sleep for 1s")
		time.sleep(1)
		print("trying to go to {}".format(page_link))
		driver.get(page_link)
		try:
			myElem = WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#product-tabs > li:nth-child(1)")))
			print("{} is ready!".format(page_link))
			product_details = get_product_details(driver)
			result_dict[page_link] = product_details
		except TimeoutException:
			print("Loading took too much time!")
			with open(FAILED_LINK_F, 'a') as failed_link_f:
				failed_link_f.write("{}\n".format(page_link))

		if len(result_dict) % 10 == 0:
			with open(RESULT_F, 'w') as result_f:
				json.dump(result_dict, result_f)

	with open(RESULT_F, 'w') as result_f:
		json.dump(result_dict, result_f)

if __name__ == '__main__':
	main()