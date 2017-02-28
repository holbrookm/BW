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
import csv

try:
    import xml.etree.cElementTree as ET   # Library for XML Parsing
except ImportError:
    import xml.etree.ElementTree as ET
    

_sessionid = ''

#CheckOnly = True    # Check BW only, do not modify.
CheckOnly = False  # Modify BW

UserGetListInSystemRequestPath = './UserGetListInSystemRequest.csv'

barring_category = 'PRS BARRED'
#barring_category = 'Incoming Service Barred'
        
def csv_writer(data, path):
    """
    Write data to a CSV file path
    """
    with open(path, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for line in data:
            writer.writerow(line)
    return

def csv_reader_column(file_obj, col_number):
    """
    Read a single column from a csv file
    """
    data = []
    with open(file_obj, 'r') as csv_file:
        reader = csv.reader(csv_file)
        reader.next() #Move to second line, skip header titles
        for row in reader:
            data.append(row[col_number])
    return data

def check_result(result):
    '''
        Make sure that command response conatins the success tag.
    '''
    tree = ET.fromstring(result)
    result = False
    for b in tree.iter():
        if b.tag == 'command' and b.attrib.values()[0] == 'c:SuccessResponse':
            result = True # Successful command
    return result


def get_user_choice():
    '''
        Get User Input Value
    '''
    print ('Please enter 0 to quit!')
    userChoice =int(raw_input('\n Please enter your number range contains search :'))
    if userChoice == 0 :
        sys.exit()
    return userChoice

def send_UserGetListInSystemResponse_to_file(xml, filename):
    '''
    '''
    #Local vars
    datalist = []
    rowlist = []
    exit_code = False
    #Unpack XML response
    tree = ET.fromstring(xml)
        
    #Parse details and print in csv file
    try:
        for elem in tree.iter():
            if(elem.tag == 'colHeading'):
                rowlist.append(elem.text)
            elif (elem.tag == 'row'):
                datalist.append(rowlist)
                rowlist = []
            elif (elem.tag == 'col'):
                rowlist.append(elem.text)
            else:
                pass
        datalist.append(rowlist)
        csv_writer(datalist, filename)  # Write data to CSV file
        exit_code = True
        
    except IOError as e:
        print (e)
        
    return exit_code
    
def main():
    """
        This service will run a CLI BW Range Network Class of Service modification script.
        
    """ 
    LOGGEDIN = False
    data = []
    row = []
    modified_subs_list = []
    print('\n\nThe Check ONLY option is set to : ', + CheckOnly)

    userChoice = get_user_choice() #get input range

    while True:
        print ('Please confirm that you want to search for numbers containing: {0}. y/n'.format(userChoice))
        yn = str(raw_input('\n y or n?'))
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
            print ('Please confirm that you want to peform Live Network Actions: [y/n]')
            yn = str(raw_input('\n y or n?'))
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
    else:
        print ('Failure to Log in : Please check with administrator.')
        sys.exit()

    # Connected: Now take user input and search for subscription in BW.
    if (LOGGEDIN):
        print('Trying to send in userlist')
        userlist = ocip.UserGetListInSystemRequest(conn.sessionid, userChoice) # Create input XML
        result = conn.sendreceive(userlist)    #Retrieve subscription information using UserGetListinSystem command
        if (send_UserGetListInSystemResponse_to_file(result, UserGetListInSystemRequestPath)):
        
            '''
        tree = ET.fromstring(result)
        
        #Parse details and print in csv file
        for elem in tree.iter():
            if(elem.tag == 'colHeading'):
                row.append(elem.text)
            elif (elem.tag == 'row'):
                data.append(row)
                row = []
            elif (elem.tag == 'col'):
                row.append(elem.text)
            else:
                pass
        data.append(row)
        csv_writer(data,path)  # Write data to CSV file
            '''
        
        
            returned_list = csv_reader_column(UserGetListInSystemRequestPath, 0) #Read particular column from CSV file to list
            print ('There are {0} user subscriptions to be modified. '.format(returned_list.__len__()))
            print (returned_list)
            
        # Now get individual user info using UserGetResponse21 command        
        # For every user, check NCOS and change it.
        if returned_list:
            for userid in returned_list: 
                userlist = ocip.ocip_user_get(conn.sessionid, userid)
                result = conn.sendreceive(userlist)

                #Start Modifying NCOS 
                tree = ET.fromstring(result)
                if not (CheckOnly): # Flag is set at top of this file to perform Check. Set to Modify!
                    for branch in tree.iter():
                        if branch.tag == 'networkClassOfService': #Check for incorrect NCOS
                            #command = ocip.ocip_modify_user_ncos(conn.sessionid, userid, 'Outgoing Service Barred')
                            command = ocip.ocip_modify_user_ncos(conn.sessionid, userid, barring_category)
                            #command = ocip.ocip_modify_user_ncos(conn.sessionid, userid, 'Incoming Service Barred')
                            result = conn.sendreceive(command)            
                            if (check_result(result)): # Check for positive result: Success Response from BW
                                modified_subs_list.append(userid)
                            pass

                else: # Check Only: Therefore just print out existing NCOS
                    for branch in tree.iter():
                        if branch.tag == 'networkClassOfService': #Check for incorrect NCOS
                            print(userid , branch.text)

    if (LOGGEDIN): # Make sure to close socket and logout from BW.
        print ('The modified subs are :    ' + str(modified_subs_list) )
        conn.bwlogout()   
        conn.close()


if __name__ == "__main__":
#    print ('Start')
    main() 

