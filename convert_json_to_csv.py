import pandas as pd
import sys

def main():
	prefix = "result/" + sys.argv[1]
	print("prefix={}".format(prefix))
	filename = prefix + 'result.json'
	with open(filename) as f:
		df = pd.read_json(f)
	df = df.T
	print(df)
	df.to_csv(filename.replace('.json', '.csv'))
if __name__ == '__main__':
	main()