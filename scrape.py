from bs4 import BeautifulSoup
import lxml
import requests
import json



def main():
	url = "http://www.nus.edu.sg/cors/Reports/openbid_3B_20162017s2.html"
	result = requests.get(url)

	soup = BeautifulSoup(result.content, 'lxml')
	rows = soup.findAll("tr")
	modules = []
	numRows = len(rows)

	for index in range(2, numRows):
		row = rows[index]
		cols = row.findAll("p")

		if len(cols) == 3:
			infoObj = {}
			infoObj["moduleQuota"] = cols[0].text
			infoObj["faculty"] = cols[1].text
			infoObj["studentType"] = cols[2].text
			module["info"].append(infoObj)
		else:
			module = {}
			module["moduleCode"] = cols[0].text
			module["moduleGroup"] = cols[1].text
			module["info"] = []
			infoObj = {}
			infoObj["moduleQuota"] = cols[2].text
			infoObj["faculty"] = cols[3].text
			infoObj["studentType"] = cols[4].text
			module["info"].append(infoObj)
		if index == numRows - 1: 
			modules.append(module)
		else:
			nextRow = rows[index + 1]
			numCols = nextRow.findAll("p")
			if len(numCols) == 5:
				modules.append(module)

	# print(modules)
	data = {}
	data["round3B"] = modules

	with open('round3B.json', 'w') as outfile:
		json.dump(data, outfile)

	# thefile = open('test.json', 'w')
	# for item in modules:
	# 	thefile.write("%s\n" % item)



	#print(rows[1])


if __name__ == "__main__":
    main()