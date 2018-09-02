import json
PREFIX = 'gettoolsdirect_sidchrome_'
with open('result/{}result.json'.format(PREFIX)) as f:
	result_dict = json.load(f)
print(len(result_dict.keys()))