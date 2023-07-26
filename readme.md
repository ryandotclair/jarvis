Shout out to this tutorial [here](https://www.twilio.com/blog/openai-gpt-3-chatbot-python-twilio-sms) that helped me get started.


# Expected Environment Variables
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
```

# Steps to Run Locally

Using Docker:

```
docker build -t llm-chat-python .

docker run -it -v .:/app -p 8080:8080 llm-chat-python
```
In docker terminal:
```
# run all your export commands for env vars

python /app/app.py
```
Outside of docker terminal, in another terminal window:
```
# Install ngrok. This tool gives you a temporarily "published" URL
pip install pyngrok

# Run the tool, and grab the public URL that redirects to you
# Put this URL in your Twillio's phone number's messaging webhook
ngrok http 8080
```
