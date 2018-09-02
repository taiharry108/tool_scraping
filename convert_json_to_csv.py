import pandas as pd

def main():
	prefix = "result/gettoolsdirect_sidchrome_"
	filename = prefix + 'result.json'
	df = pd.read_json(filename).T
	print(df)
	df.to_csv(filename.replace('.json', '.csv'))
if __name__ == '__main__':
	main()