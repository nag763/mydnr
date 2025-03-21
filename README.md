# mydnr (My daily news recap)

<div align="center"><img src="https://raw.githubusercontent.com/nag763/rssfeedaggregator/refs/heads/master/.github/preview.webp"></img></div>

## Purpose

The purpose of this project is to create an RSS news aggregator that summarizes the latest tech news using GPT-4.0 mini. This tool collects news from various RSS feeds and provides concise summaries to keep you updated with the most important information in the tech world.

It actually helps me to win time by avoiding researchs on several blogs to get the latest news, while having a summary per mail everyday is pretty handful.

There was also a learning purpose behind in getting to learn the Azure ecosystem, as well as getting to know OpenAI's API features and purposes.

## Features

- Aggregates news from multiple RSS feeds
- Uses GPT-4.0 mini to generate summaries
- Provides a user-friendly interface to browse news

## Flow

```mermaid
graph TB
    style Start fill:#0000FF,stroke:#0000FF,stroke-width:2px
    style RSSFeeds fill:#FFA500
    style CheckArticles fill:#FFA500
    style OpenAIRecap fill:#008000
    style SendEmail fill:#800080
    style ClientInteraction fill:#0000FF,stroke:#0000FF,stroke-width:2px
    style HTTPTrigger fill:#FF0000
    style OpenAIHighlight fill:#008000
    style ReturnResponse fill:#800080
    style OriginalLink fill:#808080,stroke:#000000

    Start("Start: Scheduled Azure Function (6 AM)") --> RSSFeeds("Fetch RSS Feeds")
    RSSFeeds --> CheckArticles("Get articles from previous day")
    CheckArticles --> OpenAIRecap("Send content to OpenAI API (short recap)")
    OpenAIRecap --> SendEmail("Send email with short recap\n(Azure Email Service)")
    SendEmail --> ClientInteraction("Client Interaction")
    ClientInteraction --> HTTPTrigger("HTTP Trigger: Request long recap")
    ClientInteraction --> OriginalLink("Link to original article")
    HTTPTrigger --> OpenAIHighlight("OpenAI API: Generate long recap & highlights")
    OpenAIHighlight --> ReturnResponse("Return long recap")


```


* Blue: Represents the starting point and user interaction points.
* Orange: Steps related to fetching and processing RSS feeds.
* Green: Interactions with OpenAI for generating recaps and highlights.
* Purple: Steps involving email and recap responses.
* Gray: Represents static links to the original article.
* Red: Highlights the HTTP-triggered function for generating a long recap.

Every day at 6 AM, an Azure function is triggered to fetch content from a list of RSS feeds. It collects articles that were published the previous day, then sends this data to OpenAI's API to generate a short recap.

Once the recap is generated, it is emailed to the client using Azure's mailing functionality. If the client is interested in a more detailed recap, they can request it by clicking a button. This action triggers an HTTP Azure function, which sends the full article to OpenAI for a longer recap and highlights.

The long recap is then returned as the response from the HTTP function. Alternatively, if the client prefers, they can follow a link to the original article instead of receiving a recap.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/nag763/mydnr
    ```
2. Navigate to the project directory:
    ```bash
    cd mydnr
    ```
3. Install the required dependencies:
    ```bash
    pip install
    ```

## Usage

```bash
python main.py
```

## How it works

1. The first step is basicly about fetching the RSS feeds in the `RSS_FEEDS` environment variable. These are CSV separated such as : `https://feedprovider1/rss,https://feedprovider2/rss`
2. Once these feeds are aggregated into a JSON, this JSON is sent to OpenAI to have a summary generated given the plot.
3. Given OpenAI's response, a mail will be sent to the mail precised in `MAIL_TO` environment variable.
4. The mail is received by the recipient.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.
