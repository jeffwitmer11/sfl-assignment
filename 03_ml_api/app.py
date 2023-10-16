import sqlite3
from gpt4all import GPT4All
from flask import (
    Flask, 
    render_template, 
    request, 
    url_for, 
    flash, 
    redirect, 
    jsonify)

# ----------------------------- Helpers ----------------------------------------
def get_db_connection():
    """ 
    Connect to the database. 
    """
    conn = sqlite3.connect('database.db')
    return conn


def get_db_row():
    """ 
    Return a row factory for database. 
    """
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    return conn


def get_db_dict():
    """ 
    Return a dictionary factory for database. 
    This is used by the API to help retun results as JSON. 
    """
    conn = get_db_connection()
    conn.row_factory = dict_factory
    return conn


def get_current_session_id():
    """ 
    Return a the current session ID as an integer. 
    When new sessions are created, the current session ID is incrementeed by 1. 
    So the current session is simply the max session ID.
    """
    conn = get_db_connection()
    session = conn.execute(
        "SELECT MAX(session_id) FROM chat_log").fetchall()[0][0]
    conn.close()
    return (session)


def get_current_session_chat_log():
    """ 
    Return a row factory for all prompts and responses in the current session.
    """
    session = get_current_session_id()
    conn = get_db_row()
    query = f'''
        SELECT prompt, response FROM chat_log 
        WHERE session_id = {session} 
        AND prompt IS NOT NULL 
        AND response IS NOT NULL
        '''
    chat_log = conn.execute(query).fetchall()
    conn.close()
    return(chat_log)


def dict_factory(cursor, row):
    """ 
    A dictionary factory
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def init_model():
    """
    Initalize th.e LLM
    This process relies on GPT4ALL to determine if the model is already present 
    at the path. GPT4ALL will download it if is not already there. 
    """
    model_name = 'orca-mini-3b.ggmlv3.q4_0.bin'
    model_path = 'model/'
    model = GPT4All(model_name, model_path)
    return model


def get_response(input_text):
    """
    For a given prompt, get the model's reponse. 
    """

    # We need the current chat log inorder to build the chat session for the 
    # model. In this way, the model's responses take into consideration 
    # previous prompts/responses from the session.
    chat_log = get_current_session_chat_log()

    with model.chat_session():
        # Build out the chat session before we give the model the new prompt
        for r in chat_log:
            model.current_chat_session.append(
                {'role': 'user', 'content': r['prompt']})
            model.current_chat_session.append(
                {'role': 'assistant', 'content': r['response']})

        tokens = list(model.generate(
            prompt=input_text, top_k=1, streaming=True))
        model.current_chat_session.append(
            {'role': 'assistant', 'content': ''.join(tokens)})
        response = model.current_chat_session[-1]['content']
    return (response)


# ------------------------------ Web App ----------------------------------------
app = Flask(__name__)


@app.route('/', methods=('GET', 'POST'))
def index():
    """
    The main page for the chat bot app
    """
    session = get_current_session_id()

    # User has sumbitted a prompt
    if request.method == 'POST':
        input_text = request.form['input']
        if not input_text:
            flash('Enter a prompt.')
        else:
            # Query the model for a response
            response = get_response(input_text)

            # Update the chat (prompt and reponse) in the database so that we 
            # can retain all the chats for this session 
            conn = get_db_row()
            conn.execute("INSERT INTO chat_log  (prompt, response, session_id) VALUES (?, ?, ?)",
                         (input_text, response, session))
            conn.commit()
            conn.close()

        return redirect(url_for('index'))

    # The page has been simply loaded
    else:
        # Get the current session's chat log and display it
        chat_log = get_current_session_chat_log()

        return render_template('index.html', chat_log=chat_log)


@app.route('/new', methods=('GET', 'POST'))
def new_session():
    """
    Initialize a new chat session. 
    This works by simply adding a row to the chat log database with a session ID 
    incremented from the current session ID
    """
    session = get_current_session_id()
    session += 1
    conn = get_db_row()
    conn.execute("INSERT INTO chat_log (session_id) VALUES (?)",
                 (session,)
                 )
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


# -------------------------------- API -----------------------------------------
@app.route('/api/sessions/all', methods=['GET'])
def api_all():
    """
    Return the entire chat history (all sessions)
    """
    conn = sqlite3.connect('database.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    sessions = cur.execute('SELECT * FROM chat_log;').fetchall()

    return jsonify(sessions)


@app.route('/api/sessions', methods=['GET'])
def api_id():
    """
    Return the  chat history for a given session
    """
    # Check is a session ID was provided in the URL
    if 'id' in request.args:
        id = int(request.args['id'])
    else:
        return "Error: Session ID is required."

    conn = get_db_dict()
    cur = conn.cursor()
    results = cur.execute(
        f'SELECT * FROM chat_log WHERE session_id = {id}').fetchall()
    conn.close()

    return jsonify(results)


if __name__ == '__main__':
    model = init_model()
    app.run()
