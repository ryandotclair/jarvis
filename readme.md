Shout out to this tutorial [here](https://www.twilio.com/blog/openai-gpt-3-chatbot-python-twilio-sms) that helped me get started.

Expected Environment Variables:
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

To run develop/run this locally using Docker:

```
docker build -t llm-chat-python .

docker run -it -v .:/app -p 8080:8080 llm-chat-python
```