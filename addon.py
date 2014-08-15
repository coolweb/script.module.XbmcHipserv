import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import resources.lib.hipservData
import urllib2
import urllib
from urlparse import parse_qs
from cookielib import Cookie
from resources.lib.clipboard import Clipboard

REMOTE_DBG = False

# append pydev remote debugger
if REMOTE_DBG: 
    # Make pydev debugger works for auto reload.
    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
    try:
        import pysrc.pydevd as pydevd
    # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    except ImportError:
        sys.stderr.write("Error: " + 
            "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
        sys.exit(1)

userInfo = None

# allow to display french caracters

def doLogon(): 
    global userInfo
    try:
        authToken = hipservDataObj.getAuthLogin()
        
        if authToken.returnCode=='1':
            xbmc.executebuiltin("Notification('Xbmc hipserv','" + my_addon.getLocalizedString(32000).encode('utf-8') + "')")
            return None
        else:
            if authToken.returnCode=='2':
                xbmc.executebuiltin("Notification('Xbmc hipserv','" + my_addon.getLocalizedString(32001).encode('utf-8') + "')")
                return None
            else:
                userSession = hipservDataObj.logon()
                """Test if user has access to family folder"""
                userInfo = hipservDataObj.getUserInformation()
                
                if userInfo.isFamilyMember == 'false':
                    xbmc.executebuiltin("Notification('Xbmc hipserv','" + my_addon.getLocalizedString(32002).encode('utf-8') + "')")
                    return None
            
                return authToken
        
    except urllib2.URLError, e:
        if hasattr(e, 'reason'):
            xbmc.executebuiltin("Notification('Xbmc hipserv','" + xbmc.executebuiltin("Notification('Xbmc hipserv','" + my_addon.getLocalizedString(32002).encode('utf-8').format('test') + "')") + "')")
            
my_addon = xbmcaddon.Addon('script.module.XbmcHipserv')
handle = int(sys.argv[1])

#check setings are filled if no open settings
if my_addon.getSetting('nasName') == "" or my_addon.getSetting('userName') == "" or my_addon.getSetting('password') == "":
    my_addon.openSettings()
else:   
    hipservDataObj = resources.lib.hipservData.hipservServer(my_addon.getSetting('nasType'), my_addon.getSetting('nasName'), my_addon.getSetting('userName'), my_addon.getSetting('password'))
    
    """ Enter the plugin """
    if sys.argv[2] == '':
        Clipboard.clear()
        doLogon()
    
        """ Display root folders """
        for mediaSource in userInfo.mediaSources:
            params = {'nasUrl': hipservDataObj.nasUrl, 'authCookieName': hipservDataObj.authCookie.name, 'authCookieValue': hipservDataObj.authCookie.value, 'href': mediaSource.href}
            xbmcplugin.addDirectoryItem(handle, url=sys.argv[0] + "?" + urllib.urlencode(params), listitem=xbmcgui.ListItem(label=mediaSource.name), isFolder=True)
        
        xbmcplugin.endOfDirectory(handle, True)
        
    """ Navigate to an item
    pluginUrl?nasUrl=xxx&authCookieName=xxx&authCookieValue=xxx&href=xxx&copyHref=xxx&copyType=xxx
    """
    if sys.argv[2] != '':
        queryString = parse_qs(sys.argv[2][1:])
        copyHref = ""
        copyType = ""
        pasteTo = ""
        hipservDataObj.nasUrl = queryString.get('nasUrl')[0]
        authCookie = type('DummyCookie', (object,), { "name": "", "value": "" })
        authCookie.name = queryString.get('authCookieName')[0]
        authCookie.value = queryString.get('authCookieValue')[0]
        hipservDataObj.authCookie = authCookie
        href = queryString.get('href')[0]
        action = queryString.get('action')
        
        clipboardItems = Clipboard.getItems()
        totalItems = len(clipboardItems)
        
        if queryString.get('pasteTo') != None:
            pasteTo = queryString.get('pasteTo')[0]
        
        if queryString.get('copyHref') != None:
            copyHref = queryString.get('copyHref')[0]
            copyType = queryString.get('copyType')[0]
        
        if action != None:
            if action[0] == 'paste':
                try:
                    copiesHref = []
                    copiesType = []
                    
                    for clipboardItem in clipboardItems:
                        copiesHref.append(clipboardItem.get('href'))
                        copiesType.append(clipboardItem.get('type'))
                    
                    response = hipservDataObj.copy(pasteTo, copiesHref, copiesType)
                    xbmc.executebuiltin("Notification('Xbmc hipserv','" + my_addon.getLocalizedString(32004).encode('utf-8') + "')")
                    
                    if my_addon.getSetting('autorefresh') == True:
                        xbmc.executebuiltin('UpdateLibrary(video)')
                except urllib2.URLError, e:
                    if hasattr(e, 'reason'):
                        xbmc.executebuiltin("Notification('Xbmc hipserv','" + my_addon.getLocalizedString(32005).encode('utf-8').format(e.reason) + "')") 
                        
            if action[0] == 'copy':
                numFilesInCLipBoard = Clipboard.copyToClipboard(copyHref, copyType)
                
                if numFilesInCLipBoard == None:
                    xbmc.executebuiltin("Notification('Xbmc hipserv','" + my_addon.getLocalizedString(32006).encode('utf-8') + "')")
                else:
                    xbmc.executebuiltin("Notification('Xbmc hipserv','" + my_addon.getLocalizedString(32007).encode('utf-8').format(str(numFilesInCLipBoard)) + "')")
                    
            if action[0] == 'clearClipboard':
                Clipboard.clear()
                xbmc.executebuiltin("Notification('Xbmc hipserv','" + my_addon.getLocalizedString(32008).encode('utf-8') + "')") 
        
        files = hipservDataObj.getDirectoryContent(href)
        
        """ Display items """
        for file in files:
            commands = []
            params = {'nasUrl': hipservDataObj.nasUrl, 'authCookieName': hipservDataObj.authCookie.name, 'authCookieValue': hipservDataObj.authCookie.value, 'href': file.href}
            if queryString.get('copyHref') != None:
                params['copyHref'] = queryString.get('copyHref')[0]
                params['copyType'] = queryString.get('copyType')[0]
            
            listitem = None
            if isinstance(file, resources.lib.hipservData.Folder):
                listitem=xbmcgui.ListItem(label=file.name)
                
                paramsCommand = {'nasUrl': hipservDataObj.nasUrl, 'authCookieName': hipservDataObj.authCookie.name, 'authCookieValue': hipservDataObj.authCookie.value, 'href': href}
                
                totalItems = len(Clipboard.getItems())
                if totalItems > 0:
                    paramsCommand['action'] = 'paste'
                    paramsCommand['pasteTo'] = file.href       
                    commands.append((my_addon.getLocalizedString(32009).encode('utf-8').format(str(totalItems)), 'Container.Refresh(' + sys.argv[0] + '?' + urllib.urlencode(paramsCommand) + ')'))
            else:
                listitem=xbmcgui.ListItem(label=file.name, iconImage="DefaultVideo.png")
                
                paramsCopyCommand = {'nasUrl': hipservDataObj.nasUrl, 'authCookieName': hipservDataObj.authCookie.name, 'authCookieValue': hipservDataObj.authCookie.value, 'href': href, 'copyHref': file.href, 'copyType': 'video', 'action': 'copy'}
                commands.append((my_addon.getLocalizedString(32010).encode('utf-8'), 'Container.Refresh(' + sys.argv[0] + '?' + urllib.urlencode(paramsCopyCommand) + ')'))
            
            if totalItems > 0:
                # clear clipboard command  
                paramsCommand = {'nasUrl': hipservDataObj.nasUrl, 'authCookieName': hipservDataObj.authCookie.name, 'authCookieValue': hipservDataObj.authCookie.value, 'href': href}
                paramsCommand['action'] = 'clearClipboard'
                commands.append((my_addon.getLocalizedString(32011).encode('utf-8'), 'Container.Refresh(' + sys.argv[0] + '?' + urllib.urlencode(paramsCommand) + ')'))
                
            listitem.addContextMenuItems(commands, replaceItems = True)
                
            xbmcplugin.addDirectoryItem(handle, url=sys.argv[0] + "?" + urllib.urlencode(params), listitem=listitem, isFolder=isinstance(file, resources.lib.hipservData.Folder))
            
        xbmcplugin.endOfDirectory(handle)