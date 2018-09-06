import pandas as pd
import sys

def main():
	prefix = "result/" + sys.argv[1]
	filename = prefix + 'result.json'
	df = pd.read_json(filename).T
	print(df)
	df.to_csv(filename.replace('.json', '.csv'))
if __name__ == '__main__':
	main()