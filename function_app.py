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
Transform a JSON input news list into a structured HTML email content.

The goal is to create an email from a JSON input that is both readable and informative, summarizing the news content in an engaging way.

## JSON Input Structure

The input will be a list of dictionaries, where each dictionary represents a news article with the following fields:
- "title": Title of the article
- "link": URL link to the article
- "summary": Brief summary of the article
- "published": Publication date

## JSON Output Structure

The JSON output should consist of:
- "mailTitle": A string summarizing topics as comma-separated tags
- "mailContent": A well-formatted HTML string

## Constraints

### Mail Title Constraints
- The mail title should be a summary of topics as comma-separated tags.

### Mail Content Constraints
- Begin with a friendly summary of topics.
- Extract and summarize relevant data from each entry.
- For interesting articles, provide a concise summary and ensure the inclusion of the article link.
- Each article recapped in the mail should indicate the source site at the end of the title.
- Ensure HTML is mobile-friendly; include minimal CSS if needed. 
- The articles should be spaced enough within the mail.
- Maintain sufficient spacing for readability.
- Avoid extra tags or markdown in the HTML output.

Here is a sample article template you can base yourself on :

```
<h2>Article title (source site)</h2>
<p>Article summary.</p><a href="article_link">Text inviting to check the original article</a>
```

## Output Format

- The content should be formatted in plain HTML for emails.
- Avoid using markdown or additional tags beyond basic HTML and CSS.
- Do not add markdown tags to the OpenAI's API response, as it should be processable by a program.

## Steps

1. **Extract Topics**: Identify and list topics from article titles.
2. **Create Title**: Formulate the mail title with topics and date.
3. **Draft Content**:
   - Start with a friendly overview of topics.
   - For each interesting article, summarize and append a link.
4. **Format Output**:
   - Ensure HTML is clear and mobile-friendly.
   - Adjust spacing between headers and content.
   - Embed source site information within the title.
5. **Validate HTML**: Ensure there are no extraneous tags or markdown.

## Notes

- Focus on creating a clear, easily digestible format.
- Tailor titles to reflect both topic and source.
- Design with mobile readability in mind.
"""

app = func.FunctionApp()

def send_a_mail(sender_mail: str, receiver_mail: str, mail_server: str, subject:str, content: str):
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
    ],)
    
    openai_response = response.choices[0].message.content
    
    openai_response_parsed = json.loads(openai_response)
    
    logging.info(f"Response received from OpenAI : {openai_response_parsed}")
    
    send_a_mail(sender_mail, receiver_mail, mail_server, subject=f"Today's {curr_date.day:02d}/{curr_date.month:02d} tech insights : {openai_response_parsed["mailTitle"]}", content=openai_response_parsed["mailContent"])
    logging.info("RSS fetched, mail sent, exiting...")

if __name__ == '__main__':
    NewsAggregator(None)
