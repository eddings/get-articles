# Python code to get all open articles from Springer and save them to a DB2 database

import requests
import json
import ibm_db_dbi as dbi

# Set your Springer API key
api_key = "YOUR_API_KEY"

# Set the base URL for the Springer API
base_url = "http://api.springer.com/openaccess"

# Set the parameters for the API request to retrieve all open articles
params = {
    "api_key": api_key,
    "q": "openaccess:true",
    "p": 0,
    "s": 100
}

# Initialize a list to hold the article metadata
metadata_list = []

# Make requests to the API until all pages of results have been retrieved
while True:
    # Construct the URL for the API request with the current page number
    url = f"{base_url}/json?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    
    # Make a GET request to the API URL and retrieve the JSON data
    response = requests.get(url)
    json_data = json.loads(response.text)
    
    # Add the article metadata to the list
    metadata_list += json_data["records"]
    
    # If there are no more pages of results, break out of the loop
    if len(json_data["records"]) < params["s"]:
        break
    
    # Increment the page number in the API parameters
    params["p"] += 1

# Set up the connection to the DB2 database
dsn = "DATABASE=<database_name>;HOSTNAME=<hostname>;PORT=<port_number>;PROTOCOL=TCPIP;UID=<username>;PWD=<password>;"
connection = dbi.connect(dsn)

# Create a cursor to execute SQL statements
cursor = connection.cursor()

# Create a table in the database to hold the article metadata
table_name = "springer_articles"
create_table_sql = f"""
    CREATE TABLE {table_name} (
        id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        doi VARCHAR(255),
        title VARCHAR(255),
        authors VARCHAR(255),
        publication_date DATE,
        abstract TEXT,
        fulltext_url VARCHAR(255)
    )
"""
cursor.execute(create_table_sql)

# Insert the article metadata into the database
for metadata in metadata_list:
    doi = metadata["doi"]
    title = metadata["title"]
    authors = ", ".join([f"{a['firstName']} {a['lastName']}" for a in metadata["creators"]])
    publication_date = metadata["publicationDate"].split("T")[0]
    abstract = metadata.get("abstract", "")
    fulltext_url = metadata["url"][0]["value"]
    
    insert_sql = f"""
        INSERT INTO {table_name} (doi, title, authors, publication_date, abstract, fulltext_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_sql, (doi, title, authors, publication_date, abstract, fulltext_url))

# Commit the changes to the database and close the connection
connection.commit()
connection.close()
