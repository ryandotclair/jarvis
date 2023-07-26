# import os
from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
from chatbot import ask, append_interaction_to_chat_log

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

print("started")

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values['Body']
    chat_log = session.get('chat_log')

    answer = ask(incoming_msg, chat_log)
    session['chat_log'] = append_interaction_to_chat_log(incoming_msg, answer, chat_log)

    r = MessagingResponse()
    r.message(answer)
    return str(r)

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=8080)
