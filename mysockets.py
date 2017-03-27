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
import scriptio as sio
from time import sleep

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

#SET_LAB_FLAG = True
SET_LAB_FLAG = False
    
sys.path.insert(0, '/root/Dropbox/PYTHON/Marc/ACTIVE/BW')  # Insert your base path here for libraries
logger = logging_config.logger


#Functions to be used within/on the class..

def check_modify_result(result):
    '''
        Make sure that command response conatins the success tag.
    '''
    tree = ET.fromstring(result)
    result = False
    for b in tree.iter():
        if b.tag == 'command' and b.attrib.values()[0] == 'c:SuccessResponse':
            result = True # Successful command
    return result

def check_get_response(result):
    '''
        Make sure that command response conatins the success tag.
    '''
    tree = ET.fromstring(result)
    result = False
    for b in tree.iter():
        if b.tag == 'command' and b.attrib.values()[0] == 'UserGetResponse21':
            result = True # Successful command
    return result





    
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
        
        if SET_LAB_FLAG == True:
            self.live = False
            self.xsp_host = '10.144.134.198'   # Test Plant
        else:
            self.xsp_host ='10.144.70.198'   #Live Node SRL BW XSP-WA
            self.live = True
        
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


    def recv_timeout(self,timeout=3):
        '''
            This function retrieves the API response. 
            The receive part of send receive.
        '''
        #logger.debug(" FUNC: mysockets.recv_timeout(self, timeout)       : ")
        
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
        #logger.debug(" EXIT: mysockets.recv_timeout(self, timeout)       : ")
        return (''.join(total_data))

    def sendreceive(self, cmd):
        '''
            This function combines send and receive into one action. 
            Send using sendall(), receive using recv_timeout().
        '''
        #logger.debug(" FUNC: mysockets.sendreceive(self, cmd)       : ")   
        try: # SEND
            #logger.debug(cmd)
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
            logger.debug(str('RESPONSE :: ' + response))
        except:
            #Receive failed
            logger.error(str('Receive failed:  ' + cmd))
            sys.exit()
        #logger.debug(" EXIT: mysockets.sendreceive(self, cmd)       : ")
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


    def get_service_providers_with_chosen_ncos(self, barring_category):
        '''
            Connect to BW and retrieve all Service Providers with NCOS choice.
            Return list.
        '''
        logger.info(" FUNC: mysockets.get_service_providers_with_chosen_ncos(self, barring_category)       : ")
        xml = ocip.SystemNetworkClassOfServiceGetAssignedServiceProviderListRequest(self.sessionid, barring_category)
        _list = self.sendreceive(xml)
        result, ServiceProviders_NCOSList = sio.send_ColumnRowResponse_to_file(_list, sio.SystemNetworkClassOfServiceGetAssignedServiceProviderListRequestPath)
        if not result:    
            logger.error('mysockets:get_service_providers_with_chosen_ncos:: Service Provider - NCOS Listing not received.')
        logger.info("EXIT: mysockets.get_service_providers_with_chosen_ncos(self, barring_category)       : ")
        return ServiceProviders_NCOSList


    def get_system_ncos_options(self):
        '''
            Connect to BW and retrieve all System NCOS choices.
            Return list.
        '''
        logger.info(" FUNC: mysockets.get_system_ncos_options(self)       : ")
        xml = ocip.SystemNetworkClassOfServiceGetListRequest(self.sessionid)
        qresult = self.sendreceive(xml)
        result, SystemNcosList = sio.send_ColumnRowResponse_to_file(qresult, sio.SystemNetworkClassOfServiceGetListRequestPath)
        if not result: 
            logger.error('mysockets.get_system_ncos_options:: NCOS Listing not received.')
        logger.info("EXIT: mysockets.get_system_ncos_options(self)       : ")
        return SystemNcosList


    def get_user_ncos(self, userid):
        '''
            Connect to BW and retrieve User NCOS and other information. 
            This should be expanded later.
        '''
        
        logger.info('FUNC: mysockets.get_user_ncos(conn, userid)        ')
        xml = ocip.UserGetRequest21(self.sessionid, userid) # Take first element from list
        result = self.sendreceive(xml)
        if not(check_get_response(result)):
            logger.error('Error: userlist = ocip.UserGetRequest21(conn.sessionid, userid) Failure')
        else:
            #Start Modifying NCOS 
            tree = ET.fromstring(result)
            for branch in tree.iter():
                #Set useful parameters for later use.
                if branch.tag == 'serviceProviderId':
                    ServiceProvider = branch.text
                elif branch.tag == 'groupId':
                    GroupId = branch.text
                elif branch.tag == 'networkClassOfService': #Check for incorrect NCOS
                    Ncos = branch.text
                else:
                    pass
        logger.info('EXIT: mysockets.get_user_ncos(conn, userid)        ')
        
        return ServiceProvider, GroupId, userid, Ncos 
                  

    def add_ncos_to_system_provider(self, sub, barring_category):
        '''
            Connect to BW and check what NCOS are assigned to SP.
            If nothing, then add ncos in question and 'None' and assign default as 'None'. 
        '''
        logger.info(('FUNC: mysockets.add_ncos_to_system_provider(self, {0}, {1})        ').format(sub, barring_category))
        userid,ServiceProvider, GroupId = sub[0], sub[1], sub[2]
        command = ocip.ServiceProviderNetworkClassOfServiceGetAssignedListRequest(self.sessionid, ServiceProvider) # Get list of NCOS assigned to the failed sub Service Provider
        result = self.sendreceive(command) 
        response, ServiceProviderNcosList = sio.send_ColumnRowResponse_to_file(result, sio.ServiceProviderNetworkClassOfServiceGetAssignedListRequestPath) #Write response to file
        ServiceProviderNcosList.pop(0) # remove headers
        #result will be in the format ['Name', 'Description', 'Default']
        found = False #temp var
        exit_code = True
        if ServiceProviderNcosList:
            #NCOS exists in the XML for User
            for elem in ServiceProviderNcosList:
                if barring_category in elem[0]:
                    print('Barring category available to the subscription Service provider.')
                    found = True
            if not found:
                print(str('Barring category not in Service Provider {0} assigned listing. This must be added.').format(ServiceProvider))
                print ('Add Barring function')
                xml = ocip.ExistingServiceProviderNetworkClassOfServiceAssignListRequest21(self.sessionid, ServiceProvider, barring_category)
                result = self.sendreceive(xml)
                if not(check_modify_result(result)):
                    logger.error(('Error: userlist = ocip.ExistingServiceProviderNetworkClassOfServiceAssignListRequest21  ({0}, {1], {2}) Failure').format(ServiceProvider, GroupId, barring_category))
                    exit_code = False
 
        else: #NCOS List is empty for Service Provider/Enterprise so add Barring Category, None and set default to None.
            #
            print('Add Barring/None and Default')
            xml = ocip.ServiceProviderNetworkClassOfServiceAssignListRequest21(self.sessionid, ServiceProvider, barring_category)
            result = self.sendreceive(xml)
            if not(check_modify_result(result)):
                logger.error(('Error: userlist = ocip.ServiceProviderNetworkClassOfServiceAssignListRequest21 ({0}, {1], {2}) Failure').format(ServiceProvider, GroupId, barring_category))
                exit_code = False
        
        logger.info(('EXIT: mysockets.add_ncos_to_system_provider(self, {0}, {1})        ').format(sub, barring_category))
        return exit_code

    def add_ncos_to_group(self, sub, barring_category):
        '''
            Connect to BW and check what NCOS are assigned to Group.
            If nothing, then add ncos in question and 'None' and assign default as 'None'. 
        '''
        logger.debug(('FUNC: mysockets.add_ncos_to_group(self, {0}, {1})        ').format(sub, barring_category))
        exit_code = True
        userid,ServiceProvider, GroupId = sub[0], sub[1], sub[2]
        command = ocip.GroupNetworkClassOfServiceGetAssignedListRequest(self.sessionid, ServiceProvider, GroupId) # Get list of NCOS assigned to the failed subs Trunk Group
        result = self.sendreceive(command)
        response, GroupNcosList = sio.send_ColumnRowResponse_to_file(result, sio.GroupNetworkClassOfServiceGetAssignedListRequestPath) # Write response from BW to CSV file.
        #sleep(1)
        # Result will be in the format ['Name', 'Description', 'Default']
        GroupNcosList.pop(0) # remove headers
        found = False
        if GroupNcosList:
            for elem in GroupNcosList:
                if barring_category in elem[0]:
                    print ('Barring category is in Group.')
                    found = True
            if not found:
                print(str('Barring category not in Trunk Group {0} assigned listing. This must be added.').format(GroupId))
                xml = ocip.ExistingGroupNetworkClassOfServiceAssignListRequest21(self.sessionid, ServiceProvider, GroupId, barring_category)
                result = self.sendreceive(xml)
                if not(check_modify_result(result)):
                    logger.error(('Error: userlist = ocip.ExistingServiceProviderNetworkClassOfServiceAssignListRequest21({0}, {1], {2}) Failure').format(ServiceProvider, GroupId, barring_category))
                    exit_code = False
 
        else:
            print('Add Barring/None and Default')
            xml = ocip.GroupNetworkClassOfServiceAssignListRequest21(self.sessionid, ServiceProvider, GroupId, barring_category)
            result = self.sendreceive(xml)
            if not(check_modify_result(result)):
                logger.error(('Error: userlist = ocip.GroupNetworkClassOfServiceAssignListRequest21({0}, {1], {2}) Failure').format(ServiceProvider, GroupId, barring_category))
                exit_code = False
        
        logger.debug(('EXIT: mysockets.add_ncos_to_group(self, {0}, {1})        ').format(sub, barring_category))
        return exit_code
                
                
