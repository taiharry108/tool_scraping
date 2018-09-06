import pandas as pd

def main():
	filename = 'temp/sydtools_test_debug_list.json'
	df = pd.read_json(filename)
	df.to_csv('debug_list.csv')
if __name__ == '__main__':
	main()