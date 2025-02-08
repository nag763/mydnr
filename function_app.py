import azure.functions as func
import datetime
import json
import logging
from dotenv import load_dotenv
import os
import feedparser
from datetime import datetime, timedelta
from openai import OpenAI
from azure.communication.email import EmailClient

openai_plot = """
The main purpose is to aggregate in a readable way the news content that  will be provided

The JSON input will be a list of the following dictionary :

{
                        "title": entry.title,
                        "link": entry.link,
                        "summary": entry.summary,
                        "published": entry.published
}

For the JSON Input that will be provided, it should :

* Provide a short and friendly summary at the begining of the email, telling what are the topics
* Extract the relevant data from summary subdictionnaries
* If the article is found interesting, it takes the summary and sum it up in few words
* Asides of that, for the articles selected, it should provide a link to the original article
* The output content should be a HTML, that should be readable on mobile phone format, if needed include a little of CSS styling
* The spacing between headers and its content need to be sufficent enough for readings.
* I also want the origin site of the article to appear within the title (ie for the title "The best article", the title should be "The best article (CNN)")

Don't add extra tags in the response, I just want the content to be in HTML as it will be send by mail. I also do not want the markdown html blocks to appear in the response.
"""

app = func.FunctionApp()

def send_a_mail(sender_mail: str, receiver_mail: str, mail_server: str, subject:str, content: str):
    try:
        client = EmailClient.from_connection_string(mail_server)

        message = {
            "senderAddress": sender_mail,
            "recipients": {
                "to": [{"address": receiver_mail}]
            },
            "content": {
                "subject": subject,
                "html": content
            },
        }

        poller = client.begin_send(message)
        result = poller.result()
        logging.info("Message sent: ", result)

    except Exception as ex:
        logging.error(f"An error happened while sending the mail {ex}")



@app.timer_trigger(schedule="0 0 6 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False)
def NewsAggregator(myTimer: func.TimerRequest) -> None:

    load_dotenv()

    curr_date = datetime.now()

    # Stores the previous day number
    yesterday_date = curr_date - timedelta(1)
    yesterday_date_number = yesterday_date.day

    news_stack = []

    rss_feeds : str = os.getenv("RSS_FEEDS")
    api_key : str = os.getenv("API_KEY")
    sender_mail : str = os.getenv("MAIL_FROM")
    receiver_mail : str = os.getenv("MAIL_TO")
    mail_server : str = os.getenv("MAIL_SERVER")

    if not rss_feeds:
        logging.error("No RSS feed defined, exiting")
        return -1

    if not api_key:
        logging.error("No API key defined, exiting")
        return -1
    client = OpenAI(api_key=api_key)

    rss_feeds = rss_feeds.split(',')
    logging.debug(f"RSS feeds: {rss_feeds}")

    for feed in rss_feeds:
        if feed:
            logging.info(f"Processing feed {feed}")
            parsed_feed = feedparser.parse(feed)
            for entry in parsed_feed.entries:
                if entry.published_parsed.tm_mday == yesterday_date_number:
                    news_stack.append({
                        "title": entry.title,
                        "link": entry.link,
                        "summary": entry.summary,
                        "published": entry.published
                    })


    if not news_stack:
        logging.warning("No news found yesterday, so bad!")
        send_a_mail(sender_mail, receiver_mail, mail_server, subject=f"Today's {curr_date.day}/{curr_date.month} news (nothing)",content="Seems like there is nothing to report today")
        return

    logging.info(f"Found {len(news_stack)} news articles")
    response = client.chat.completions.create(model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": openai_plot},
        {"role": "user", "content": json.dumps(news_stack)},
    ])
    mail_content = response.choices[0].message.content
    send_a_mail(sender_mail, receiver_mail, mail_server, subject=f"Today's {curr_date.day:02d}/{curr_date.month:02d} news", content=mail_content)
    logging.info("RSS fetched, mail sent, exiting...")

if __name__ == '__main__':
    NewsAggregator(None)
