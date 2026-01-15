import os
import smtplib
import logging
from curl_cffi import requests
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="app.log",
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 "
    "Safari/537.36"
)


def loadVars():
    load_dotenv()

    env = {
        "TRUTH_USERNAME": os.getenv("TRUTH_USERNAME"),
        "TRUTH_PASSWORD": os.getenv("TRUTH_PASSWORD"),
        "EMAIL_FROM": os.getenv("EMAIL_FROM"),
        "EMAIL_TO": os.getenv("EMAIL_TO"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
    }

    if not all(
        key in env
        for key in [
            "TRUTH_USERNAME",
            "TRUTH_PASSWORD",
            "EMAIL_FROM",
            "EMAIL_TO",
            "EMAIL_PASSWORD",
        ]
    ):
        logger.critical("Missing one or more required environment variables.")
        raise Exception
    else:
        return env


def getToken(username, password):
    body = {
        "client_id": "9X1Fdd-pxNsAgEDNi_SfhJWi8T-vLuV2WVzKIbkTCw4",
        "client_secret": "ozF8jzI4968oTKFkEnsBC-UbLPCdrSv0MkXGQu2o_-M",
        "grant_type": "password",
        "password": password,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "scope": "read",
        "username": username,
    }

    logger.info(f"Getting token with username {username}.")
    token = requests.post(
        url="https://truthsocial.com/oauth/token",
        headers={"User-Agent": USER_AGENT},
        json=body,
        impersonate="chrome123",
    )

    if token.content:
        logger.info("Received token response.")
        token = token.json()
    else:
        logger.critical("Failed to receive token response.")
        raise Exception

    if "error" in token:
        logger.critical("Error occurred during token request.")
        logger.error(token["error"])

        raise Exception
    elif "access_token" in token:
        return token["access_token"]
    else:
        logger.critical(
            "Received unexpected response from token request. Missing access_token field."
        )
        raise Exception


def getStatuses(token):
    logger.info("Getting list of statuses.")

    statuses = requests.get(
        url="https://truthsocial.com/api/v1/accounts/107780257626128497/statuses?exclude_replies=true",
        headers={"Authorization": "Bearer " + token, "User-Agent": USER_AGENT},
        impersonate="chrome123",
    )

    if statuses.content:
        logger.info("Received statuses response.")
        statuses = statuses.json()
    else:
        logger.critical("Failed to received statuses response.")
        raise Exception

    if "error" in statuses:
        logger.critical("Error occurred during statuses request.")
        logger.error(token["error"])

        raise Exception
    else:
        return statuses


def formatStatuses(statusJson):
    formattedStatuses = []

    for status in statusJson:
        statusObj = {}

        timestamp = status["created_at"].replace("Z", "+00:00")
        utc_dt = datetime.fromisoformat(timestamp)
        local_dt = utc_dt.astimezone()
        statusObj["local_timestamp"] = local_dt
        statusObj["naive_timestamp"] = local_dt.replace(tzinfo=None)

        statusObj["url"] = status["url"]
        statusObj["content"] = status["content"]
        statusObj["replies_count"] = status["replies_count"]
        statusObj["reblogs_count"] = status["reblogs_count"]
        statusObj["favorites_count"] = status["favourites_count"]

        statusObj["media"] = []
        if status["media_attachments"]:
            for attachment in status["media_attachments"]:
                if attachment["url"]:
                    statusObj["media"].append(
                        {"url": attachment["url"], "preview": attachment["preview_url"]}
                    )

        formattedStatuses.append(statusObj)

    return formattedStatuses


def sendEmail(statuses, email_to, email_from, email_password):
    if not statuses:
        logger.info("No statuses received. Skipping sending email.")
        return

    now = datetime.now()
    one_hour = timedelta(hours=1)
    one_hour_ago = now - one_hour

    new_statuses = []
    for status in statuses:
        if status["naive_timestamp"] > one_hour_ago:
            new_statuses.append(status)
            statuses.remove(status)

    if not new_statuses:
        logger.info(
            "No new statuses received from within the past hour. Skipping sending email."
        )
        return

    logger.info("Sending email with new statuses.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "New Donald Trump Status on Truth Social"
    msg["From"] = email_from
    msg["To"] = email_to

    def statusCard(status):
        mediaLinks = []
        if status["media"]:
            for item in status["media"]:
                mediaLinks.append(
                    f"<a href={item["url"]}><img src={item["preview"]} style='max-width: 100%; border: 1px solid #ddd; border-radius: 4px; padding: 5px;' /></a>"
                )

        return f"""\
            <div>
                <a href={status["url"]} style="font-size: 12px">View post on Truth Social</a>

                <div style="font-size: 125%">
                    <p>
                        <strong>
                            {status["local_timestamp"].strftime("%A, %B %d, %Y")}<br />
                            {status["local_timestamp"].strftime("%H:%M")}
                        </strong>
                    </p>

                    {status["content"]}
                </div>

                <div style="margin-bottom: 15px;">{" ".join(mediaLinks)}</div>

                <span style="margin-right: 20px; margin-top: 15px;">↩️ {status["replies_count"]}</span>
                <span style="margin-right: 20px;">🔃 {status["reblogs_count"]}</span>
                <span>❤️ {status["favorites_count"]}</span>
            </div>
            """

    new_status_cards = [statusCard(status) for status in new_statuses]
    old_status_cards = [statusCard(status) for status in statuses]

    html = f"""\
    <html>
        <body>
            <div style=
            "background-color: Cornsilk; padding: 1px; padding-left: 14px; padding-right: 14px;">
                {"<hr style='margin: 20px 0 20px;' />".join(new_status_cards)}
            </div>
            <br />
            
            {"<hr style='margin: 20px 0 20px;' />".join(old_status_cards)}
        </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
            smtp_server.login(email_from, email_password)
            smtp_server.sendmail(email_from, email_to, msg.as_string())
        logger.info("Email sent successfully.")
    except Exception as e:
        logger.critical("Error occurred while sending email.")
        logger.error(e)


def main():
    env = loadVars()

    token = getToken(env["TRUTH_USERNAME"], env["TRUTH_PASSWORD"])

    statuses = getStatuses(token)

    formattedStatuses = formatStatuses(statuses)

    sendEmail(
        formattedStatuses, env["EMAIL_TO"], env["EMAIL_FROM"], env["EMAIL_PASSWORD"]
    )


if __name__ == "__main__":
    main()
