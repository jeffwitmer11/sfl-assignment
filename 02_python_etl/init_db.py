import sqlite3
import pandas as pd


connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

input_data_path = "SRDataEngineerChallenge_DATASET.csv"
df = pd.read_csv(input_data_path)

df[['address','domain']] = df['email'].str.split('@',expand=True)

blocked_domains = df.sample(n=100)["domain"].drop_duplicates()
blocked_ips =  df.sample(n=100)["ip_address"].drop_duplicates()

blocked_domains.to_sql(name = "blocked_domains", con=connection, if_exists='append', index=False)
blocked_ips.to_sql(name = "blocked_ips", con=connection, if_exists='append', index=False)

connection.close()