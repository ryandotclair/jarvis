import os
import time
import redis
import json
import twilio.twiml
from flask import Flask, request, jsonify
from twilio.rest import Client
from chatbot import ask, get_hashed_user_id
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
redis_loc = os.environ['REDIS_LOC']
redis_access_key = os.environ['REDIS_ACCESS_KEY']

client = Client(account_sid, auth_token)
r = redis.Redis(
    host=redis_loc,
    port=6380,
    password=redis_access_key, # use your Redis password
    ssl=True,
    decode_responses=True)

app.logger.info("App started")

@app.route('/bot', methods=['POST'])
def bot():
    # This function parses the webhook from Twilio, grabs the question from user, and passes it on to OpenAI
    user_phone = request.values["From"]

    user_id = get_hashed_user_id(user_phone)
    incoming_msg = request.values['Body']
    app.logger.info("Recieving a request from Twilio. User: {}, Message: {}".format(user_id,incoming_msg))
    app.logger.debug("Redis r value is: {}".format(r))

    # Clear conversation if sending a RESET (for dev purposes)
    if incoming_msg=="RESET":
        r.delete(user_id)
        app.logger.info("Deleting conversation.")
        return '200'
    # Check if new user, if so load up their profile into Redis.
    if r.exists(user_id):
        #This person has texted before
        app.logger.debug("This person has texted Jarvis before")
    else:
        #This person hasn't texted before
        app.logger.debug("This person hasn't texted Jarvis before")
        messages=[
        {"role": "system", "content": "Your name is Jarvis. You are an intelligent personal AI assistant for Azure Spring Apps Enterprise. You know ASA-E means Azure Spring Apps Enterprise, but you don't use that acronym. Your creator's name is Ryan Clair. In Azure Spring Apps Enterprise you can promote cyan's Staging to Production, tell the number of apps currently running, what apps are running, and provide the URL of any app that's running. Anything outside of Azure Spring Apps Enterprise you can not help them and you will politely decline. Any question you don't know the answer to, or any question that is subjective in nature, you will politely tell them you don't know the answer. If asked about the 🧠 emoji, you explain it denotes that the answer has been grounded in truth."},
        {"role": "user", "content": "What is ASA-E?"},
        {"role": "assistant", "content": "Azure Spring Apps Enterprise, is a fully managed app platform, optimized for Spring workloads. It was jointly built by Microsoft and VMware."},
    ]

        user_record= {"messages":json.dumps(messages)}
        r.set(user_id, json.dumps(user_record))
        app.logger.debug("Person has been added to redis")
        app.logger.debug("Here's redis record: {}".format(json.loads(r.get(user_id))))
    # Get an answer from OpenAI
    answer = ask(incoming_msg,user_id)

    app.logger.info("BOT: The answer: {}".format(answer))

    # Adds OpenAI's answer to the conversation
    # append_interaction_to_conversation(answer)

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
    message_status = check_message_status(messageSid)
    delivery_check(messageSid=messageSid,answer=answer,user_phone=user_phone)

    message_status = check_message_status(messageSid)
    app.logger.debug("LOOP: message has been deemed delivered ({}) for messageSid: {}".format(message_status, messageSid))
    # Remove messages status once message has been delivered to free up memeory
    r.delete(messageSid)

    # Check for failed or undelivered status of the message, and resend if caught
    while message_status != "delivered":
        message_status = check_message_status(messageSid)
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

            # set the new message sid for the loop
            messageSid = message.sid
            r.set(messageSid, "init")
            r.expire(messageSid, 60) # set to auto delete in 60 seconds
            app.logger.debug("LOOP: New messageSid: {}".format(messageSid))

        if timeout == 5 or resent_count > 2:
            app.logger.warning("BOT LOOP: An error has occured. Failed to send to Twilio.")
            break

        timeout +=1
        time.sleep(1)

    message_status = check_message_status(messageSid)
    app.logger.debug("LOOP: message has been deemed delivered ({}) for messageSid: {}".format(message_status, messageSid))
    # Remove env var that stores the messages status once message has been delivered to free up memeory
    # resp = twiml.Response()
    # resp.message(answer, to=user_phone)
    # return str(resp)
    return(message.sid)

def delivery_check(messageSid,answer,user_phone):
    # Check for failed or undelivered status of the message, and resend if caught
    timeout = 0
    resent_count = 0
    delivery_check = True

    while delivery_check:
        message_status = check_message_status(messageSid)
        app.logger.debug("BOT LOOP: Not delivered yet, current value of messageSid is: {}".format(message_status))
        app.logger.debug("BOT LOOP: Not delivered yet, current timeout is: {}".format(timeout))
        app.logger.debug("BOT LOOP: Not delivered yet, current resent count is: {}".format(resent_count))

        if message_status == "delivered":
            delivery_check = False
        elif message_status == "sent":
            delivery_check = False

        if message_status == "failed":
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

            # app.logger.debug("LOOP: Popping env: {}".format(messageSid))
            # unset message sid, counting it as "lost"
            # r.delete(messageSid)
            # set the new message sid for the loop
            messageSid = message.sid
            r.set(messageSid, "init")
            r.expire(messageSid, 60) # set to auto delete in 60 seconds
            app.logger.debug("LOOP: New env: {}".format(messageSid))

        if message_status == "undelivered":
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

            # app.logger.debug("LOOP: Popping env: {}".format(messageSid))
            # unset message sid, counting it as "lost"
            # r.delete(messageSid)
            # set the new message sid for the loop
            messageSid = message.sid
            r.set(messageSid, "init")
            r.expire(messageSid, 60) # set to auto delete in 60 seconds
            app.logger.debug("LOOP: New env: {}".format(messageSid))

        if timeout == 10 or resent_count > 10:
            app.logger.warning("BOT LOOP: An error has occured. Failed to send to Twilio.")
            # Assume it eventually delivered (Twilio's API is so fincky)
            delivery_check = False

        timeout +=1
        time.sleep(1)

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
    #app.logger.info("CALLBACK: value of messagesid is: {}".format(request.values))

    messageSid = request.values["MessageSid"]
    messageStatus = str(request.values["MessageStatus"])
    r.set(messageSid, messageStatus)
    r.expire(messageSid,60) # auto deletes key after 1 min
    app.logger.info("CALLBACK: Status from redis: {}".format(r.get(messageSid)))

    return '200'

def check_message_status(messageSid):
    if r.exists(messageSid):
        # Assuming it's being tracked...
        return r.get(messageSid)
    else:
        return "pending"

if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=8080)
    pass
