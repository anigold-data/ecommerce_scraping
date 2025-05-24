import requests
from urllib.robotparser import RobotFileParser
import certifi  

def check_robots_txt(website_url, user_agent="PriceAnalysisBot"):
    """Check if scraping is allowed for a given website and user agent"""

    # Ensure website starts with https
    if not website_url.startswith("http"):
        website_url = "https://" + website_url
    if not website_url.endswith("/"):
        website_url += "/"
    
    robots_url = website_url + "robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)

    try:
        # Safer request with timeout and CA bundle
        response = requests.get(
            robots_url,
            headers={"User-Agent": user_agent},
            timeout=(5, 5),
            verify=certifi.where()  # Prevent SSL errors like Walmart's
        )
        response.raise_for_status()
        
        # Parse manually
        rp.parse(response.text.splitlines())

        can_fetch = rp.can_fetch(user_agent, website_url)
        crawl_delay = rp.crawl_delay(user_agent)

        return {
            "can_fetch": can_fetch,
            "crawl_delay": crawl_delay if crawl_delay is not None else "Not specified"
        }

    except Exception as e:
        return {
            "error": str(e),
            "can_fetch": False,
            "crawl_delay": "Error fetching robots.txt"
        }

# Example usage
retailers = [
    'www.amazon.co.uk',
    'www.walmart.com',
    'www.target.com',
    'www.newegg.com',
    'www.currys.co.uk',
    'www.sainsburys.co.uk',
    'www.asda.com',
    'https://www.tesco.com/'
]

for retailer in retailers:
    print(f"Checking {retailer}:")
    result = check_robots_txt(retailer)
    print(result)
    print("---")
