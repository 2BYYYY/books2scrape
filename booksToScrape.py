import requests
import csv
import os
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv
import mysql.connector

def connect_to_mysql():
    # Load environment variables from .env file
    load_dotenv()
    
    # Correctly assign variables without commas
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")

    try:
    # Establish a connection to the MySQL database
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def save_to_sql(articles, prices):
    # Establish connection
    connected = connect_to_mysql()

    if connected:
        try:
            # Create a cursor object to execute SQL queries
            cursor = connected.cursor()

            # Prepare the insert query
            insert_query = "INSERT INTO bookstoscrape (title, price) VALUES (%s, %s)"
            data_to_insert = list(zip(articles, prices))

            # Execute the insert query for each book in the data list
            cursor.executemany(insert_query, data_to_insert)
            
            # Commit the transaction (important to save changes)
            connected.commit()
            print(f"{cursor.rowcount} rows inserted.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            # Close the cursor and connection
            cursor.close()
            connected.close()

def fetch_html(url):
    try:
        # Send a GET request to the URL and retrieve the server's response
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        print(f"Successfully fetched: {url}")
        # Return the HTML content of the page
        return response.content
    except requests.RequestException as e:
        # Print error message if the request fails (e.g., due to internet issues)
        print(f"Failed to fetch {url}: {e}")
        return None

def parse_html(content):
    # Create a BeautifulSoup object to parse the HTML
    return BeautifulSoup(content, "html.parser")

def extract_data(html_code):
    # Find all price elements by looking for <p> tags with class "price_color"
    prices = html_code.findAll("p", attrs={"class": "price_color"})
    # Find all <a> tags that have a "title" attribute to get the book titles
    articles = html_code.findAll("a", attrs={"title": True})
    
    # Extract the title attribute from each <a> tag to get the book titles
    article_titles = [article["title"] for article in articles]
    
    # Extract the text of each price element, slicing off the currency symbol
    price_values = [price.text[1:] for price in prices]  # Remove currency symbol

    return article_titles, price_values

def save_to_csv(filename, articles, prices):
    fieldnames = ["Title", "Price"]
    # Check if articles and prices lists are the same length to avoid mismatches
    if len(articles) == len(prices):
        # Check if the file already exists
        file_exists = os.path.isfile(filename)

        # Open the file in append mode to add data without overwriting
        with open(filename, mode='a', newline='') as file:
            csv_writer = csv.writer(file)

            # Write headers if the file is new
            if not file_exists:
                csv_writer.writerow(fieldnames)

            # Write each title and price as a row in the CSV
            for title, price in zip(articles, prices):
                csv_writer.writerow([title, price])
    else:
        # Print message if there is a mismatch in the number of titles and prices
        missing_data = len(articles) - len(prices)
        print(f"Missing {abs(missing_data)} data in {'article' if missing_data < 0 else 'price'}")

def get_page_range(parsed_html):
    # Find the list item with the class "current" to get the current page number
    pages = parsed_html.find("li", attrs={"class": "current"})
    pages_to_text = pages.text.strip()
    # Extract the first and last page numbers from the text
    first_page = int(pages_to_text.split()[1])
    last_page = int(pages_to_text.split()[3])
    return first_page, last_page

def main():
    # Base URL for the pages to scrape
    base_url = "https://books.toscrape.com/catalogue/page-{}.html"
    # URL of the first page to determine the range of pages
    first_page_url = "https://books.toscrape.com/index.html"
    
    # Fetch the HTML content of the first page
    html_content = fetch_html(first_page_url)
    if html_content:
        # Parse the HTML content of the first page
        parsed_html = parse_html(html_content)
        # Get the range of pages to scrape
        first_page, last_page = get_page_range(parsed_html)
        
        # Loop through each page in the range
        for page_number in range(first_page, last_page + 1):
            # Generate the URL for the current page number
            url_to_scrape = base_url.format(page_number)
            # Fetch the HTML content of the current page
            html_content = fetch_html(url_to_scrape)
            if html_content:
                # Parse the HTML content of the current page
                parsed_html = parse_html(html_content)
                # Extract book titles and prices
                article_titles, price_values = extract_data(parsed_html)
                # Save the extracted data to a CSV file
                save_to_csv("books_to_scrape.csv", article_titles, price_values)
                # Save the extracted data to a MySQL database
                save_to_sql(article_titles, price_values)

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
