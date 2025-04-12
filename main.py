from curl_cffi import requests
import os
from dotenv import load_dotenv
from html.parser import HTMLParser

class customParser(HTMLParser):
    data = ""

    def handle_data(self, data):
        self.data = self.data + data

    def new_status(self):
        self.data = ""

load_dotenv(dotenv_path="./login.env")

TRUTH_USERNAME = os.getenv("TRUTH_USERNAME")
TRUTH_PASSWORD = os.getenv("TRUTH_PASSWORD")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 "
    "Safari/537.36"
)

body = {
    "client_id": "9X1Fdd-pxNsAgEDNi_SfhJWi8T-vLuV2WVzKIbkTCw4",
    "client_secret": "ozF8jzI4968oTKFkEnsBC-UbLPCdrSv0MkXGQu2o_-M",
    "grant_type": "password",
    "password": TRUTH_PASSWORD,
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "scope": "read",
    "username": TRUTH_USERNAME
}

token = requests.post(
    url="https://truthsocial.com/oauth/token",
    headers = {
    "User-Agent": USER_AGENT
    },
    json=body,
    impersonate="chrome123"
)

token = token.json()
try:
    if token["error"]:
        raise Exception(token["error"])
except KeyError:
    token = token['access_token']

statuses = requests.get(
    "https://truthsocial.com/api/v1/accounts/107780257626128497/statuses?exclude_replies=true",
    impersonate="chrome123",
    headers={
        "Authorization": "Bearer " + token,
        "User-Agent": USER_AGENT
    }
)

parser = customParser()
statuses = statuses.json()
for status in statuses:
    date = status["created_at"]
    content = status["content"]

    parser.new_status()
    parser.feed(content)

    if parser.data == "" or "RT @realDonaldTrump" in parser.data:
        pass
    else:
        print(date)
        print(parser.data)
        print('\n')
