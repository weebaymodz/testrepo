import requests
from bs4 import BeautifulSoup
import re
import xbmc
import xbmcaddon

class Scraper1337x:
    def __init__(self):
        self.base_url = 'https://1337x.to'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.addon = xbmcaddon.Addon()
        self.addon_name = self.addon.getAddonInfo('name')

    def _log(self, message, level=xbmc.LOGDEBUG):
        xbmc.log(f"{self.addon_name}: {message}", level=level)

    def search(self, query, category=None):
        self._log(f"Searching for: {query} in category: {category}", xbmc.LOGINFO)
        if category == 'tv':
            url = f"{self.base_url}/cat/TV/search/{query}/1/"
        elif category == 'movies':
            url = f"{self.base_url}/cat/Movies/search/{query}/1/"
        elif category == 'anime':
            url = f"{self.base_url}/cat/Anime/search/{query}/1/"
        else:
            url = f"{self.base_url}/search/{query}/1/"
        return self._parse_results(url)

    def get_category(self, category):
        self._log(f"Getting category: {category}", xbmc.LOGINFO)
        if category == 'tv':
            url = "https://1337x.to/cat/TV/1/"
        elif category == 'movies':
            url = "https://1337x.to/cat/Movies/1/"
        elif category == 'anime':
            url = "https://1337x.to/cat/Anime/1/"
        else:
            url = f"{self.base_url}/cat/{category}/1/"
        return self._parse_results(url)

    def _parse_results(self, url):
        try:
            self._log(f"Fetching URL: {url}", xbmc.LOGDEBUG)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raise exception for bad status codes
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for row in soup.select('tbody tr'):
                try:
                    name = row.select_one('td.name a:last-child')
                    if not name:
                        continue
                        
                    size = row.select_one('td.size').get_text(strip=True)
                    seeds = row.select_one('td.seeds').get_text(strip=True)
                    leeches = row.select_one('td.leeches').get_text(strip=True)
                    
                    results.append({
                        'title': name.get_text(strip=True),
                        'url': self.base_url + name['href'],
                        'size': size,
                        'seeds': seeds,
                        'leeches': leeches
                    })
                except Exception as e:
                    self._log(f"Error parsing row: {str(e)}", xbmc.LOGERROR)
                    continue
            
            self._log(f"Found {len(results)} results", xbmc.LOGINFO)
            return results
            
        except requests.exceptions.RequestException as e:
            self._log(f"Network error: {str(e)}", xbmc.LOGERROR)
            return []
        except Exception as e:
            self._log(f"Error parsing results: {str(e)}", xbmc.LOGERROR)
            return []

    def get_torrent_info(self, url):
        try:
            self._log(f"Getting torrent info from: {url}", xbmc.LOGDEBUG)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            info = {}
            info['title'] = soup.select_one('h1').get_text(strip=True)
            magnet_link = soup.select_one('a[href^="magnet:"]')
            
            if not magnet_link:
                self._log("No magnet link found", xbmc.LOGWARNING)
                return None
                
            info['magnet'] = magnet_link['href']
            
            # Parse additional information
            for row in soup.select('.torrent-detail-page ul.list li'):
                try:
                    label = row.select_one('strong')
                    if label:
                        key = label.get_text(strip=True).lower().replace(':', '')
                        value = row.get_text(strip=True).replace(label.get_text(strip=True), '').strip()
                        info[key] = value
                except Exception as e:
                    self._log(f"Error parsing info row: {str(e)}", xbmc.LOGWARNING)
                    continue
            
            self._log("Successfully retrieved torrent info", xbmc.LOGINFO)
            return info
            
        except requests.exceptions.RequestException as e:
            self._log(f"Network error getting torrent info: {str(e)}", xbmc.LOGERROR)
            return None
        except Exception as e:
            self._log(f"Error getting torrent info: {str(e)}", xbmc.LOGERROR)
            return None
