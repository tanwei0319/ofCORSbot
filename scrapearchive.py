from bs4 import BeautifulSoup
import lxml
import requests
import json



def main():
	url = "http://www.cors.nus.edu.sg/Archive/201617_Sem1/successbid_3B_20162017s1.html"
	result = requests.get(url)

	soup = BeautifulSoup(result.content, 'lxml')
	rows = soup.findAll("tr")
	modules = []
	numRows = len(rows)

	for index in range(2, numRows):
		row = rows[index]
		cols = row.findAll("p")

		if len(cols) == 7:
			infoObj = {}
			infoObj["moduleQuota"] = cols[0].text
			infoObj["numBidders"] = cols[1].text
			infoObj["lowestBid"] = cols[2].text
			infoObj["succBid"] = cols[3].text
			infoObj["highestBid"] = cols[4].text
			infoObj["faculty"] = cols[5].text
			infoObj["studentType"] = cols[6].text
			module["info"].append(infoObj)
		else:
			module = {}
			module["moduleCode"] = cols[0].text
			module["moduleGroup"] = cols[1].text
			module["info"] = []
			infoObj = {}
			infoObj["moduleQuota"] = cols[2].text
			infoObj["numBidders"] = cols[3].text
			infoObj["lowestBid"] = cols[4].text
			infoObj["succBid"] = cols[5].text
			infoObj["highestBid"] = cols[6].text
			infoObj["faculty"] = cols[7].text
			infoObj["studentType"] = cols[8].text
			module["info"].append(infoObj)
		if index == numRows - 1: 
			modules.append(module)
		else:
			nextRow = rows[index + 1]
			numCols = nextRow.findAll("p")
			if len(numCols) == 9:
				modules.append(module)

	# # print(modules)
	data = {}
	data["round3Bsumm"] = modules

	with open('round3Bsumm.json', 'w') as outfile:
		json.dump(data, outfile)

	# thefile = open('test.json', 'w')
	# for item in modules:
	# 	thefile.write("%s\n" % item)



	#print(rows[1])


if __name__ == "__main__":
    main()