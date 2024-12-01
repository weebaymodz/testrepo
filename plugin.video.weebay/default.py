# -*- coding: utf-8 -*-
import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
from resources.lib.scraper import Scraper1337x
import urllib.parse

_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_base_url = sys.argv[0]
_addon_name = _addon.getAddonInfo('name')

def _log(message, level=xbmc.LOGDEBUG):
    xbmc.log(f"{_addon_name}: {message}", level=level)

def get_url(**kwargs):
    return f"{_base_url}?{urllib.parse.urlencode(kwargs)}"

def list_category_menu(category):
    _log(f"Displaying menu for category: {category}", xbmc.LOGINFO)
    try:
        # Add search option
        search_item = xbmcgui.ListItem(label="Search")
        search_url = get_url(action='search', category=category)
        xbmcplugin.addDirectoryItem(_handle, search_url, search_item, True)
        
        # Add browse option
        browse_item = xbmcgui.ListItem(label="Browse All")
        browse_url = get_url(action='listing', category=category)
        xbmcplugin.addDirectoryItem(_handle, browse_url, browse_item, True)
        
        xbmcplugin.endOfDirectory(_handle)
    except Exception as e:
        _log(f"Error displaying category menu: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(_addon_name, "Error displaying menu", xbmcgui.NOTIFICATION_ERROR)

def search(category=None):
    _log(f"Starting search for category: {category}", xbmc.LOGINFO)
    keyboard = xbmc.Keyboard('', f'Search {category.title() if category else "All"}')
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        query = keyboard.getText()
        if query:
            _log(f"Searching for: {query} in category: {category}", xbmc.LOGINFO)
            try:
                scraper = Scraper1337x()
                results = scraper.search(query, category)
                if results:
                    list_results(results)
                else:
                    _log("No results found", xbmc.LOGINFO)
                    xbmcgui.Dialog().notification(_addon_name, "No results found", xbmcgui.NOTIFICATION_INFO)
            except Exception as e:
                _log(f"Error during search: {str(e)}", xbmc.LOGERROR)
                xbmcgui.Dialog().notification(_addon_name, "Error during search", xbmcgui.NOTIFICATION_ERROR)

def list_categories():
    _log("Displaying categories", xbmc.LOGINFO)
    categories = [
        ('Movies', 'movies'),
        ('TV Shows', 'tv'),
        ('Anime', 'anime'),
        ('Search All', 'search')
    ]
    
    try:
        for title, category in categories:
            list_item = xbmcgui.ListItem(label=title)
            if category == 'search':
                url = get_url(action='search')
            else:
                url = get_url(action='category_menu', category=category)
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        
        xbmcplugin.endOfDirectory(_handle)
    except Exception as e:
        _log(f"Error displaying categories: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(_addon_name, "Error displaying categories", xbmcgui.NOTIFICATION_ERROR)

def list_results(results):
    _log(f"Displaying {len(results)} results", xbmc.LOGINFO)
    try:
        for item in results:
            list_item = xbmcgui.ListItem(label=item['title'])
            
            # Add video information
            video_info = {
                'title': item['title'],
                'size': item['size'],
                'genre': item.get('category', ''),
                'mediatype': 'movie'  # or 'tvshow' based on category
            }
            
            list_item.setInfo('video', video_info)
            
            # Add context menu for direct play
            context_menu = [
                ('Play', 'PlayMedia(%s)' % get_url(action='play', url=item['url'])),
                ('Information', 'Action(Info)')
            ]
            list_item.addContextMenuItems(context_menu)
            
            # Make the item playable
            url = get_url(action='play', url=item['url'])
            is_folder = False
            
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        
        xbmcplugin.setContent(_handle, 'movies')
        xbmcplugin.endOfDirectory(_handle)
    except Exception as e:
        _log(f"Error displaying results: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(_addon_name, "Error displaying results", xbmcgui.NOTIFICATION_ERROR)

def play_video(url):
    _log(f"Getting video information for: {url}", xbmc.LOGINFO)
    try:
        # Get torrent info
        scraper = Scraper1337x()
        info = scraper.get_torrent_info(url)
        
        _log(f"Torrent info retrieved: {info}", xbmc.LOGDEBUG)
        
        if not info:
            _log("No torrent information found", xbmc.LOGERROR)
            xbmcgui.Dialog().notification(_addon_name, "No torrent information found", xbmcgui.NOTIFICATION_ERROR)
            return
            
        if 'magnet' not in info:
            _log("No magnet link found in torrent info", xbmc.LOGERROR)
            xbmcgui.Dialog().notification(_addon_name, "No magnet link found", xbmcgui.NOTIFICATION_ERROR)
            return

        # Check if Elementum or Torrest is installed
        elementum_installed = xbmc.getCondVisibility('System.HasAddon(plugin.video.elementum)')
        torrest_installed = xbmc.getCondVisibility('System.HasAddon(plugin.video.torrest)')
        
        if not (elementum_installed or torrest_installed):
            _log("No torrent streaming addon found. Please install Elementum or Torrest.", xbmc.LOGERROR)
            xbmcgui.Dialog().ok(_addon_name, 
                               "Torrent Streaming Add-on Required",
                               "Please install either Elementum or Torrest add-on to play torrents.",
                               "You can find them in the Kodi add-on repository.")
            return

        # Create list of available players
        players = []
        if elementum_installed:
            players.append(('Elementum', 'plugin://plugin.video.elementum/play?uri='))
        if torrest_installed:
            players.append(('Torrest', 'plugin://plugin.video.torrest/play_magnet?magnet='))

        # If only one player is available, use it directly
        if len(players) == 1:
            player_name, player_url = players[0]
        else:
            # Let user choose the player
            choice = xbmcgui.Dialog().select('Choose Player', [p[0] for p in players])
            if choice < 0:
                return
            player_name, player_url = players[choice]

        _log(f"Using player: {player_name}", xbmc.LOGINFO)
        
        # Create the full playback URL
        magnet_url = info['magnet']
        _log(f"Magnet URL: {magnet_url}", xbmc.LOGDEBUG)
        
        # URL encode the magnet link
        encoded_magnet = urllib.parse.quote(magnet_url)
        full_url = f"{player_url}{encoded_magnet}"
        
        _log(f"Full playback URL: {full_url}", xbmc.LOGDEBUG)

        # Create ListItem with video information
        play_item = xbmcgui.ListItem(path=full_url)
        play_item.setInfo('video', {
            'title': info['title'],
            'mediatype': 'movie'
        })

        # Start playback
        _log("Starting playback...", xbmc.LOGINFO)
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
        
    except Exception as e:
        _log(f"Error in play_video: {str(e)}", xbmc.LOGERROR)
        import traceback
        _log(f"Traceback: {traceback.format_exc()}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(_addon_name, "Error playing video", xbmcgui.NOTIFICATION_ERROR)

def display_torrent_info(info):
    _log("Displaying torrent information", xbmc.LOGINFO)
    try:
        if not info:
            xbmcgui.Dialog().notification(_addon_name, "Error getting torrent information", xbmcgui.NOTIFICATION_ERROR)
            return

        # Create a formatted message with the torrent information
        message = f"Title: {info['title']}\n"
        if 'size' in info:
            message += f"Size: {info['size']}\n"
        if 'seeds' in info:
            message += f"Seeds: {info['seeds']}\n"
        if 'leeches' in info:
            message += f"Leeches: {info['leeches']}\n"

        # Show the information in a dialog
        xbmcgui.Dialog().textviewer(_addon_name, message)

        # Ask if user wants to copy magnet link
        if 'magnet' in info:
            if xbmcgui.Dialog().yesno(_addon_name, "Copy magnet link to clipboard?"):
                xbmc.Keyboard(info['magnet'], 'Magnet Link (Copy)').doModal()
    except Exception as e:
        _log(f"Error displaying torrent info: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(_addon_name, "Error displaying torrent information", xbmcgui.NOTIFICATION_ERROR)

def router(paramstring):
    _log(f"Router called with params: {paramstring}", xbmc.LOGDEBUG)
    params = dict(urllib.parse.parse_qsl(paramstring[1:]))
    
    try:
        if params:
            if params['action'] == 'category_menu':
                list_category_menu(params['category'])
            elif params['action'] == 'listing':
                scraper = Scraper1337x()
                results = scraper.get_category(params['category'])
                list_results(results)
            elif params['action'] == 'search':
                search(params.get('category'))
            elif params['action'] == 'play':
                play_video(params['url'])
            elif params['action'] == 'get_info':
                scraper = Scraper1337x()
                info = scraper.get_torrent_info(params['url'])
                display_torrent_info(info)
        else:
            list_categories()
    except Exception as e:
        _log(f"Router error: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(_addon_name, "An error occurred", xbmcgui.NOTIFICATION_ERROR)

if __name__ == '__main__':
    _log("Addon started", xbmc.LOGINFO)
    router(sys.argv[2])
