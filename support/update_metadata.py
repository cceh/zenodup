import json
import requests

data = {
    "metadata": {
        "title": "My first upload",
        "upload_type": "poster",
        "description": "This is my first upload",
        "creators": [
            {"name": "Doe, John", "affiliation": "Zenodo"}
        ]
    }
}
url = "https://zenodo.org/api/deposit/depositions/1234?access_token=ACCESS_TOKEN"
headers = {"Content-Type": "application/json"}

r = requests.put(url, data=json.dumps(data), headers=headers)
