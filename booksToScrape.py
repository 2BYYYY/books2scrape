import requests, csv, os
from bs4 import BeautifulSoup

def fetch_html(url):
    try:
        # Send a GET request to the URL and retrieve the server's response
        response = requests.get(url)
        print("The request was successfully received and processed by the server.")
        # Return the HTML content of the page
        return response.content
    except:
        # Print error message if the request fails (e.g., due to internet issues)
        print("Failed to connect. Check your internet connection")
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
        fileExists = os.path.isfile(filename)

        # Open the file in append mode to add data without overwriting
        with open(filename, mode='a', newline='') as file:
            csv_writer = csv.writer(file)

            # Write headers if the file is new
            if not fileExists:
                csv_writer.writerow(fieldnames)

            # Write each title and price as a row in the CSV
            for i in range(len(articles)):
                csv_writer.writerow([articles[i], prices[i]])
    else:
        # Print message if there is a mismatch in the number of titles and prices
        missingData = len(articles) - len(prices)
        print(f"missing {abs(missingData)} data in {'article' if missingData < 0 else 'price'}")

def main():
    # Loop through the first 50 pages of the site
    for pageNumber in range(1, 51):
        # Generate the URL for the current page number
        url_to_scrape = f"https://books.toscrape.com/catalogue/page-{pageNumber}.html"
        
        # Fetch the HTML content of the current page
        html_content = fetch_html(url_to_scrape)

        # If the HTML was successfully fetched, proceed with parsing and data extraction
        if html_content:
            parsed_html = parse_html(html_content)

            # Extract book titles and prices
            article_titles, price_values = extract_data(parsed_html)

            # Save the extracted data to a CSV file
            save_to_csv('scrapedB2S.csv', article_titles, price_values)

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
