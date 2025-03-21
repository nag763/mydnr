import azure.functions as func
import datetime
import json
import logging
import feedparser
import base64
from datetime import datetime, timedelta
from openai import AzureOpenAI
from azure.communication.email import EmailClient
import traceback

from settings import Settings

app = func.FunctionApp()

def error_handler(fun): 
    '''Decorator that wraps and catch exceptions priting them into apps insights.'''
  
    def wrap(*args, **kwargs): 
        try:
            result = fun(*args, **kwargs) 
        except Exception as e:
            logging.error("An error has been met while executing function", e)
            logging.error(traceback.format_exc())
            settings = Settings()
            send_a_mail(
                settings.sender_mail,
                settings.receiver_mail,
                settings.mail_server,
                subject="Error met while attempting to fetch today news",
                content=traceback.format_exc(),
            )
            return func.HttpResponse(
                    "An unrecoverable error has been met", status_code=500
            )
        return result
    return wrap 
  

def call_chat_gpt_4o_mini(endpoint:str, api_key: str, system_role: str, user_content: str):
    client = AzureOpenAI(api_key=api_key, azure_endpoint=endpoint, api_version="2024-02-01")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": user_content},
        ],
    )

    openai_response = response.choices[0].message.content

    return openai_response


def send_a_mail(
    sender_mail: str, receiver_mail: str, mail_server: str, subject: str, content: str
):
    client = EmailClient.from_connection_string(mail_server)

    message = {
        "senderAddress": sender_mail,
        "recipients": {"to": [{"address": receiver_mail}]},
        "content": {"subject": subject, "html": content},
    }

    poller = client.begin_send(message)
    result = poller.result()
    logging.info("Message sent: ", result)


@error_handler
@app.timer_trigger(
    schedule="0 0 6 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def NewsAggregator(myTimer: func.TimerRequest) -> None:
    settings = Settings()

    curr_date = datetime.now()

    # Stores the previous day number
    yesterday_date = curr_date - timedelta(1)
    yesterday_date_number = yesterday_date.day

    news_stack = []

    if not settings.rss_feeds:
        logging.error("No RSS feed defined, exiting")
        return -1

    if not settings.open_ai_api_key:
        logging.error("No API key defined, exiting")
        return -1

    rss_feeds = settings.rss_feeds.split(",")

    logging.debug(f"RSS feeds: {rss_feeds}")

    for feed in rss_feeds:
        if feed:
            logging.info(f"Processing feed {feed}")
            parsed_feed = feedparser.parse(feed)
            for entry in parsed_feed.entries:
                if hasattr(entry, 'published_parsed') and entry.published_parsed.tm_mday == yesterday_date_number:
                    news_stack.append(
                        {
                            "title": entry.title,
                            "link": entry.link,
                            "summary": entry.summary,
                            "published": entry.published,
                            "recap_link": f"{settings.function_url}?payload={base64.urlsafe_b64encode(
                                json.dumps({"feed": feed, "link": entry.link}).encode()
                            ).decode()}&code={settings.function_key}",
                        }
                    )

    if not news_stack:
        logging.warning("No news found yesterday, so bad!")
        send_a_mail(
            settings.sender_mail,
            settings.receiver_mail,
            settings.mail_server,
            subject=f"Today's {curr_date.day}/{curr_date.month} news (nothing)",
            content="Seems like there is nothing to report today",
        )
        return

    logging.info(f"Found {len(news_stack)} news articles")

    chatgpt_user_content = json.dumps(news_stack)

    openai_response = call_chat_gpt_4o_mini(
        settings.azure_endpoint,
        settings.open_ai_api_key,
        system_role=settings.openai_plot_for_rss_recap,
        user_content=chatgpt_user_content,
    )

    openai_response_parsed = json.loads(openai_response)

    logging.info(f"Response received from OpenAI : {openai_response_parsed}")

    send_a_mail(
        settings.sender_mail,
        settings.receiver_mail,
        settings.mail_server,
        subject=f"Today's {curr_date.day:02d}/{curr_date.month:02d} tech insights : {openai_response_parsed["mailTitle"]}",
        content=openai_response_parsed["mailContent"],
    )
    logging.info("RSS fetched, mail sent, exiting...")


@error_handler
@app.route(route="NewsRecap", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def NewsRecap(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    settings = Settings()

    payload_base64 = req.params.get("payload")
    if not payload_base64:
        logging.error("No payload provided, exiting")
        return func.HttpResponse("No payload provided", status_code=400)

    payload = json.loads(base64.urlsafe_b64decode(payload_base64).decode())

    parsed_feed = feedparser.parse(payload["feed"])
    for entry in parsed_feed.entries:
        if entry.link == payload["link"]:
            openai_response = call_chat_gpt_4o_mini(
                settings.azure_endpoint,
                settings.open_ai_api_key,
                system_role=settings.openai_plot_for_article_recap,
                user_content=entry.content[0].value,
            )
            return func.HttpResponse(
                openai_response, status_code=200, mimetype="text/html"
            )
                

    return func.HttpResponse("The article wasn't found", status_code=204)


if __name__ == "__main__":
    """
    The news aggregator can't be run locally as it requires the Azure Function runtime to be executed, hence this trick.
    """
    NewsAggregator(None)
