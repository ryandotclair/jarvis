import os
import openai
import logging
import requests
import json

openai.api_key = os.environ.get('OPENAI_KEY')

subscription = os.environ['AZURE_SUBSCRIPTION']
asae_instance = os.environ['ASAE_INSTANCE']
directory_id = os.environ['AZURE_DIRECTORYID']
app_id = os.environ['AZURE_APPID']
app_value_id = os.environ['AZURE_APP_VALUEID']
azure_rgo = os.environ['AZURE_RGO']
#debug
logging.info("chatbot started")
completion = openai.ChatCompletion()

# log = logging.getLogger("chatbot.sub")

messages=[
        {"role": "system", "content": "Your name is Jarvis. You are their personal AI assistant for Azure Spring Apps Enterprise. You know ASA-E means Azure Spring Apps Enterprise, but you avoid using that acroynm. Your model is based on OpenAI's gpt-3.5-turbo-0613, and was last updated by your developers on October 1, 2021. Your creator's name is Ryan Clair."},
        {"role": "user", "content": "What all can you do with Azure Spring Apps Enterprise?"},
        {"role": "assistant", "content": "At this time I can promote Staging to Production and I can tell you the number of apps currently in production."},
    ]

def get_data_with_authentication(url, token):
    print("Running GET with auth...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    # print(response)
    return response

def post_data_with_authentication(url, token, payload):
    print("Running POST with auth...")

    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.request("POST", url, headers=headers, json=payload)
    # print(response.text)
    return response

def azure_auth():
    url = "https://login.microsoftonline.com/{}/oauth2/token".format(directory_id)

    payload = "grant_type=client_credentials&client_id={}&client_secret={}&resource=https%3A%2F%2Fmanagement.azure.com%2F".format(app_id,app_value_id)

    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': 'fpc=AjtfSXJH2GxLg3UqoXUjQlmGw70iAwAAAITpVNwOAAAA; stsservicecookie=estsfd; x-ms-gateway-slice=estsfd'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print("Azure auth response: {}".format(str(response.text)))
    bearer_token = response.json()["access_token"]

    return bearer_token

def fetch_app_names():
    url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance)

    azure_token = azure_auth()
    print(azure_token)

    try:
        print("Authenticating...")
        response = get_data_with_authentication(url, azure_token)


        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            print("Authenticated")
            data = response.json()["value"]
            # print(data)
            # print("/////////////")
            app_list = []
            for i in data:
                app_list.append(i["name"])
            return str(app_list).strip("[").strip("]")
            # parsed = data
        else:
            error_message = f"Failed to fetch data. Status code: {response.status_code}"
            print(error_message)

    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        print(error_message)

def set_production():
    app = "cyan"
    query_url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps/{}/deployments/green?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance, app)
    set_url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps/{}/setActiveDeployments?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance, app)

    azure_token = azure_auth()
    # print(azure_token)

    try:
        print("Authenticating...")
        response = get_data_with_authentication(query_url, azure_token)

        active = response.json()["properties"]["active"]
        # print(active)
        if active:
            # Green is active, so need to set Blue to production
            print("green is active, switching to blue")
            payload = {
            "activeDeploymentNames": [
                "blue"
                ]
            }

            post_data_with_authentication(set_url, azure_token, payload)
            print("Done")
            return("started")
        else:
            # Blue is active, so need to set Green to production
            print("blue is active, switching to green")
            payload = {
            "activeDeploymentNames": [
                "green"
                ]
            }

            post_data_with_authentication(set_url, azure_token, payload)
            print("Done")
            return("started")
    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        print(error_message)

def ask(question, chat_log=None):
    logging.debug("chat_log's contents: {}".format(chat_log))
    # If this is the first conversation, ensure the model has the right context in who it is and what it does.
    messages=[
        {"role": "system", "content": "Your name is Jarvis. You are their personal AI assistant for Azure Spring Apps Enterprise. You know ASA-E means Azure Spring Apps Enterprise, but you avoid using that acroynm. Your model is based on OpenAI's gpt-3.5-turbo-0613, and was last updated by your developers on October 1, 2021. Your creator's name is Ryan Clair."},
        {"role": "user", "content": "What all can you do with Azure Spring Apps Enterprise?"},
        {"role": "assistant", "content": "At this time I can promote Staging to Production and I can tell you the number of apps currently in production."},
    ]

    if chat_log is None:
        logging.debug('going into if chat_log statement')
        chat_log = messages
        logging.debug('Chatlog contents: {}'.format(chat_log))

    # Add the question to the chat log for future context.
    chat_log = messages.append({"role":"user","content":question})

    logging.debug('Chatlog contents: {}'.format(chat_log))

    # Inform the model of which functions are available to it, and the context in which to run them.
    functions = [
        {
            "name": "fetch_app_names",
            "description": "Get current app names deployed into production",
            "parameters": {
                "type": "object",
                "properties" : {}
                }
        },
        {
            "name": "set_production",
            "description": "Set what is currently in cyan app's staging into production",
            "parameters": {
                "type": "object",
                "properties" : {}
                }
        }
    ]

    # Run the initial prompt through
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo-0613",
        messages = messages,
        functions = functions,
        function_call="auto"
    )

    logging.debug('response from openai is: {}'.format(response))

    # Grab the answer from the model
    response_message = response["choices"][0]["message"]["content"]
    logging.debug('answer is: {}'.format(response_message))

    # Look for whether or not the model thinks it should run a particular function.
    if response["choices"][0]["finish_reason"] == "function_call" and response["choices"][0]["message"]["function_call"]["name"] == "fetch_app_names":
        logging.debug("Running the fetch_app_names function...")

        # Run the function fetch_app_names, store the return value of the function in this dict
        use_functions = {
            "fetch_app_names": fetch_app_names()
        }

        # Pass the return value into the model for it to use it.
        return enrich_model(response, use_functions, messages)
    if response["choices"][0]["finish_reason"] == "function_call" and response["choices"][0]["message"]["function_call"]["name"] == "set_production":

        # Run the function set_production, store the return value of the function in this dict
        use_functions = {
            "set_production": set_production()
        }

        return enrich_model(response, use_functions, messages)
    return response_message

def enrich_model(response, use_functions, messages):
    # This function grab the name of the function the model ran, as well as it's contents.
    # Then passes it into the chat log and tells the model to respond with the newest context (function's values)

    # Grab function name
    function_name = response["choices"][0]["message"]["function_call"]["name"]
    # Grab the function's output
    fuction_to_call = use_functions[function_name]
    function_response = fuction_to_call

    # Add this to the chat log / conversation
    messages.append(
        {
            "role": "function",
            "name": function_name,
            "content": function_response,
        }
    )

    # Tell the model to give a new answer based on the additional values
    second_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages
    )

    # Pass the new response from GPT onn
    return second_response["choices"][0]["message"]["content"]

def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = messages
    chat_log = messages.append({"role":"assistant","content":answer})
    return chat_log