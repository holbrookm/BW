#!/usr/bin/python

""" This script will access the EMA via http commands with SOAP XML content.
    This will test Ivica's xml for vobb.
    # 0851742253
    # <mholbrook@eircom.ie>
    Modified: 23-2-17: Marc Holbrook: Added check for Lab or live connections.
    
"""

from __future__ import print_function
import sys
sys.path.insert(0, '/root/Dropbox/PYTHON/Marc/ACTIVE/BW')  # Insert your base path here for libraries

import string
import ocip_functions as ocip
import mysockets
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import csv
import os
import logging_config
from time import sleep
import scriptio as sio

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

    
logger = logging_config.logger
_sessionid = ''

#CheckOnly = True    # Check BW only, do not modify.
CheckOnly = False  # Modify BW


NCOSList = []
#barring_category = 'PRS BARRED'
#barring_category = ''



    

def get_user_choice():
    '''
        Get User Input Value
    '''
    print ('Please enter 0 to quit!')
    userChoice =int(raw_input('\n Please enter your number range contains search :'))
    if userChoice == 0 :
        sys.exit()
    return userChoice


    
def selectncos(l):
    '''
        Select the Chosen NCOS for the input list.
        List input is Name, Description.
    '''
    d = {} # temp dict
    l.pop(0) # remove Headings
    for num, elem in enumerate(l):
        d[num] = elem[0] # Take first Column only
        
    print ('Please choose the NCOS of interest for you search from the list below:  ')
    l1 = d.keys()
    l1.sort()
    for key in l1:
        print (str(key) + '  :  ' + d[key])
    while True:
        recipient = int(raw_input('Enter your choice :  '))
        if recipient in d.keys():
            break
        else:
            print ('\nPlease enter only a number indicating an NCOS choice above. ')
    
    return (d[recipient])
    
    


    
def main():
    """
        This service will run a CLI BW Range Network Class of Service modification script.
        
    """ 
    
    
    sio.cleanse_files()
    
    LOGGEDIN = False
    data = []
    row = []
    modified_subs_list = []
    failed_subs_list = []
    barring_category = ''
    
    print('\n\nThe Check ONLY option is set to : ', + CheckOnly)

    userChoice = get_user_choice() #get input range

    while True:
        yn = str(raw_input('Please confirm that you want to search for numbers containing: {0}.\t\t [y/n]'.format(userChoice)))
        if yn == 'y':
            break
        elif yn == 'n':
            userChoice = get_user_choice()
            pass
        else:
            print ('Please enter y or n..')
            pass

    userChoice = str(userChoice)
    
    # Connect to BW
    conn = mysockets.BWconnect()
    if (conn.isLiveNetwork()):
        print('Connecting to Live Broadworks Platform \n')
        
        while True:
            yn = str(raw_input('Please confirm that you want to peform Live Network Actions: [y/n]'))
            if yn == 'y':
                break
            elif yn == 'n':
                print('Ok: Shutting down. Change mysockets.py for Lab settings!\n')
                sys.exit()
            else:
                print ('Please enter y or n..')
                pass
            
    if (conn.bwlogin()):
        LOGGEDIN = True
        d = {}
        SystemNcosList = conn.get_system_ncos_options() #Get the complete System NCOS Listing. Returns Name and Description
        barring_category = selectncos(SystemNcosList)
        
        '''
        #Not needed for this program but good to have :)
        # retrieve all the enterprises with the chosen NCOS
        EnterpriseList= conn.get_service_providers_with_chosen_ncos(barring_category) # returns list of : (Service Provider Id, Service Provider Name, Is Enterprise)
        EnterpriseList.pop(0)# Remove Headers
                
        print ('The following Enterprises have the chosen NCOS assigned: [Service Provider Id : Service Provider Name     \n')
        for number, elem in enumerate(EnterpriseList):
            print (str(number) + '  :  ' + str(elem[0]) +  '  :  ' + str(elem[1]))
        
        '''
        
    else:
        print ('Failure to Log in : Please check with administrator.')
        sys.exit()
    
    # Get all 
    # Connected: Now take user input and search for subscription in BW.
    if (LOGGEDIN):
        print('\n\nTrying to send in userlist')
        
        xml = ocip.UserGetListInSystemRequest(conn.sessionid, userChoice) # Create input XML
        result = conn.sendreceive(xml)    #Retrieve subscription information using UserGetListinSystem command
        result, UserList = sio.send_ColumnRowResponse_to_file(result, sio.UserGetListInSystemRequestPath)
        UserList.pop(0) # Remove Headers from List
        
        if result:
            print ('There are {0} user subscriptions to be modified. '.format(UserList.__len__()))
            print (UserList)
            
        # Now get individual user info using UserGetResponse21 command        
        # For every user, check NCOS and change it.
        if UserList:
            for line in UserList: 
                userid = line[0]
                xml = ocip.UserGetRequest21(conn.sessionid, userid) # Take first element from list
                result = conn.sendreceive(xml)
                if not(mysockets.check_get_response(result)):
                    logger.error('Error: userlist = ocip.UserGetRequest21(conn.sessionid, userid) Failure')
                else:
                    #Start Modifying NCOS 
                    tree = ET.fromstring(result)
                    if not (CheckOnly): # Flag is set at top of this file to perform Check. Set to Modify!
                        for branch in tree.iter():
                            #Set useful parameters for later use.
                            if branch.tag == 'serviceProviderId':
                                ServiceProvider = branch.text
                            elif branch.tag == 'groupId':
                                GroupId = branch.text
                            
                            #NCOS related
                            elif branch.tag == 'networkClassOfService': #Check for incorrect NCOS
                                command = ocip.ocip_modify_user_ncos(conn.sessionid, userid, barring_category)
                                result = conn.sendreceive(command)            
                                                                
                                if (mysockets.check_modify_result(result)): # Check for positive result: Success Response from BW
                                    modified_subs_list.append(userid)
                                else:
                                    sub_tuple = (userid, ServiceProvider, GroupId)
                                    failed_subs_list.append(sub_tuple)
                            else:
                                pass
                    else: # Check Only: Therefore just print out existing NCOS
                        for branch in tree.iter():
                            if branch.tag == 'networkClassOfService': #Check for incorrect NCOS
                                print(userid , branch.text)
    #Check if any subs failed 
    if failed_subs_list: # Failed list made up of (userid, ServiceProvider, GroupId)
        for sub in failed_subs_list:
            _userid,_ServiceProvider, _GroupId = sub[0], sub[1], sub[2]
            command = ocip.ServiceProviderNetworkClassOfServiceGetAssignedListRequest(conn.sessionid, _ServiceProvider) # Get list of NCOS assigned to the failed sub Service Provider
            result = conn.sendreceive(command) 
            response, ServiceProviderNcosList = sio.send_ColumnRowResponse_to_file(result, sio.ServiceProviderNetworkClassOfServiceGetAssignedListRequestPath) #Write response to file
            ServiceProviderNcosList.pop(0) # remove headers
            #result will be in the format ['Name', 'Description', 'Default']
            found = False #temp var
            for elem in ServiceProviderNcosList:
                if barring_category in elem[0]:
                    print('Barring category available to the subscription Service provider.')
                    found = True
            if not found:
                print(str('Barring category not in Service Provider {0} assigned listing. This must be added.').format(_ServiceProvider))
                print ('Add Barring function')
                    
                      
            command = ocip.GroupNetworkClassOfServiceGetAssignedListRequest(conn.sessionid, _ServiceProvider, _GroupId) # Get list of NCOS assigned to the failed subs Trunk Group
            result = conn.sendreceive(command)
            response, GroupNcosList = sio.send_ColumnRowResponse_to_file(result, sio.GroupNetworkClassOfServiceGetAssignedListRequestPath) # Write response from BW to CSV file.
            # Result will be in the format ['Name', 'Description', 'Default']
            GroupNcosList.pop(0) # remove headers
            found = False
            for elem in GroupNcosList:
                if barring_category in elem[0]:
                    print ('Barring category is in Group.')
                    found = True
            if not found:
                print(str('Barring category not in Trunk Group {0} assigned listing. This must be added.').format(_GroupId))
                print ('Add Barring function')
                
            
    
    if (LOGGEDIN): # Make sure to close socket and logout from BW.
        for sub in modified_subs_list:
            ServiceProvider, GroupId, userid, Ncos = conn.get_user_ncos (sub)
            print (str('The modified subs are :\n   {2} in group {1} in Service Provider {0} with new NCOS {3} ').format(ServiceProvider, GroupId, userid, Ncos)) 
        conn.bwlogout()   
        conn.close()


if __name__ == "__main__":
#    print ('Start')
    main() 

