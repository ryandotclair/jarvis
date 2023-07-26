This follows the tutorial found [here](https://www.twilio.com/blog/openai-gpt-3-chatbot-python-twilio-sms)

In a "key.env" file, place these two lines in
```
OPENAI_KEY="(your_openAI_key)"

SECRET_KEY="(your_twillio_secret)"
```

To run this locally using Docker run:

```
docker build -t llm-chat-python .

docker run -it -v .:/app -p 8080:8080 llm-chat-python
```