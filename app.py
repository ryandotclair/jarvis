import os
import time
from flask import Flask, request, session, jsonify
from twilio.rest import Client
from chatbot import ask, append_interaction_to_conversation
from logging.config import dictConfig

# Configures Flasks's logging format
level = os.getenv('LOGGING_LEVEL', 'INFO')
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': level.upper(),
        'handlers': ['wsgi']
    }
})


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
callback_url = os.environ['BOT_URL'] + '/callback'
chatbot_number = os.environ['BOT_NUMBER'] # no dashes, include country code

client = Client(account_sid, auth_token)

app.logger.info("App started")

@app.route('/bot', methods=['POST'])
def bot():
    # This function parses the webhook from Twilio, grabs the question from user, and passes it on to OpenAI
    app.logger.info("Recieving payload: {}".format(request.values))
    incoming_msg = request.values['Body']

    # Get an answer from OpenAI
    answer = ask(incoming_msg)

    user_phone = request.values["From"]

    app.logger.info("BOT: The answer: {}".format(answer))

    # Adds OpenAI's answer to the conversation
    append_interaction_to_conversation(answer)

    message = client.messages.create(
                    body=answer,
                    from_=chatbot_number,
                    status_callback=callback_url,
                    to=user_phone
                )

    timeout = 0
    resent_count = 0
    app.logger.debug("BOT: message sid content is: {}".format(message.sid))

    messageSid = message.sid
    message_status = os.environ.get(messageSid)

    # Check for failed or undelivered status of the message, and resend if caught
    while message_status != "delivered":
        message_status = os.environ.get(messageSid)
        app.logger.debug("BOT LOOP: Not delivered yet, current value of messageSid is: {}".format(message_status))
        app.logger.debug("BOT LOOP: Not delivered yet, current timeout is: {}".format(timeout))
        app.logger.debug("BOT LOOP: Not delivered yet, current resent count is: {}".format(resent_count))

        if message_status == "failed" or message_status == "undelivered":
        # if it's been deamed failed by Twilio, try again
            message = client.messages.create(
                body=answer,
                from_=chatbot_number,
                status_callback=callback_url,
                to=user_phone
            )
            #rest timeout clock
            timeout = 0
            resent_count+=1

            app.logger.debug("LOOP: Popping env: {}".format(messageSid))
            # unset message sid, counting it as "lost"
            os.environ.pop(messageSid)
            # set the new message sid for the loop
            messageSid = message.sid
            app.logger.debug("LOOP: New env: {}".format(messageSid))

        if timeout == 5 or resent_count > 2:
            app.logger.warning("BOT LOOP: An error has occured. Failed to send to Twilio.")
            break

        timeout +=1
        time.sleep(1)

    message_status = os.environ.get(messageSid)
    app.logger.debug("LOOP: message has been deemed delivered ({}) for messageSid: {}".format(message_status, messageSid))
    # Remove env var that stores the messages status once message has been delivered to free up memeory
    os.environ.pop(messageSid)

    return(message.sid)

@app.route('/healthz', methods=['GET'])
def health():
    # This endpoint is used for Readiness Probes.
    return jsonify("up")

@app.route('/callback', methods=['POST'])
def callback():
# This function is used used for Twilio's callback feature. Twilio will make a POST to this endpoint,
# reporting the status of the message  as it changes (delivered, sent, failed, undelivered, etc). This
# uses the unique identifier of the message as the key, and the status as the value, in an environment 
# variable. This is used by the /bot endpoint to confirm message delivered successfully.
    app.logger.debug("CALLBACK: value of messagesid is: {}".format(request.values))

    messageSid = request.values["MessageSid"]
    messageStatus = request.values["MessageStatus"]

    # Set message status as env for /bot to pick up
    os.environ[messageSid] = messageStatus

    return '200'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

