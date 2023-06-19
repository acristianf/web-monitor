from email.message import EmailMessage
import os
from pathlib import Path
from bs4 import BeautifulSoup
from time import sleep
import logging
import requests
import smtplib
import hashlib
import json


WEBSITE = "https://seu.frc.utn.edu.ar/?pIs=1286"

creds_fp = open("credentials.json", "r")
creds = json.load(creds_fp)

FROM = creds["from_mail"]
PASS = creds["from_pass"]

TO = creds["to_mail"]

SECS_TO_SLEEP = 600  # 10 minutes


def process_html(string: str) -> str:
    soup = BeautifulSoup(string, "html.parser")

    for s in soup.select("script"):
        s.extract()

    for s in soup.select("meta"):
        s.extract()

    for s in soup.select("img"):
        s.extract()

    return str(soup)


def send_mail() -> None:
    msg = EmailMessage()
    msg["Subject"] = f"{WEBSITE} was changed!"
    msg["From"] = FROM
    msg["To"] = TO
    with smtplib.SMTP(host="smtp-mail.outlook.com", port=587) as server:
        server.starttls()
        server.login(FROM, PASS)
        server.sendmail(msg["From"], msg["To"], msg.as_string())


def website_was_changed() -> bool:
    headers = {
        "Cache-Control": "no-cache",
    }
    response_data = requests.get(url=WEBSITE, headers=headers)
    response_data = process_html(response_data.text)
    hash_response = hashlib.sha224(response_data.encode("utf-8")).hexdigest()

    if not Path("sha224.txt").exists():
        open(file="sha224.txt", mode="w+").close()

    fp = open(file="sha224.txt", mode="r")
    hash_previous = fp.read()
    fp.close()

    if hash_response == hash_previous:
        return False
    else:
        fp = open(file="sha224.txt", mode="w")
        fp.write(hash_response)
        fp.close()

        return True


def main():
    log = logging.getLogger(name=__name__)
    logging.basicConfig(
        level=os.environ.get("LOGLEVEL", "INFO"), format="%(asctime)s %(message)s"
    )
    log.info("Running website monitor...")

    while True:
        try:
            if website_was_changed():
                log.info("Webpage was changed.")
                send_mail()
            else:
                log.info("Webpage was not changed.")
        except Exception as e:
            log.info("Error checking website. ERROR: '%s'" % e)
        sleep(SECS_TO_SLEEP)


if __name__ == "__main__":
    main()
