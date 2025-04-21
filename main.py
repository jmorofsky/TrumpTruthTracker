from curl_cffi import requests
import os
from dotenv import load_dotenv
from html.parser import HTMLParser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import time


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
    "username": TRUTH_USERNAME,
}

print(f"Getting token with username {TRUTH_USERNAME}")

token = requests.post(
    url="https://truthsocial.com/oauth/token",
    headers={"User-Agent": USER_AGENT},
    json=body,
    impersonate="chrome123",
)

if token.content:
    print("Got token response!")
    token = token.json()
else:
    raise Exception("No token response received.")


try:
    if token["error"]:
        raise Exception(f"Error during token acquisition: {token["error"]}")
except KeyError:
    token = token["access_token"]

print("Fetching statuses...")

statuses = requests.get(
    "https://truthsocial.com/api/v1/accounts/107780257626128497/statuses?exclude_replies=true",
    impersonate="chrome123",
    headers={"Authorization": "Bearer " + token, "User-Agent": USER_AGENT},
)

if statuses.content:
    print("Got statuses response!")
    statuses = statuses.json()
else:
    raise Exception("No statuses response received.")

parser = customParser()
output = []
days = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
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
    12: "December",
}

local_now = time.time()
offset = datetime.fromtimestamp(local_now) - datetime.utcfromtimestamp(local_now)
first = True
new_statuses = []
for status in statuses:
    date = status["created_at"]
    date = date[:-1]

    formatted_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f")
    formatted_date = formatted_date + offset

    day_of_week = days[formatted_date.isoweekday()]
    word_month = months[formatted_date.month]
    final_date = (
        f"{day_of_week}, {word_month} {formatted_date.day}, {formatted_date.year}"
    )
    if formatted_date.minute < 10:
        timestamp = f"{formatted_date.hour}:0{formatted_date.minute}"
    else:
        timestamp = f"{formatted_date.hour}:{formatted_date.minute}"

    content = status["content"]

    parser.new_status()
    parser.feed(content)

    now = datetime.now()
    one_hour = timedelta(hours=1)
    one_hour_ago = now - one_hour
    if parser.data == "" or "RT:" in parser.data or "RT @" in parser.data:
        pass
    elif formatted_date > one_hour_ago:
        if first:
            new_statuses.append(
                f"<p style='color: black'><strong>{final_date}<br />{timestamp}</strong></p><p>{parser.data}</p>"
            )
            first = False
        else:
            new_statuses.append(
                f"<hr class='solid'><p style='color: black'><strong>{final_date}<br />{timestamp}</strong></p><p>{parser.data}</p>"
            )
    else:
        output.append(
            f"<hr class='solid'><br /><span style='white-space: pre-line'>{final_date}\n{timestamp}\n\n{parser.data}\n\n</span>"
        )

output = " ".join(output)
new_statuses = " ".join(new_statuses)

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

msg = MIMEMultipart("alternative")
msg["Subject"] = "New Donald Trump Status on Truth Social"
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO

html = f"""\
<html>
  <body>
    <div style=
    "background-color: Cornsilk; padding: 1px; padding-left: 14px; padding-right: 14px; font-size: 125%;">
      {new_statuses}
    </div>

    <br />
    {output}
  </body>
</html>
"""

if len(new_statuses) > 0:
    part1 = MIMEText(output, "plain")
    part2 = MIMEText(html, "html")
    msg.attach(part1)
    msg.attach(part2)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(EMAIL_FROM, EMAIL_PASSWORD)
        smtp_server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
