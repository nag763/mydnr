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

<div align="center"><img src="https://raw.githubusercontent.com/nag763/rssfeedaggregator/refs/heads/master/.github/flow.svg"></img></div>


## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/nag763/rssfeedaggregator
    ```
2. Navigate to the project directory:
    ```bash
    cd rssfeedaggregator
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
