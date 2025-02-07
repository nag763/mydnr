import azure.functions as func
import datetime
import json
import logging
from dotenv import load_dotenv 
import os
import feedparser
from datetime import datetime, timedelta

app = func.FunctionApp()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def NewsAggregator(myTimer: func.TimerRequest) -> None:
    
    load_dotenv()
    
    # Stores the previous day number
    yesterday_date = datetime.now() - timedelta(1)
    
    news_stack = []
    
    rss_feeds : str = os.getenv("RSS_FEEDS")
    api_key : str = os.getenv("API_KEY")
    
    if not rss_feeds:
        logging.error("No RSS feed defined, exiting")
        return -1
    
    rss_feeds = rss_feeds.split(',')
    
    
    for feed in rss_feeds:
        if feed:
            logging.info(f"Processing feed {feed}")
            parsed_feed = feedparser.parse(feed)
            for entry in parsed_feed.entries:
                if entry.published_parsed.tm_mday == yesterday_date:
                    news_stack.append({
                        "title": entry.title,
                        "link": entry.link,
                        "summary": entry.summary,
                        "published": entry.published
                    })     
            
    if not news_stack:
        logging.warning("No news found yesterday, so bad!")
    else:
        logging.info(f"Found {len(news_stack)} news articles")
    return 0