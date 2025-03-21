import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


from dotenv import load_dotenv

openai_plot_for_rss_recap = """
Transform a JSON input news list into a structured HTML email content.

The goal is to create an email from a JSON input that is both readable and informative, summarizing the news content in an engaging way.

## JSON Input Structure

The input will be a list of dictionaries, where each dictionary represents a news article with the following fields:
- "title": Title of the article
- "link": URL link to the article
- "summary": Brief summary of the article
- "published": Publication date
- "recap_link": The link to an Azure function that will send a recap of the article in a separate mail

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
- Add a link to the base64 encoded article link right after the original article link. The purpose of this is to send to the function a request to send a recap in a separate mail.
- I do want an horizontal separator between each article.
- The send me a recap in a separate mail link could be a button.

Here is a sample article template you can base yourself on :

```
<h2>Article title (source site)</h2>
<p>Article summary.</p>
<a href="article_link">Text inviting to check the original article</a>
<a href="{recap_link}">Show me a longer recap</a>
```

## Output Format

The output format will be a JSON dictionnary with the following fields:
- "mailTitle": A string summarizing topics as comma-separated tags.
- "mailContent": A well-formatted HTML string.

- The content should be formatted in plain HTML for emails.
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

openai_plot_for_article_recap = """
I want a recap of the provided content in a structured HTML format.

The recap shouldn't take more than 3 minutes to read and should be engaging and informative.

Code blocks and images from the original can be included.

## Input

The input will be a JSON object with the following fields:

- "title": Title of the article
- "content": Main content of the article
- "link": URL link to the article

## Output

The output should be a plain HTML content with the following structure:


- A header with the original article title.
- The output should be structured in a way that the user can quickly grasp the main points of the article, whcih means :
    * It should be structured with sections and sections title.
    * It should have a clear introduction and conclusion.
    * It should have a section after introduction with the key take aways.
    * It should then have a main block with the content of the article shortened.
    * It should have a section with the opinion of the model.
    * It should have a section with recommendations for further reading.
    * It should have a section with the original article link that is provided in the input.
- Do not include extra markdown tag, the output should be plain HTML, it will be shown as received to the user triggering the function.
- The output should make a focus on being readable for a user on mobile phone, with dark mode styling being enabled.
- It should be readable in 3 to 5 minutes.
"""


class Settings:
    """
    Application settings
    """

    def __init__(self):
        load_dotenv()
        
        key_vault = os.getenv("KEY_VAULT")
        key_vault_uri = f"https://{key_vault}.vault.azure.net"
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=key_vault_uri, credential=credential)
        
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.rss_feeds: str = os.getenv("RSS_FEEDS")
        self.open_ai_api_key: str = client.get_secret("OPEN-AI-API-KEY").value
        self.sender_mail: str = client.get_secret("MAIL-FROM").value
        self.receiver_mail: str = os.getenv("MAIL_TO")
        self.mail_server: str = client.get_secret("MAIL-SERVER").value
        self.function_url : str =  f'https://{os.getenv("WEBSITE_HOSTNAME")}/api/NewsRecap'
        self.function_key : str = client.get_secret("FUNCTION-KEY").value
        self.openai_plot_for_rss_recap: str = openai_plot_for_rss_recap
        self.openai_plot_for_article_recap: str = openai_plot_for_article_recap