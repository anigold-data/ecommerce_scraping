import logging
import requests
class ProxyManager:
    """Handles proxy rotation to avoid IP blocks."""
    
    def __init__(self, proxy_list=None):
        """Initialize with a list of proxies or use free proxy services."""
        self.logger = logging.getLogger('ProxyManager')
        
        # Default proxy list if none provided
        self.proxy_list = proxy_list or []
        self.current_index = 0
        
        # If no proxies provided, try to fetch free proxies
        if not self.proxy_list:
            self.refresh_proxies()
    
    def refresh_proxies(self):
        """Fetch fresh proxies from free proxy services."""
        try:
            # This is a simple example - in a real application, 
            # you would use a reliable proxy provider
            response = requests.get('https://www.proxy-list.download/api/v1/get?type=https')
            if response.status_code == 200:
                self.proxy_list = [f"https://{line}" for line in response.text.split('\r\n') if line]
                self.logger.info(f"Loaded {len(self.proxy_list)} proxies")
            else:
                self.logger.warning("Failed to fetch proxy list")
        except Exception as e:
            self.logger.error(f"Error refreshing proxies: {str(e)}")
    
    def get_proxy(self):
        """Get the next proxy from the rotation."""
        if not self.proxy_list:
            return None
            
        proxy = self.proxy_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxy_list)
        return proxy
    
    def get_session(self):
        """Create a requests session with the current proxy."""
        session = requests.Session()
        proxy = self.get_proxy()
        
        if proxy:
            session.proxies = {
                'http': proxy,
                'https': proxy
            }
            
        return session
