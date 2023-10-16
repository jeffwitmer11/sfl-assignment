"""
TODO: Name
Author: Jeff Witmer
TODO: Last Updated:

About
-----
TODO

Design
------
TODO
"""

import pandas as pd
import sqlalchemy as db
from string import Template


def get_db_connection():

    # Connecet to a mysql database that is in another docker image. 
    # The database configueation (including user and password) is hard coded in 
    # the docker-compose.yml. This is, of course, not best practice but it is 
    # fine for now.

    # specify database configurations
    config = {
        'host': 'db',
        'port': 3306,
        'user': 'user',
        'password': 'password',
        'database': 'mysql'
    }
    db_user = config.get('user')
    db_pwd = config.get('password')
    db_host = config.get('host')
    db_port = config.get('port')
    db_name = config.get('database')

    # Using SQLAchemy to connect to the mysql database
    # specify connection string
    connection_str = f'mysql+pymysql://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}'
    engine = db.create_engine(connection_str)
    conn = engine.connect()

    return conn


def init_db():
    input_data_path = "SRDataEngineerChallenge_DATASET.csv"
    df = pd.read_csv(input_data_path)

    conn = get_db_connection()

    df.to_sql(name="users", con=conn, if_exists='replace', index=False)

    df[['address', 'domain']] = df['email'].str.split('@', expand=True)

    (df
        .sample(n=100)["domain"]
        .drop_duplicates()
        .to_sql(name="blocked_domains", con=conn,
                           if_exists='append', index=False)
    )

    (df
        .sample(n=100)["ip_address"] 
        .drop_duplicates()
        .to_sql(name="blocked_ips", con=conn,
                       if_exists='append', index=False)
    )

    conn.close()


def create_emails():

    conn = get_db_connection()

    # Extract
    input_data_path = "SRDataEngineerChallenge_DATASET.csv"
    df = pd.read_csv(input_data_path)
    df.to_sql(name="users", con=conn, if_exists='replace', index=False)

    query = '''
            SELECT t1.*
            FROM users t1
            LEFT JOIN blocked_ips t2 on t1.ip_address = t2.ip_address
            WHERE t2.ip_address IS NULL
            '''
    df = pd.read_sql_query(query, conn)

    # Transform

    df[['user_name', 'domain']] = df['email'].str.split('@', expand=True)

    blocked_domains = pd.read_sql_query(
        "SELECT domain FROM blocked_domains", conn)

    df_blocked_domains_joined = df.merge(
        blocked_domains, how='left', indicator=True)
    df_valid_domains = df_blocked_domains_joined[~(
        df_blocked_domains_joined._merge == 'both')].drop('_merge', axis=1)

    df_vaild_emails = df_valid_domains \
        .dropna(subset=['email']) \
        .drop_duplicates(subset=['first_name', 'last_name', 'user_name'])

    email_template = Template(
        'Dear $first_name, Your gender of \"$gender\" has been associated with the user name: $user_name.')

    df_vaild_emails['email_message'] = df_vaild_emails \
        .apply(lambda x: email_template.substitute(
            first_name=x['first_name'],
            gender=x['gender'],
            user_name=x['user_name']), axis=1)

    # Load
    df_vaild_emails.to_sql(name="email_messages",
                            con=conn, if_exists='replace', index=False)

    df_test = pd.read_sql_query("SELECT * FROM email_messages", conn)
    print(df_test)
    conn.close()


if __name__ == "__main__":
    init_db()
    create_emails()
