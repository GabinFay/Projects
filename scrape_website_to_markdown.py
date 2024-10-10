import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re

def crawl_subdomain(start_url, subdomain_to_keep, visited=None, to_visit=None):
    if visited is None:
        visited = set()
    if to_visit is None:
        to_visit = set([start_url])

    # Parse the subdomain to keep
    parsed_subdomain = urlparse(subdomain_to_keep)
    base_domain = f"{parsed_subdomain.scheme}://{parsed_subdomain.netloc}"
    subdomain = parsed_subdomain.netloc + parsed_subdomain.path.rstrip('/')

    while to_visit:
        current_url = to_visit.pop()
        
        # Remove fragment from URL
        current_url = current_url.split('#')[0]

        # Check if we've already visited this URL
        if current_url in visited:
            continue

        # Check if the current URL is under the subdomain we want to keep
        if not current_url.startswith(subdomain_to_keep):
            continue

        # Add the current URL to the visited set
        visited.add(current_url)
        print(f"Crawling: {current_url}")

        try:
            # Make a GET request to the URL
            response = requests.get(current_url)
            response.raise_for_status()

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all links in the page
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_domain, href)
                parsed_full_url = urlparse(full_url)

                # Remove fragment from URL
                full_url = full_url.split('#')[0]

                # Check if the URL belongs to the subdomain we want to keep
                if (full_url.startswith(subdomain_to_keep) and
                    'email-protection' not in full_url and
                    full_url not in visited and
                    full_url not in to_visit):
                    print(f"Found new URL: {full_url}")
                    to_visit.add(full_url)

        except requests.RequestException as e:
            print(f"Error crawling {current_url}: {e}")

    return visited

def save_urls_to_file(urls, filename):
    with open(filename, 'w') as f:
        for url in sorted(urls):
            f.write(f"{url}\n")
    print(f"URLs saved to {filename}")

def sanitize_filename(url):
    # Remove scheme and domain
    path = urlparse(url).path
    # Replace non-alphanumeric characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9]', '_', path)
    # Remove leading/trailing underscores and return
    return sanitized.strip('_') or 'index'

def scrape_and_save_content(url, output_folder):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title and content
        title = soup.title.string if soup.title else "No Title"
        content = soup.get_text(separator='\n', strip=True)
        
        # Create markdown content
        markdown_content = f"# {title}\n\nSource: {url}\n\n{content}"
        
        # Create filename and path
        filename = sanitize_filename(url) + '.md'
        filepath = os.path.join(output_folder, filename)
        
        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Save the content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Saved content from {url} to {filepath}")
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")

# Example usage
if __name__ == "__main__":
    start_url = "https://academy.avax.network/course/interchain-token-transfer/"
    subdomain_to_keep = "https://academy.avax.network/course/interchain-token-transfer/"
    all_urls = crawl_subdomain(start_url, subdomain_to_keep)
    
    print("All URLs found:")
    for url in all_urls:
        print(url)
    
    # Save URLs to a text file
    save_urls_to_file(all_urls, "crawled_urls.txt")
    
    # Scrape and save content for each URL
    output_folder = "scraped_content"
    for url in all_urls:
        scrape_and_save_content(url, output_folder)
