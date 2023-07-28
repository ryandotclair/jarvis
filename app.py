import os
from flask import Flask, request, session, jsonify
from twilio.rest import Client
from chatbot import ask, append_interaction_to_chat_log
from logging.config import dictConfig

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
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
chatbot_number = os.environ['BOT_NUMBER'] # no dashes, include country code

client = Client(account_sid, auth_token)

app.logger.info("App started")


@app.route('/bot', methods=['POST'])
def bot():
    #debug
    app.logger.info("Recieving payload: {}".format(request.values))
    incoming_msg = request.values['Body']
    chat_log = session.get('chat_log')

    answer = ask(incoming_msg, chat_log)

    user_phone = request.values["From"]

    #debug
    app.logger.info("The answer: {}".format(answer))
    session['chat_log'] = append_interaction_to_chat_log(incoming_msg, answer, chat_log)

    message = client.messages \
                .create(
                    body=answer,
                    from_=chatbot_number,
                    to=user_phone
                )

    return(message.sid)

@app.route('/healthz', methods=['GET'])
def health():

    return jsonify("up")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
