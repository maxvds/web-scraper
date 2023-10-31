"""
Module Name: main.py
Description: A web scraper customised for a business database site used to extract business data into csv format.
Author: Max van der Sluis
Date: 30-10-2023
Version: 1.1.0
"""
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re  # Regular expressions
import csv

count = 1  # Global count for number of entries


def getBusinessDetails(url, start, end):
    """Extract business details from the specified URL up to max_pages."""
    # Option to run the script in the background
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)  # Initialize the web driver
    wait = WebDriverWait(driver, 15)  # Wait up to 15 seconds for specified content to be loaded
    global count
    business_details = []  # List to store details
    # This loop repeats for every page in the current batch being processed
    for page_num in range(start, end + 1):
        page_url = f'{url}/page/{page_num}/?post_type=site&s=Temperature+metrology&filter=service&state&status'
        driver.get(page_url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.space-y-3')))
        # Get links of businesses on the current page
        business_links = driver.find_elements(By.CSS_SELECTOR, "*[id^='post-']")
        for link in business_links:  # Repeats for every link on the current page
            link.click()
            # Switch active window to opened link
            driver.switch_to.window(driver.window_handles[1])
            # Initialising data fields to default values
            business = name = phone = email = street = suburb = country = 'None'
            services = []
            products = []
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-sm.text-gray-900.flex.flex-col")))
            page_content = BeautifulSoup(driver.page_source, 'html.parser')
            # Extracting business name/title
            title_div = page_content.find('h1', class_='entry-title text-gray-900 text-4xl font-bold sm:text-5xl '
                                               'sm:tracking-tight break-words print:text-2xl')
            if title_div:
                business = title_div.text.strip()
            # Extracting services and products
            service_tds = page_content.findAll('td', class_='px-5 print:px-3 py-3 text-scope text-gray-900 align-top')
            id_num = 1
            if service_tds:
                for td in service_tds:
                    # Find the first <td> element (Service)
                    service_text = td.text.strip()
                    # Checking if service is relevant to the clients interest
                    if 'Temperature metrology' in service_text:
                        # Find the second <td> element (Corresponding product)
                        product_td = td.find_next_sibling('td')
                        product_text = product_td.get_text(strip=True) if product_td else ""
                        # Removing unnecessary repeating text
                        processed_service_text = service_text.replace('Temperature metrology - ', '')
                        # Adding service and corresponding product to their lists
                        services.append(f'{id_num} {processed_service_text}')
                        products.append(f'{id_num} {product_text}')
                        id_num += 1
            # Extracting Contact details
            contact_span = page_content.find('div', class_='text-sm text-gray-900 flex flex-col')
            if contact_span:  # Ensuring the element exists
                name = contact_span.span.text.strip()
                phone = contact_span.find('span', string=lambda x: x and x.startswith('P: ')).text.replace(
                    'P: ', '').strip() if contact_span.find('span', string=lambda x: x and x.startswith('P: ')) else None
            # Extracting location details
            address_div = page_content.find('p', string='Address')
            # Extracting obfuscated email
            email_span = page_content.find('span', class_='obfs-em')
            if email_span:
                prefix = email_span['data-name'][::-1]  # Reverse the data-name value
                domain = email_span['data-domain'][::-1]  # Reverse the data-domain value
                email = f"{prefix}@{domain}"
            if address_div:
                address_string = address_div.find_next_sibling('p').get_text(strip=True)
                # Using regex to split addresses into finer detail
                match = re.search(r'^(.*?[A-Za-z](?=(?:[A-Z][^A-Z]*){2}))(.*?,\s*[A-Z]+\s*\d+)\s*([A-Za-z\s]+)$',
                                  address_string)
                if match:
                    street = match.group(1).strip()
                    suburb = match.group(2).strip()
                    country = match.group(3).strip()
            # Appending individual details to the main list, using a list of lists
            business_details.append({
                'Business': business,
                'TM Services': services,
                'Products': products,
                'Name': name,
                'Phone': phone,
                'Email': email,
                'Street': street,
                'Suburb/City': suburb,
                'Country': country
            })
            print(f'Entry #{count}: {business}')
            count += 1
            driver.close()  # Close the current tab of the current business
            driver.switch_to.window(driver.window_handles[0])  # Switch back to original tab

    driver.quit()  # Close the browser after all requested data has been collected
    return business_details  # Return the finished list of business details


def save_to_csv(data, filename='output.csv'):
    """Save the provided data into a CSV file."""
    # Define the headers
    header = ['Business', 'TM Services', 'Products', 'Name', 'Phone', 'Email', 'Street', 'Suburb/City', 'Country']

    # Open the CSV file in write mode
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)

        # Write the header to the CSV file
        writer.writeheader()

        # Write each row to the CSV file
        for row in data:
            writer.writerow(row)


def get_output_name(input_name, num):
    """Ensure the filename ends with .csv and increments name for each batch of processing."""
    name = input_name + str(num+1)
    if not name.lower().endswith('.csv'):
        name += '.csv'
    return name


def processBatch(batch_start, batch_end, num):
    """Processing function to be called for each required batch. Calls upon all previously defined functions."""
    file_name = get_output_name(output_name, num)
    print(f"Processing pages {batch_start} to {batch_end}")
    details = getBusinessDetails('https://website.com', batch_start, batch_end)
    save_to_csv(details, file_name)
    print(f'Data saved to {file_name}')


if __name__ == "__main__":
    """Main function that takes user input and calculates batch processing"""
    max_pages_at_once = 25
    total_pages = int(input('How many pages to extract from: '))
    start_from_page = int(input('Which page would you like to start from? '))
    start_batch = (start_from_page - 1) // max_pages_at_once  # Calculate the starting batch number
    # Calculate the number of full batches
    num_full_batches = total_pages // max_pages_at_once
    # Calculate the number of pages in the last batch
    remainder = total_pages % max_pages_at_once
    output_name = input('Output .csv file name: ')
    # Processing data scraping in batches
    for i in range(start_batch, num_full_batches):
        start_page = i * max_pages_at_once + 1
        end_page = (i + 1) * max_pages_at_once
        processBatch(start_page, end_page, i)
    # If there's a remainder, process it
    if remainder and start_batch <= num_full_batches:
        start_page = num_full_batches * max_pages_at_once + 1
        end_page = start_page + remainder - 1
        processBatch(start_page, end_page, start_batch)

