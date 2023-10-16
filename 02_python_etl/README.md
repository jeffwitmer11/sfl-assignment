
# Overview
This documentation outlines the design, deployment, and functionality of a mock ETL (Extract, Transform, Load) pipeline. The pipeline takes a list of users as input, transforms it into a structured table, and loads it into a MySQL database. The resulting table can be queried for downstream processes, such as sending targeted emails.

## Disclaimer:
This would be a great way to demonstrate skills with Spark, a platform I am quite familiar with and love using. I, however, opted not to set up a Docker container with Spark and instead called out areas where I could leverage spark if this ETL pipeline was deployed with larger data. 

# Requirements:
Docker (installed and running)
docker-compose

# Usage

1. Navigate to the `02_python_etl` directory
2. Execute the command: `docker-compose up` or `docker-compose up -d`
Two Docker containers will be initiated:
   - `db`: The container for a MySQL database
   - `app`: The container for running a Python script that executes the ETL pipeline.
> *Note: The Python container will wait for 20 seconds before starting to ensure the database is set up adequately.*
3. Upon completion of the Python container, records will be written to the MySQL database in the db container. These records constitute a subset of the original input data, along with additional constructed fields.

# Deployment

The deployment is orchestrated via a `docker-compose.yml` file, which builds a multi container application from two Docker images:

1. **MySQL Database Container:**
   - Initializes a database with three tables using the schema defined in `schema.sql`.
   >*Note: Environment variables required for the database are hardcoded in the `docker-compose.yml` file, which is not best practice but fine for now.*

2. **Python App Container:**
   - Copies the contents of the program folder on the host to the container.
   - Installs the necessary Python packages.
   - Once the python script is running, it populates two tables in the database with hypothetical data representing a list of domains and IP addresses that are blocked for email dispatch. This is done to demonstrate the merging of incoming data with existing data, a common ETL requirement.

# ETL Pipeline Process

## Extract

The supplied data is read into a Pandas DataFrame and immediately written in its entirety to the database. This approach facilitates SQL joins with other tables in subsequent stages. 
This strategy is similar to what would be done with Spark where it is important to extract the smallest possible dataset for performance. Techniques such as broadcast joins can be used to efficiently filter the data when using Spark.

## Transform

 >*Note: Pandas is used for data transformations due to its common usage and feature-rich capabilities. For larger datasets, distributed computing with PySpark is recommended over Pandas.*

  1. Join the data with a table of blocked IP addresses, filtering out records with blocked IPs.
  2. Split the email field into a username and domain.
  3. Join data with a table of blocked domains, filtering out records with blocked domains.
  4. Construct an email message using fields in the data.

## Load

The transformed data is loaded into a table in the MySQL database, ready for downstream consumption by other applications.

