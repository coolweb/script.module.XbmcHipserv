import urllib2
import cookielib
import xml.etree.ElementTree as ET

class AuthLoginResponse:
	def __init__(self, returnCode, authCode, nasUrl):
		self.returnCode=returnCode
		self.authCode=authCode
		self.nasUrl=nasUrl
		
class UserSession:
	def __init__(self, supportURL, userURI, serverConfigURI, href, locale):
		self.supportURL = supportURL
		self.userURI = userURI
		self.serverConfigURI = serverConfigURI
		self.href = href
		self.locale = locale
		
class UserInformation:
	def __init__(self, isFamilyMember, mediaSources):
		self.isFamilyMember = isFamilyMember
		self.mediaSources = mediaSources
		
class MediaSource:
	def __init__(self, id, name, href):
		self.id = id
		self.name = name
		self.href = href
		
class Folder:
	def __init__(self, name, href):
		self.name = name
		self.href = href
		
class File:
	def __init__(self, name, href):
		self.name = name
		self.href = href
		
class VideoFile(File):
	def __init__(self, name, href):
		File.__init__(self, name, href)

class hipservServer:
	
	def __init__(self, nasType, nasName, userName, password):
		"""request a login code
		
		Arguments:
		nasType: the nas type, 0: Medion
		nasName: the name of the user nas
		userName: the user name to logon
		password: the password of the user
		"""
		
		self.nasType = nasType
		self.nasName = nasName
		self.userName = userName
		self.password = password
		
		"""
		private static const AXENTRA_CS:String = "https://www.myhipserv.com/rest/1.0/sessions/hipserv";
      
      private static const LACIE_CS:String = "https://www.homelacie.com/rest/1.0/sessions/hipserv";
      
      private static const NETGEAR_CS:String = "https://www.mystora.com/rest/1.0/sessions/hipserv";
      
      private static const ORANGE_CS:String = "https://www.homelibrary.fr/rest/1.0/sessions/hipserv";
      
      private static const RAIDSONIC_CS:String = "https://www.myicybox.com/rest/1.0/sessions/hipserv";
      
      private static const ROXIO_CS:String = "https://www.roxiostreamer.com/rest/1.0/sessions/hipserv";
      
      private static const SEAGATE_CS:String = "https://www.seagateshare.com/rest/1.0/sessions/hipserv";
      
      private static const VERBATIM_CS:String = "https://www.myverbatim.com/rest/1.0/sessions/hipserv";
      
      private static const MEDION_CS:String = "https://www.lifecloudmedion.com/rest/1.0/sessions/hipserv";
      """
		
		self.address = 'https://www.lifecloudmedion.com'
		self.nasUrl=''
		self.authToken=''
		self.userSession = None
		self.authCookie = None
	
	def _getXML(self, url, data = None):
		cookies = cookielib.LWPCookieJar()
		handlers = [
				urllib2.HTTPHandler(debuglevel=1),
				urllib2.HTTPSHandler(debuglevel=1),
				urllib2.HTTPCookieProcessor(cookies)
				]
		
		opener = urllib2.build_opener(*handlers)
		urllib2.install_opener(opener)
		
		"""if user session is not None, user is logon and futur calls is sent to the NAS with the auth cookie"""
		if self.authCookie != None :
			opener.addheaders.append(('Cookie', self.authCookie.name + '=' + self.authCookie.value))
		
		req = urllib2.Request(url)
		
		if data != None:
			req.add_header('Content-Type', 'application/xml; charset=\"UTF-8\"')
			req.add_header('Accept', '*/*')
			req.add_header('Accept-Encoding', 'gzip,deflate,sdch')
			req.add_header('Content-Length', len(data))
			req.add_data(data)
		
		""" force timeout to 30 min to allow copy large files """
		response = urllib2.urlopen(req, timeout=1800)
		
		if self.authCookie == None:
			for cookie in cookies:
				if cookie.name == 'HOMEBASEID':
					self.authCookie = cookie
					
		responseXml = ""
		while 1:
		    data = response.read()
		    print "Response http data: " + data
		    if data == "":         # This might need to be    if data == "":   -- can't remember
		        break
		    responseXml = responseXml + data
		    
		return responseXml
	
	def getAuthLogin(self):
		request = '<?xml version="1.0"?><session hipserv="' + self.nasName + '" username="' + self.userName + '" password="' + self.password + '"/>' 
		response = self._getXML(self.address + "/rest/1.0/sessions/hipserv", request.encode('utf8'))
		
		root = ET.fromstring(response)
		
		if root.get('code') == '0':
			self.nasUrl = root[0].get('url')
			self.authToken = root[0].get('auth')
			return AuthLoginResponse(root.get('code'), root[0].get('auth'), root[0].get('url'))
		else:
			return AuthLoginResponse(root.get('code'), '', '')
		
	def logon(self):
		request= ET.Element('session', {'code': self.authToken})
		
		response = self._getXML(self.nasUrl + "/api/2.0/rest/sessions", ET.tostring(request, encoding="utf-8", method="xml"))
		root = ET.fromstring(response)
		self.userSession = UserSession(root.get('supportURL'), root.get('userURI'), root.get('serverConfigURI'), root.get('href'), root.get('locale'))
		return self.userSession
	
	def getUserInformation(self):
		response = self._getXML(self.nasUrl + self.userSession.userURI)
		
		root = ET.fromstring(response)
		mediaSources = []
		
		for mediaSource in root.iter('mediaSource'):
			mediaSources.append(MediaSource(mediaSource.get('id'), mediaSource.get('name'), mediaSource.get('href')))
		
		return UserInformation(root.get('isFamilyMember'), mediaSources)
	
	def getDirectoryContent(self, href):
		response = self._getXML(self.nasUrl + href + "?mediafilter=video")
		
		root = ET.fromstring(response)
		items = []
		
		for file in root.findall('file'):
			if file.get('type') == 'folder':
				items.append(Folder(file.get('name'), file.get('href')))
				
			if file.get('type') == 'video':
				items.append(VideoFile(file.get('name'), file.get('href')))
		
		return items
	
	def copy(self, hrefDestination, hrefsToCopy, fileTypesToCopy):
		request= ET.Element('files')
		
		i = 0
		for file in hrefsToCopy:
			ET.SubElement(request, 'file', {'href': file, 'type': fileTypesToCopy[i]})
			i = i + 1
		
		""" add method query parameter to enable flex mode because python reject success code http 201 """
		response = self._getXML(self.nasUrl + hrefDestination + "?method=POST", ET.tostring(request, encoding="utf-8", method="xml"))
		