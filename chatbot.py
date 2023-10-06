import os
import openai
import logging
import requests
import json
import redis
import hashlib
from requests.adapters import HTTPAdapter, Retry

openai.api_key = os.getenv('OPENAI_KEY')
openai.api_version = "2023-09-01-preview"
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_APIBASE")
openai_deployment_name = os.getenv('OPENAI_DEPLOYMENT_NAME')

subscription = os.getenv('AZURE_SUBSCRIPTION')
asae_instance = os.getenv('ASAE_INSTANCE')
directory_id = os.getenv('AZURE_DIRECTORYID')
app_id = os.getenv('AZURE_APPID')
app_value_id = os.getenv('AZURE_APP_VALUEID')
azure_rgo = os.getenv('AZURE_RGO')
redis_loc = os.getenv('REDIS_LOC')
redis_access_key = os.getenv('REDIS_ACCESS_KEY')

logging.info("chatbot started")
completion = openai.ChatCompletion()
r = redis.Redis(
    host=redis_loc,
    port=6380,
    password=redis_access_key, # use your Redis password
    ssl=True)


def get_data_with_authentication(url, token):
    logging.debug("Running GET with auth...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    logging.debug("response from get_data_with_auth function: {}".format(response))
    return response

def post_data_with_authentication(url, token, payload):
    logging.debug("Running POST with auth...")

    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.request("POST", url, headers=headers, json=payload)
    logging.debug("response from post_data_with_auth function: {}".format(response))
    logging.debug("payload response from post_data_with_auth function: {}".format(response.text))
    return response

def azure_auth():
    try:
        url = "https://login.microsoftonline.com/{}/oauth2/token".format(directory_id)

        payload = "grant_type=client_credentials&client_id={}&client_secret={}&resource=https%3A%2F%2Fmanagement.azure.com%2F".format(app_id,app_value_id)

        headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'fpc=AjtfSXJH2GxLg3UqoXUjQlmGw70iAwAAAITpVNwOAAAA; stsservicecookie=estsfd; x-ms-gateway-slice=estsfd'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        logging.debug("response from azure_auth function: {}".format(response))

        bearer_token = response.json()["access_token"]

        return bearer_token

    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        logging.info(error_message)
        return "Error. Issue authenticating with Azure API"

def fetch_app_names():

    azure_token = azure_auth()
    logging.debug("fetch_app_names: this is the azure auth token: {}".format((azure_token)))

    try:
        url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance)
        response = get_data_with_authentication(url, azure_token)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            logging.debug("fetch_app_names: Authenticated to ASA-E API, grabbing app list")
            data = response.json()["value"]
            app_list = []
            for i in data:
                app_list.append(i["name"])
            converted_string = ', '.join(app_list)
            logging.debug("fetch_app_names: app list is: {}".format(converted_string))
            return converted_string

    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        logging.debug(error_message)
        return "Error. There was an error in retrieving the list."

def get_app_url(app_name=None):
    if app_name == None:
        return "Error. The app name is required"

    azure_token = azure_auth()
    logging.debug(azure_token)

    try:
        get_url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps/{}?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance, app_name)
        response = get_data_with_authentication(get_url, azure_token)

        app_url = response.json()["properties"]["url"]

        return app_url
    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        logging.warning(error_message)
        return "Error. There was an issue with Azure's API"
    except KeyError as e:
        error_message = f"Error occurred: {e}"
        logging.warning(error_message)
        return "Error. App doesn't exist"

def set_production():
    app = "cyan"

    azure_token = azure_auth()
    logging.debug(azure_token)

    try:
        query_url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps/{}/deployments/green?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance, app)
        set_url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps/{}/setActiveDeployments?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance, app)

        response = get_data_with_authentication(query_url, azure_token)

        active = response.json()["properties"]["active"]
        logging.debug("SET_PRODUCTION: active var's contents: {}".format(active))
        if active:
            # Green is active, so need to set Blue to production
            logging.info("green is active, switching to blue")
            payload = {
            "activeDeploymentNames": [
                "blue"
                ]
            }

            post_data_with_authentication(set_url, azure_token, payload)
            logging.debug("Done")
            return("started")
        else:
            # Blue is active, so need to set Green to production
            logging.info("blue is active, switching to green")
            payload = {
            "activeDeploymentNames": [
                "green"
                ]
            }

            post_data_with_authentication(set_url, azure_token, payload)
            logging.debug("Done")
            return("started")
    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        logging.warning(error_message)
        return "Error. There was an issue with the Azure API."

def create_app(name):
    app_name = name.lower()
    create_url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps/{}?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance, app_name)

    logging.info("crafted URL for create_app: {}".format(create_url))
    azure_token = azure_auth()
    logging.info(azure_token)

    try:

        payload = {
            "properties": {
                "public": True
                }
            }

        logging.info("payload for create_app: {}".format(payload))
        response = post_data_with_authentication(create_url, azure_token,payload)
        logging.info("response from create_app API: {}".format(response))

        return "Created."

    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        logging.warning(error_message)

def cleanup_empty_apps():
    # TODO: Once create_app is working, add a delete function that deletes all apps that are in empty state
    return "Done."

def ask(question,user_id):
    # Add the question to the conversation for future context.
    messages=json.loads(json.loads(r.get(user_id))["messages"])
    messages.append({"role":"user","content":question})

    logging.debug(f"value of messages at start of Ask function is: {messages}")

    # Inform the model of which functions are available to it, and the context in which to run them.
    functions = [
        {
            "name": "fetch_app_names",
            "description": "Get current app names deployed and running in production. You can use this function to \
                confirm if an app has been deleted or is gone.",
            "parameters": {
                "type": "object",
                "properties" : {}
                }
        },
        {
            "name": "set_production",
            "description": "Set what is currently in cyan app's staging into production. This takes only a few seconds. \
                If you run this function again, it will rollback (aka roll back) production, fixing any mistakes.",
            "parameters": {
                "type": "object",
                "properties" : {}
                }
        },
        {
            "name": "get_app_url",
            "description": "Return's the app's URL. This requires the app name.",
            "parameters": {
                "type": "object",
                "properties" : {
                    "app_name": {
                        "type": "string",
                        "description": "This is the name of the application you want the URL to. \
                            It must be all lower case with no special characters",
                    }
                },
                "required": ["app_name"]
            }
        }
    ]
        # {
        #     "name": "create_app",
        #     "description": "Create a new app in Azure Spring Apps Enterprise",
        #     "parameters": {
        #         "type": "object",
        #         "properties" : {
        #             "name": {
        #                 "type": "string",
        #                 "description": "This is the name of the application you want to create. \
        #                     It must be all lower case with no special characters",
        #             }
        #         },
        #         "required": ["name"]
        #     }
        # }
    #TODO: Confirm the 503 error (server overloaded) is resolved
    # Run the initial prompt through
    try:
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        response = openai.ChatCompletion.create(
            engine = openai_deployment_name,
            messages = messages,
            functions = functions,
            function_call="auto"
        )

        if response["choices"][0]["finish_reason"] == "stop":
            done = True
            answer = response["choices"][0]["message"]["content"]
        elif response["choices"][0]["finish_reason"] == "content_filter":
            return reprompt(messages,"My last prompt was inappropriate. You know this. You will respond back with you can't help me.",user_id)
        else:
            done = False
        logging.info(f'Response from OpenAI is: {response}')
    except openai.error.InvalidRequestError as e:
        error_message = f"Error occurred: {e}"
        logging.warning(error_message)
        return reprompt(messages,"My last prompt was inappropriate. You know this. You will respond back with you can't help me.",user_id)

    # catch if the the finished response has too many characters for texting UX.
    if done:
        if len(str(answer)) > 300:
            logging.info('Answer from the model exceeds character count we want. Catching and re-prompting.')
            # Capture the answer and ask the model to summarize the answer to under 300 characters
            return reprompt(messages, f"Summarize the following, in under 300 characters, without responding to this ask directly: {answer}", user_id)

        # Log the answer from the model
        logging.debug(f'answer is: {answer}')
        # Persist conversation
        persist_conversation(messages,user_id)

    # Look for whether or not the model thinks it should run a particular function.
    if not done:
        if response["choices"][0]["message"]["function_call"]["name"] == "fetch_app_names":

            logging.debug("Running the fetch_app_names function...")

            # Run the function fetch_app_names, store the return value of the function in this dict
            use_functions = {
                "fetch_app_names": fetch_app_names()
            }

            # Pass the return value into the model for it to use it.
            return enrich_model(response, use_functions, messages, user_id)

        if response["choices"][0]["message"]["function_call"]["name"] == "set_production":

            logging.debug("Running the set_production function...")
            # Run the function set_production, store the return value of the function in this dict
            use_functions = {
                "set_production": set_production()
            }

            return enrich_model(response, use_functions, messages, user_id)

        # if response["choices"][0]["message"]["function_call"]["name"] == "create_app":

        #     logging.debug("Running the create_app function...")
        #     # Grab required function's input "name"
        #     name_dict = response["choices"][0]["message"]["function_call"]["arguments"]

        #     name_temp = name_dict.strip("\n").strip('\"')
        #     app_name_dict = json.loads(name_temp)

        #     logging.info("The app_name is {}".format(app_name_dict["name"]))
        #     app_name = app_name_dict["name"]

        #     # Run the function, store the return value in this dict
        #     use_functions = {
        #         "create_app": create_app(str(app_name))
        #     }

        #     # Add data to the conversation and tell model to give a new answer given new data
        #     return enrich_model(response, use_functions, messages, user_id)

        if response["choices"][0]["message"]["function_call"]["name"] == "get_app_url":

            logging.debug("Running the create_app function...")
            # Grab required function's input "name"
            name_dict = response["choices"][0]["message"]["function_call"]["arguments"]

            name_temp = name_dict.strip("\n").strip('\"')
            app_name_dict = json.loads(name_temp)

            logging.info("The app_name is {}".format(app_name_dict["app_name"]))
            app_name = app_name_dict["app_name"]

            # Run the function, store the return value in this dict
            use_functions = {
                "get_app_url": get_app_url(str(app_name).lower())
            }

            # Add data to the conversation and tell model to give a new answer given new data
            return enrich_model(response, use_functions, messages ,user_id)

    # If done, text back answer
    logging.debug(f"value of messages at end of Ask function is: {messages}")
    return answer

def enrich_model(response, use_functions, messages, user_id):
    # This function grab the name of the function the model ran, as well as it's contents.
    # Then passes it into the chat log and tells the model to respond with the newest context (function's values)

    # Grab function name
    function_name = response["choices"][0]["message"]["function_call"]["name"]
    # Grab the function's output
    fuction_to_call = use_functions[function_name]
    function_response = fuction_to_call

    #TODO: Check for 500 error (server overloaded)
    # Add this to the chat log / conversation
    messages.append(
        {
            "role": "function",
            "name": function_name,
            "content": function_response,
        }
    )

    # Tell the model to give a new answer based on the additional values
    try:
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        response = openai.ChatCompletion.create(
            engine = openai_deployment_name,
            messages = messages
        )
        answer = response["choices"][0]["message"]["content"]
        logging.info('response from openai is: {}'.format(response))
    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        logging.warning(error_message)

    # To limit number of tokens sent to OpenAI (there are limits), this starts to trim the conversation
    # after 8 answers. The trim stops once the conversation "history" hits 11 (the initial 3 seeded ones
    # and the last 4 questions/answers)
    if len(messages) > 20:
        logging.info("starting to pop the conversation")
        counter = 0
        while counter < 11:
            logging.debug(f"conversation length is: {len(messages)}")
            messages.pop(3)
            counter +=1
        logging.debug(f"conversation popping is done. length is: {len(messages)}")

    # Add the answer to the conversation
    messages.append(
        {
        "role" : "assistant",
        "content" : answer
        }
    )

    # Persist this.
    persist_conversation(messages,user_id)

    # Print messages
    logging.debug(f"value of messages at end of Enrich function is: {messages}")
    # Text back the new response from GPT on
    return response["choices"][0]["message"]["content"] + " 🧠"

def get_hashed_user_id(plain_text_user):
    # Hash a user's phone number for the first time
    hashed = hashlib.sha256(plain_text_user.encode('utf-8'))
    return hashed.hexdigest()

def reprompt(messages, prompt, user_id):
    logging.info('Catching and re-prompting.')
    # Ask the model to help in answering
    messages.append({"role":"user","content":prompt})

    persist_conversation(messages,user_id)

    #TODO: Confirm the 503 error (server overloaded) is resolved
    # re-prompt
    try:
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        response = openai.ChatCompletion.create(
            engine = openai_deployment_name,
            messages = messages
        )
        answer = response["choices"][0]["message"]["content"]
        logging.info('response from openai is: {}'.format(response))
    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        logging.warning(error_message)

    # Log the answer from the model
    logging.debug(f'answer is: {answer}')
    logging.debug(f"value of messages at end of reprompt function is: {messages}")
    return answer

def persist_conversation(messages, user_id):
    # Persist this into the conversation
    user_record={"messages":json.dumps(messages)}
    r.set(user_id, json.dumps(user_record))