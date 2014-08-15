import xbmc
import xbmcvfs
import xbmcaddon
import xml.etree.ElementTree as ET

class Clipboard:
    clipBoardFileName = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8') + "clipboard.xml"
    
    @staticmethod
    def copyToClipboard(hrefToCopy, fileTypeToCopy):
        print "Copy to clipboard, check if clipboard file exists"
        
        root = None
        if xbmcvfs.exists(Clipboard.clipBoardFileName):
            print "Clipboard file exists, load clipboard file"
            clipBoardFile = xbmcvfs.File(Clipboard.clipBoardFileName)
            buffer = clipBoardFile.read()
            clipBoardFile.close()
            
            root = ET.fromstring(buffer.decode("utf-8"))
        else:
            print "Clipboard file doesn't exists, create new one"
            root = ET.fromstring("<clipboard></clipboard>")
            
        # check if the file to copy is already into the clipboard
        fileInClipboard = root.findall("./file[@href='" + hrefToCopy + "']")
        if len(fileInClipboard) > 0:
            print "File to copy already in clipboard"
            return
        
        # create file node element
        fileNode = ET.Element('file', {'href': hrefToCopy, 'type': fileTypeToCopy})
        root.append(fileNode)
        
        print "Write clipboard file"
        clipBoardFile = xbmcvfs.File(Clipboard.clipBoardFileName, 'w')
        buffer = ET.tostring(root, encoding="utf-8", method="xml").encode('utf-8')
        clipBoardFile.write(buffer)
        clipBoardFile.close()
        
        return len(root.findall("./file"))
    
    @staticmethod
    def getItems():
        items = []
        
        if xbmcvfs.exists(Clipboard.clipBoardFileName) == False:
            return items
        
        clipBoardFile = xbmcvfs.File(Clipboard.clipBoardFileName)
        buffer = clipBoardFile.read()
        clipBoardFile.close()
            
        root = ET.fromstring(buffer.decode("utf-8"))
        
        for file in root.findall('file'):
            items.append({'href': file.get('href'), 'type': file.get('type')})
            
        return items
       
    @staticmethod
    def clear():
        print "Clear the clipboard if file exists"
        
        if xbmcvfs.exists(Clipboard.clipBoardFileName):
            print "Clipboard file exists, delete it"
            xbmcvfs.delete(Clipboard.clipBoardFileName)