# Overview 
A chat bot web application with a simple API to retrieve the chat history

## Disclaimer
In its current form, the deployment of this ML model is not complete as it lacks a suitable environment (AWS, Azure, GCP, docker, kubernetes, etc). I developed this code using and tested this code using a virtual environment (venv). 

# Requirements
Following on from disclaimer above, the environment requires
* Python 3
* GPT4ALL 
* Flask 
* Web browser

# Usage 
## Starting the application
To run the application on a local server, navigate to the `03_ml_api` directory and run the python file `app.py`.
Once the script is running, an IP address will be displayed in the terminal (such as http://127.0.0.1:5000). 
Open a web browser and enter the IP address as a URL.

## Interacting with the chat bot (via the web app)
Type a prompt to the chat bot in the box and click “GO”
The chat both will respond in a few seconds
To start a new session, select the “New Session” button at the top of the chat window. 

## Retrieving chat history (via the API)
An API is provided to allow access to the chat history. 

#### 1. Return the entire chat history from all sessions
> Navigate to the `…/api/sessions/all` URL.<br>
For example http://127.0.0.1:5000/api/sessions/all

#### 2. Retrieve the chat history for a single session
> Navigate to the `…/api/sessions` page and supply an integer session id to the `id` parameter. <br>
For example: http://127.0.0.1:5000/api/sessions?id=1


# Deployment
The model is deployed using a Flask web app and API. <br>
>*NOTE: Prior to the app starting, a SQLite database must be provisioned. This can be done by running the `init_db.py` script. I have, however, have already provisioned a database with some sample data and uploaded it to this repository.*

1. Upon the application start up, the model is either located or downloaded to the server's file system. I am relying on `GPT4All` to initialize the model in this way. <br>
2. The Flask app is then started. 
3. The app sets up a home page 
4. Clicking the “GO” button submits a POST method and the app retrieves the user's input from the form. 
5. It then queries the database for the chat history for this chat session. Using this chat history, and the newly supplied user input, it prompts the model for a response. 
6. The prompt and response are saved to the  database and the chat history (including this new prompt/response) is displayed. 
7. Clicking the new session button increments the session ID by one and adds a new line to the table in the database with this new session ID. The main page is then refreshed. The current session is determined to be this new session.

# Future Improvements
* Complete deployment in a production environment 
* Expand the functionality of the API
* Provide methods to tune the model's parameters
* Incorporate more featureful model ecosystem (Hugging Face and LangChain)
* Add unit tests
* Add error handling
* Organize as Python package 

# Model
The model is a 3 billion parameter Large Language Model (which is a relatively small model) called  [Orca](https://www.microsoft.com/en-us/research/publication/orca-progressive-learning-from-complex-explanation-traces-of-gpt-4/). 

This model was built using Meta's LLaMa and fine-tuned using [OpenAI's GPT4](https://openai.com/gpt-4). 
In this app, I am using [Orca mini](https://huggingface.co/TheBloke/orca_mini_3B-GGML), one of the smallest versions of Orca.
