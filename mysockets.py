#!/usr/bin/python

""" This Library will contain the socket type functions needed to communicate with the BWAPI.
    # This libraby was required to use sockets as BW did not respond correctly to httplib2 
    # or the requests library.
    # 0851742253
    # <mholbrook@eircom.ie>
    13/1/2017 :- Initial Draft.
    23/2/2017 :- Added isLiveNetwork method.
    
"""

from __future__ import print_function
import sys
import socket    # Used for connecting to BW. Normal requests library not working.
import time
import hashlib   # Used for Authentication
import sessionid # Generate unique sessionid
import re   #regex Library, used to search for XML <nonce> tag
import ocip_functions as ocip  #used for building XML for BW.
import logging_config

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

sys.path.insert(0, '/root/Dropbox/PYTHON/Marc/ACTIVE/BW')  # Insert your base path here for libraries
logger = logging_config.logger


class BWconnect(object):
      
    def __init__(self):
        """
             This class creates an instance of a socket connection to BW. 
             The class includes Authentication and closing/Logout.
        """
              
        
        def connect_socket():
            '''
              Create socket and connect to host/port listed above
            '''
            logger.debug(" FUNC: mysockets.connect_socket()       : ")
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.xsp_host, self.ocip_port)) # Connect to Target System
                s.setblocking(0) #  Set socket as not blocking
            except socket.error as e:
                logger.error(str('Failed to create socket:  ' + e))
                sys.exit()     
            logger.debug(str('Socket Connected to ' + self.xsp_host + ' on port ' + str(self.ocip_port)))
            
            logger.debug(" EXIT: mysockets.connect_socket()       : ")
            return s  #return socket


        logger.debug(" FUNC: mysockets.__init__(self)       : ")
        
        #self.xsp_host ='10.144.70.198'   #Live Node SRL BW XSP-WA
        self.xsp_host = '10.144.134.198'   # Test Plant
        #self.live = True
        self.live = False
        self.ocip_port = 2208
        self.sessionid = sessionid.id_generator(32)
        self.nonce = ''
        self.sha1pw = ''
        self.pw =''
        self.s = connect_socket()
        self.hexdigest =''
        
        logger.debug(" EXIT: mysockets.__init__(self)       : ")
        return
        
    def isLiveNetwork(self):
        return self.live
        
        
    def getSignedPW(self, pword):
        '''
            Take password and nonce and return signedPassword to authenticate with BW.
        '''
        logger.debug(" FUNC: mysockets.getSignedPW(self)       : ")
 
        self.pw =  hashlib.sha1()
        self.pw.update(pword)
        self.sha1pw = self.pw.hexdigest()
        self.spw = hashlib.md5()
        self.spw.update("%s:%s" %(self.nonce, self.sha1pw))
        logger.debug("%s:%s" %(self.nonce, self.sha1pw))
        self.signedPW = self.spw.hexdigest()
        logger.debug(" EXIT: mysockets.getSignedPW(self)       : ")
        return

    def close(self):
        '''
            Close socket.
        '''
        logger.debug(" FUNC: mysockets.close(self)       : ")
        self.s.close()
        logger.debug(" EXIT: mysockets.close(self)       : ")
        return


    def recv_timeout(self,timeout=2):
        '''
            This function retrieves the API response. 
            The receive part of send receive.
        '''
        logger.debug(" FUNC: mysockets.recv_timeout(self, timeout)       : ")
        
        #make socket non blocking
        self.s.setblocking(0)     
        #total data partwise in an array
        total_data=[]
        data=''
        #beginning time
        begin=time.time()
        while 1:
            #if you got some data, then break after timeout
            if total_data and time.time()-begin > timeout:
                break
             
            #if you got no data at all, wait a little longer, twice the timeout
            elif time.time()-begin > timeout*2:
                break
             
            #recv something
            try:
                data = self.s.recv(64)
                if data:
                    total_data.append(data)
                    #change the beginning time for measurement
                    begin=time.time()
                else:
                    #sleep for sometime to indicate a gap
                    time.sleep(0.1)
            except:
                pass
         
        #join all parts to make final string
        logger.debug(" EXIT: mysockets.recv_timeout(self, timeout)       : ")
        return (''.join(total_data))

    def sendreceive(self, cmd):
        '''
            This function combines send and receive into one action. 
            Send using sendall(), receive using recv_timeout().
        '''
        logger.debug(" FUNC: mysockets.sendreceive(self, cmd)       : ")   
        try: # SEND
            logger.debug(cmd)
            self.s.sendall(cmd)
        except socket.error:
        #Send failed
            logger.error(str('Send failed:   ' + cmd))
            self.bwlogout()
            self.s.close()
            print('Error: The following command failed to send to BW. Exiting script.')
            print (cmd)
            sys.exit()
        try: # RECEIVE
            response = self.recv_timeout(2).strip()
            logger.debug(response)
        except:
            #Receive failed
            logger.error(str('Receive failed:  ' + cmd))
            sys.exit()
        logger.info(" EXIT: mysockets.sendreceive(self, cmd)       : ")
        return response

    def bwlogin(self):
        '''
           Login to the BW OCI-P using the XSP-WA server.
        '''
        logger.info(" FUNC: mysockets.bwlogin(self)       : ")
       
        loginxml = ocip.ocip_login(self.sessionid) # Initialise Login procedure
        response = self.sendreceive(loginxml)
        if (response): # Perform authentication if response is not an error.
            if not(re.search('Error', response)):
                self.nonce = re.search('<nonce>(.*?)</nonce>', response)
                self.nonce = self.nonce.group(1)
                logger.debug(str('Nonce is :  ' + self.nonce))
                pword = ocip.ocip_password()
                self.getSignedPW(pword)
                logger.debug (str('Signed Password is :  ' + self.signedPW))
                authxml = ocip.ocip_auth_response(self.sessionid, self.signedPW)
                    
                response = self.sendreceive(authxml)
                authresponse = re.search('<passwordExpiresDays>(.*?)</passwordExpiresDays>', response)  
                if not (authresponse):
                    Logger.error ('ERROR in Authentication')
                    exitcode = False
                else:
                    exitcode = True
            else: # Check if error message had information, if so print it
                tree = ET.fromstring(response)
                for b in tree.iter():
                    if b.tag == 'summary':
                        logger.error(b.text)
                        print ('\n' + b.text + '\n')
                exitcode = False
        logger.info(" EXIT: mysockets.bwlogin(self)       : ")   
        return exitcode 

    def bwlogout(self):
        '''
           Logout from BW using API
        '''
        logger.info(" FUNC: mysockets.bwlogout(self)       : ")
        logoutxml = ocip.ocip_logout(self.sessionid)
        response = self.sendreceive(logoutxml)
        print(response)
        logger.info(" EXIT: mysockets.bwlogout(self)       : ")
        return













