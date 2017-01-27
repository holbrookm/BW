#!/usr/bin/python

""" This script will access the EMA via http commands with SOAP XML content.
    This will test Ivica's xml for vobb.
    # 0851742253
    # <mholbrook@eircom.ie>
"""

from __future__ import print_function
import sys
sys.path.insert(0, '/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK')  # Insert your base path here for libraries
import requests
import httplib2
import urllib2
import httplib
import string
import commands
import subprocess
from requests.auth import HTTPBasicAuth
import time
import sessionid
import ocip_functions as ocip
import socket
import sys
import hashlib
import re

ocip_username = 'admin'
ocip_password = 'admin'

#xsp_host = '10.147.21.198'  # Live Node
xsp_host = '10.144.134.198'   # Test Plant
ocip_port = '2208'


def main():
    """
        Testing
    """
    
    def getSignedPW(nonce, pword):
        '''
        '''
        pw =  hashlib.sha1()
        pw.update(pword)
        sha1pw = pw.hexdigest()
        spw = hashlib.md5()
        spw.update("%s:%s" %(nonce, sha1pw))
        return spw.hexdigest()
      
 
    def recv_timeout(the_socket,timeout=2):
        #make socket non blocking
        the_socket.setblocking(0)
         
        #total data partwise in an array
        total_data=[];
        data='';
         
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
                data = the_socket.recv(64)
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
        return ''.join(total_data)
     
    def make_payload():
        '''
        '''
        _sessionid = sessionid.id_generator(32)    
        head = (ocip.ocip_head(_sessionid))
        tail = (ocip.ocip_bottom())
        command = (ocip.ocip_authentication(ocip_username))
        xml = head + command + tail
        encoded_body = xml.replace("\n", "")
        return encoded_body, _sessionid
    
    def auth_response(_sessionid, signedPW):
        '''
        '''
        head = (ocip.ocip_head(_sessionid))
        tail = (ocip.ocip_bottom())
        command = (ocip.ocip_login2(signedPW))
        xml = head + command + tail
        encoded_body = xml.replace("\n", "")
        return encoded_body

    def check_connection():
        '''
        '''
        commandstring = ('timeout -s INT 5 bash -c "exec 3<>/dev/tcp/{0}/{1}";'.format(xsp_host, ocip_port))
        if(subprocess.call(commandstring, shell = True)) != 0:
            print(" Error connecting with OCI-P")
            subprocess.call('exec 3>&-;')
            sys.exit()
        print('Connection to OCI-P verified.')        
        return


    def bash_connect():
        '''
        '''
        payload = make_payload()
        print('Opening File ')
        f = open('./temp.xml.tmpl', 'w')
        f.write(payload)
        f.close()
        subprocess.call("marc.sh", shell = True)
        return


    def sendreceive(cmd):
        '''
        '''

        try:
            print('Sending in command now!!!')
            s.sendall(cmd)
        except socket.error:
        #Send failed
            print ('Send failed')
            sys.exit()
        print ('Message send successfully') 
        try:
            response = recv_timeout(s).strip()
            print (response)
        except:
            #Receive failed
            print ('Receive failed')
            sys.exit()
        return response

    #ocip.ocipLogin(ocip_username, ocip_password, _sessionid)
    
    try:
        #check_connection()
        #bash_connect()
        #xml_string = make_payload()
        #auth_request(xml_string)
        pass
    except:
        sys.exit() 

    try:
        print ('Starting Stage 1 My Sockets')
        #payload, _sessionid = make_payload()
        _sessionid = sessionid.id_generator(32)
        payload = ocip.ocip_login(_sessionid)
        endmesg = '</BroadsoftDocument>'
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print ('Failed to create socket')
            sys.exit()
     
        print ('Socket Created')
        
        try :
        #Set the whole string
            s.connect((xsp_host, 2208))
            print ('Socket Connected to ' + xsp_host + ' on port ' + ocip_port)
            s.sendall(payload)
        except socket.error:
            #Send failed
            print ('Send failed')
            sys.exit()
     
        print ('Message send successfully')
        
        s.setblocking(0) #  Set socket as not blocking
        response = recv_timeout(s).strip()
        print (response)
        print(response.__len__())
        if endmesg == (response[-20:]):
            print('YES')
            try:
                _nonce = re.search('<nonce>(.*?)</nonce>', response)
                nonce = _nonce.group(1)
                print('Nonce is :  ', nonce)
            except:
                print ('Issue with re.search')
                sys.exit()

            signedPW = getSignedPW( nonce, ocip_password)
            print ('Signed Passwaord is :  ', signedPW)
            payload = auth_response(_sessionid, signedPW)
            print (payload)
            print ('Trying to send auth response:')
            result = sendreceive(payload)
            '''
            try:
                s.sendall(payload)
            except socket.error:
            #Send failed
                print ('Send failed')
                sys.exit()
            print ('Message send successfully')    
            response = recv_timeout(s).strip()
            print (response)
            print(response.__len__())
            if endmesg == (response[-20:]):
                print('YES WE ARE IN')
            '''
                
            userlist = ocip.ocip_user_get_list_in_system(_sessionid, '766875')
            print('Trying to send in userlist')
            result = sendreceive(userlist)
            

            '''
                try:
                    print('Sending in UserList command now!!!')
                    s.sendall(userlist)
                except socket.error:
                #Send failed
                    print ('Send failed')
                    sys.exit()
                print ('Message send successfully') 
                response = recv_timeout(s).strip()
                print (response)
                print(response.__len__())
                if endmesg == (response[-20:]):
                    print('LIST IS BACK')
            '''
            result = sendreceive(ocip.ocip_logout(_sessionid))
            '''
                try:    
                    xml = (ocip.ocip_logout(_sessionid))
                    print (xml)
                    s.sendall(xml)
                except socket.error:
                #Send failed
                    print ('Send failed')
                    sys.exit()
                print ('Message send successfully')    
                response = recv_timeout(s).strip()
                print (response)
                print(response.__len__())
                if endmesg == (response[-20:]):
                    print('YES WE ARE LOGGED OUT')
            '''        
        s.close()

    except:
        print ('MySockets crap')   
        if (s):
            result = sendreceive(ocip.ocip_logout(_sessionid))
            s.close()
    """
    try:
        print('Using the Requests Module')
        headers={'cache-control':'no-cache', 'Accept-Encoding':'ISO-8859-1', 'content-type':'text/xml; charset=ISO-8859-1',\
            'Accept': 'application/soap+xml, application/dime, multipart/related, text/*' }
        #headers = {'content-type':'text/xml; charset=ISO-8859-1', 'SOAPAction':'processOCIMessage'}
        encoded_body = make_payload()
        #print (encoded_body)
        r = requests.post('http://10.144.134.198:2208', stream = True, data = encoded_body, timeout = 5, headers = headers, auth = ('admin', 'admin'))
    except requests.exceptions.RequestException as e:
        print (e)
        
    try:
        print('Starting stage httplib2')
        encoded_body = make_payload()
        http_agent = httplib2.Http(cache=None, timeout= 5, disable_ssl_certificate_validation=True)
        httplib2.debuglevel = 1
        response, response_body = http_agent.request('http://10.144.134.198:2208', method="POST", body=encoded_body, \
            headers={'cache-control':'no-cache', 'Accept-Encoding':'ISO-8859-1', 'content-type':'text/xml; charset=ISO-8859-1', \
            'Accept': 'application/soap+xml, application/dime, multipart/related, text/*', })
        print (response, response_body)

    except:
        print('Http2 orig crap')
    try:
        print ('Starting Stage 3: httplib2 again????')
        encoded_body = make_payload()
        h = httplib2.Http('.cache')
        httplib2.debuglevel = 1
        h.add_credentials('admin', 'admin')
        try:
            headers={'cache-control':'no-cache', 'Accept-Encoding':'ISO-8859-1', 'content-type':'text/xml; charset=ISO-8859-1', \
            'Accept': 'application/soap+xml, application/dime, multipart/related, text/*', }
            response, content = h.request('http://10.144.134.198:2208', timeout=5 ,headers = headers, method = 'GET', body = encoded_body )
        except requests.exceptions.RequestException as e:
            print (e)
            
        print (response)
        print (content)
    except:
        print('Error in httplib2')
    '''
    try:
        print ("Starting Stage 4")
        host = "10.144.134.198"
        port = '2208'
        url = "http://10.144.134.198:2208"
        username = 'admin'
        password = 'admin'
        message = make_payload()
         
        webservice = httplib.HTTPConnection(host, port, timeout = 5)
        webservice.set_debuglevel = 5
        # write your headers
        webservice.connect()
        webservice.putrequest("POST", url)
        webservice.putheader("Host", host)
        webservice.putheader("User-Agent", "Python http auth")
        webservice.putheader("Content-type", "text/xml; charset=\"ISO-8859-1\"")
        webservice.putheader("Content-length", "%d" % len(message))
        # write the Authorization header like: 'Basic base64encode(username + ':' + password) 
        webservice.endheaders()
        webservice.send(message)
        # get the response
        statuscode, statusmessage, header = webservice.getresponse()
        print ("Response: ", statuscode, statusmessage)
        print ("Headers: ", header)
        res = webservice.getfile().read()
        print ('Content: ', res)
    except:
        print ("Stage 4 Crap")
    '''
    """
    #ocip.ocipLogin(ocip_username, ocip_password, _sessionid)

if __name__ == "__main__":
#    print ('Start')
    main() 

