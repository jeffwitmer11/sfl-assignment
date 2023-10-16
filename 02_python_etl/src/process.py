import pandas as pd
import sqlalchemy as db
from string import Template


def get_db_connection():
    """
    Connect to a mysql database that is in another docker image. 
    # The database configuration (including user and password) is hard coded in 
    # the docker-compose.yml. This is, of course, not best practice but it is 
    # fine for now.
    """
    # Specify database configurations
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

    # Using sqlalchemy to connect to the mysql database
    # specify connection string
    connection_str = f'mysql+pymysql://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}'
    engine = db.create_engine(connection_str)
    conn = engine.connect()

    return conn


def init_db():
    """
    Set up some tables and schema in the database. Populate two tables in the 
    database with hypothetical data representing a list of domains and IP 
    addresses that are blocked for email dispatch. This is done to demonstrate 
    the merging of incoming data with existing data, a common ETL requirement.
    """
    input_data_path = "SRDataEngineerChallenge_DATASET.csv"
    df = pd.read_csv(input_data_path)

    conn = get_db_connection()
    df.to_sql(name="users", con=conn, if_exists='replace', index=False)
    df[['address', 'domain']] = df['email'].str.split('@', expand=True)

   # Note that the sampling of rows is not reproducible. 
   # I am intentionally not setting a seed or enforcing reproducibility
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
    """
    A pipeline that reads in the supplied data and creates a new table that 
    represents users that should be emailed, along with the message to email 
    them. 
    """

    conn = get_db_connection()

    # Extract
    input_data_path = "SRDataEngineerChallenge_DATASET.csv"
    df = pd.read_csv(input_data_path)
    df.to_sql(name="users", con=conn, if_exists='replace', index=False)
    # SPARK: Partition the data appropriately
    # SPARK: Cache/persist 

    # Filtering IP addresses, using SQL 
    # SPARK: Use a broadcast join
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

    # Filtering Domains, using Pandas
    # SPARK: Use a broadcast join
    df_blocked_domains_joined = df.merge(
        blocked_domains, how='left', indicator=True)
    df_valid_domains = df_blocked_domains_joined[~(
        df_blocked_domains_joined._merge == 'both')].drop('_merge', axis=1)

    # Clean the data
    # Wow, the data we got is super clean already. Usually there would be many 
    # steps here to get the data cleaned up. But I am only including two simple 
    # steps for now
    df_vaild_emails = df_valid_domains \
        .dropna(subset=['email']) \
        .drop_duplicates(subset=['first_name', 'last_name', 'user_name'])

    # Feature Construction
    email_template = Template(
        'Dear $first_name, Your gender of \"$gender\" has been associated with the user name: $user_name.')

    df_vaild_emails['email_message'] = df_vaild_emails \
        .apply(lambda x: email_template.substitute(
            first_name=x['first_name'],
            gender=x['gender'],
            user_name=x['user_name']), axis=1)

    # Load
    # SPARK: Write to distributed table (such as a Delta table)
    df_vaild_emails.to_sql(name="email_messages",
                            con=conn, if_exists='replace', index=False)

  # Check to make sure the data got written correctly
    df_read_in = pd.read_sql_query("SELECT * FROM email_messages", conn)
    print(df_read_in.head())
    conn.close()


if __name__ == "__main__":
    init_db()
    create_emails()
