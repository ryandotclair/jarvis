import os
from flask import Flask, request, session
from twilio.rest import Client
from chatbot import ask, append_interaction_to_chat_log

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
chatbot_number = os.environ['BOT_NUMBER'] # no dashes, include country code
client = Client(account_sid, auth_token)

print("started")

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values['Body']
    chat_log = session.get('chat_log')

    answer = ask(incoming_msg, chat_log)
    user_phone = request.values["From"]

    #debug
    print(answer)
    session['chat_log'] = append_interaction_to_chat_log(incoming_msg, answer, chat_log)

    message = client.messages \
                .create(
                    body=answer,
                    from_=chatbot_number,
                    to=user_phone
                )

    return(message.sid)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
