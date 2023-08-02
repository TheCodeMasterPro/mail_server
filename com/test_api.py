import requests

url = 'https://www.virustotal.com/vtapi/v2/file/scan'
params = {'apikey': '3ba93fa402a55711d973c4a5d33dc72f60e34380edc534bd50dd72042055698a'}
files = {'file': ('malicious.docx', open('malicious files/malicious.docx', 'rb'))}
response = requests.post(url, files=files, params=params)
scan_id = response.json()["scan_id"]
print(scan_id)
params = {'apikey': '3ba93fa402a55711d973c4a5d33dc72f60e34380edc534bd50dd72042055698a', 'resource':scan_id}
url = 'https://www.virustotal.com/vtapi/v2/file/report'
response = requests.get(url, params=params)
print(response.json())