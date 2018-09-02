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
	"Name":"#product_addtocart_form > div.product-primary-column.product-shop.grid12-5 > div.product-name > h1",
	"Short Description":"#product_addtocart_form > div.product-primary-column.product-shop.grid12-5 > div.short-description > div",
	"Code":"#product_addtocart_form > div.product-primary-column.product-shop.grid12-5 > div.short-description > div > span",
	"Price":"div.price-box",
}

HOME_URL = 'https://www.toolmart.com.au/brands/sidchrome.html'

TIMEOUT = 20

JOIN = os.path.join
PREFIX = "toolmart_"
PROD_P_LINK_F = JOIN('temp', PREFIX + "product_page_links.json")
RESULT_F = JOIN('result', PREFIX + "result.json")
FAILED_LINK_F = JOIN('temp', PREFIX + "failed_link.txt")

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
		myElem = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, 'root-wrapper')))
		print("Page is ready!")
		return True
	except TimeoutException:
		print("Loading took too much time!")	
		return False

def get_num_of_pages(driver):
	css_selector = "#amshopby-page-container > div.category-products > div.toolbar-bottom > div > div > p.amount"
	ele = driver.find_element_by_css_selector(css_selector)
	items_per_page = 16
	num_of_items = re.search(" of (\d+) total", ele.text).group(1)
	num_of_items = int(num_of_items)
	return math.ceil(num_of_items / items_per_page)

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

def get_prod_page_links(driver, num_of_pages):
	product_page_links = []
	product_page_links.extend(get_product_pages(driver))
	for i in range(1, num_of_pages):
		page = i + 1
		url = HOME_URL + "?p={}".format(page)		
		driver.get(url)
		try:
			myElem = WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable((By.CLASS_NAME, 'product-image-wrapper')))
			print("Page {} is ready!".format(page))
			links = get_product_pages(driver)
			product_page_links.extend(links)
		except TimeoutException:
			print("Loading page {} took too much time!".format(page))
	return product_page_links

def get_product_pages(driver):
	img_wrappers = driver.find_elements_by_class_name('product-image-wrapper')
	return [ele.find_element_by_tag_name('a').get_attribute('href') for ele in img_wrappers]

def get_product_details(driver):
	product_details = {}
	for key, sel in FIELD_DICT.items():
		try:
			product_details[key] = driver.find_element_by_css_selector(sel).text
		except:
			product_details[key] = ""
	try:
		sel = "#product-tabs > div > div:nth-child(2) > div"
		product_details["Description"] = driver.find_element_by_css_selector(sel).text
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

	num_of_pages = get_num_of_pages(driver)

	product_page_links = have_prod_page_links()
	if not product_page_links:
		print("cannot find product page link file, going to get it")
		product_page_links = get_prod_page_links(driver, num_of_pages)
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
			myElem = WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#product-tabs > ul")))
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