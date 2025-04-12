from curl_cffi import requests
import os
from dotenv import load_dotenv
from html.parser import HTMLParser
import smtplib
from email.message import EmailMessage
from datetime import datetime

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
output = []
days = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
        7: "Sunday"
    }
months = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December"
    }
for status in statuses:
    date = status["created_at"]
    date = date[:-1]

    formatted_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')

    day_of_week = days[formatted_date.isoweekday()]
    word_month = months[formatted_date.month]
    final_date = f"{day_of_week}, {word_month} {formatted_date.day}, {formatted_date.year}"
    timestamp = formatted_date.time()
    
    content = status["content"]

    parser.new_status()
    parser.feed(content)

    if parser.data == "" or "RT @realDonaldTrump" in parser.data:
        pass
    else:
        output.append(f"{final_date}\n{timestamp}\n\n{parser.data}\n\n\n")

output = " ".join(output)

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

msg = EmailMessage()
msg.set_content(output)
msg['Subject'] = "New Donald Trump Status on Truth Social"
msg['From'] = EMAIL_FROM
msg["To"] = EMAIL_TO

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
    smtp_server.login(EMAIL_FROM, EMAIL_PASSWORD)
    smtp_server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
