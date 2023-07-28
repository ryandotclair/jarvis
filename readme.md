
# How to deploy this to Azure Spring Apps Enterprise

```
az spring app deploy -n (app-name) -d default --source-path . --env OPENAI_KEY="" TWILIO_ACCOUNT_SID="" TWILIO_AUTH_TOKEN="" BOT_NUMBER="" SECRET_KEY="" AZURE_RGO="" AZURE_SUBSCRIPTION="" ASAE_INSTANCE="" AZURE_DIRECTORYID="" AZURE_APPID="" AZURE_APP_VALUEID=""
```

# Where to get the keys
- Open AI (req CC): https://platform.openai.com/account/api-keys
- Twilio SID/Auth (req CC): https://console.twilio.com/?frameUrl=/console
- Bot's phone number (Twilio): https://console.twilio.com/us1/develop/phone-numbers/manage/incoming

# Twilio Webhook Last Mile Configuration Steps

- Grab the URL to your app via:
    ```
    az spring app show -n (app-name)
    ```
- Navigate to your Twilio's [phone number](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming), click on it, scroll down to the Messaging Configuration section, under the "A message comes in" webhook, paste the URL in and append "/bot" to it.
- Text your bot 😀

# Additional (Optional) Things
## Expected Environment Variables
```
OPENAI_KEY="(your_openAI_key)"
# Found here (after signup): https://platform.openai.com/account/api-keys

SECRET_KEY="(random key for flask)"

TWILIO_ACCOUNT_SID="(twilio SID)"
# Found here (after signup): https://console.twilio.com/?frameUrl=/console

TWILIO_AUTH_TOKEN="(twilio auth token)"
# Found here (after signup): https://console.twilio.com/?frameUrl=/console

BOT_NUMBER="(twilio phone number)"
# Found here (after signup): https://console.twilio.com/us1/develop/phone-numbers/manage/incoming

AZURE_RGO="" 
# This is your Azure Resource Group

AZURE_SUBSCRIPTION="" 
# Your Azure Subscription ID

ASAE_INSTANCE="" 
# The ASA-E Instance name (for now hard coded to one instance)

AZURE_DIRECTORYID="" 
# Your Tenant ID

AZURE_APPID="" 
# Your "app registration"'s App ID in Azure Active Directory (used to auth the bot). This registered app needs full access to the ASA-E instance in question.

AZURE_APP_VALUEID=""
# Your "app registration" client secret.

```

## Steps to Run Locally

Using Docker:

```
docker build -t llm-chat-python .

docker run -it -v .:/app -p 8080:8080 llm-chat-python
```
In docker terminal:
```
# run all your export commands for env vars mentioned above
# And then run python command

python /app/app.py
```
Outside of docker terminal, in another terminal window:
```
# Install ngrok. This tool gives you a temporarily "published" URL
pip install pyngrok

# Run the ngrok tool
ngrok http 8080

# Grab the public URL that redirects to your localhost:8080
# Put this URL in your Twillio's phone number's messaging webhook
```

## Shout out
Big shout out to this tutorial [here](https://www.twilio.com/blog/openai-gpt-3-chatbot-python-twilio-sms) that helped me get started with this project.