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
from time import sleep

try:
    import xml.etree.cElementTree as ET   # Library for XML Parsing
except ImportError:
    import xml.etree.ElementTree as ET
    

_sessionid = ''

CheckOnly = True    # Check BW only, do not modify.
#CheckOnly = False  # Modify BW

path = './output.csv'
range_path = './range.csv'
input_file = './subs.csv'
        
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
    with open(path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        reader.next() #Move to second line, skip header titles
        for row in reader:
            data.append(row[col_number])
    return data
    
def read_file(input_file):
    '''
        Read in subs file and prepare.
        Outputs list of numbers.
    '''
    data = []
    with open(input_file, 'r') as f:
        for line in f:
            start = line.find('+353') + 4
            stop = line.find('@')
            data.append(line[start:stop])
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


def main():
    """
        This service will run a CLI BW Range Network Class of Service modification script.
        
    """ 
    LOGGEDIN = False
    data = []
    row = []
    modified_subs_list = []
    range_list = []
    
    file_data = read_file(input_file)
        
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
        print('Trying to send in userlist')
        
        first_run =  True
        useridlist = []
        previous_number = ''
        
        for number in file_data:
            if number != (''):
                userlist = ocip.ocip_get_number_contains_from_system_list(conn.sessionid, number)
                
                result = conn.sendreceive(userlist)    #Retrieve subscription information using UserGetListinSystem command
                
                tree = ET.fromstring(result)
                
                #Parse details and print in csv file
                for elem in tree.iter():
                    if first_run:
                        if(elem.tag == 'colHeading'):
                            row.append(elem.text)
                        elif (elem.tag == 'row'):
        
                            stop = str(row[0]).find('@')
                            first_run = False
                            check = row[0][:stop]
                            
        
                            if (str(check).endswith(previous_number)):
                                data.append(row)
                            else:
                                range_list.append(previous_number)
                            row = []
                        elif (elem.tag == 'col'):
                            row.append(elem.text)
                        else:
                            pass
                        
                    else:
                        if (elem.tag == 'row'):
        
                            stop = str(row[0]).find('@')
                            check = str(row[0])[:stop]
                            
                            if (check.endswith(previous_number)):
                                data.append(row)
                            else:
                                range_list.append(previous_number)
                            row = []
                        elif (elem.tag == 'col'):
                            row.append(elem.text)
                        else:
                            pass
            previous_number =  number            
                
        
        
            
            #sleep(10)
        print('Writing to File!!!!!')
        
        csv_writer(data,path)  # Write data to CSV file
        csv_writer(range_list, range_path)
    else:
        print ('Failure to Log in : Please check with administrator.')
        sys.exit()

    # Connected: Now take user input and search for subscription in BW.

    
    returned_list = csv_reader_column(path, 0) #Read particular column from CSV file to list
    print ('There are {0} user subscriptions to be modified. '.format(returned_list.__len__()))
    
    """
        # Now get individual user info using UserGetResponse21 command        
        # For every user, check NCOS and change it.
        for number in returned_list: 
            userlist = ocip.ocip_user_get(conn.sessionid, userid)
            result = conn.sendreceive(userlist)

            #Start Modifying NCOS 
            tree = ET.fromstring(result)
            if not (CheckOnly): # Flag is set at top of this file to perform Check. Set to Modify!
                for branch in tree.iter():
                    if branch.tag == 'networkClassOfService': #Check for incorrect NCOS
                        #command = ocip.ocip_modify_user_ncos(conn.sessionid, userid, 'Outgoing Service Barred')
                        command = ocip.ocip_modify_user_ncos(conn.sessionid, userid, 'PRS BARRED')
                        #command = ocip.ocip_modify_user_ncos(conn.sessionid, userid, 'Incoming Service Barred')
                        result = conn.sendreceive(command)            
                        if (check_result(result)): # Check for positive result: Success Response from BW
                            modified_subs_list.append(userid)
                        pass

            else: # Check Only: Therefore just print out existing NCOS
                for branch in tree.iter():
                    if branch.tag == 'networkClassOfService': #Check for incorrect NCOS
                        print(userid , branch.text)
        
    """
        
    if (LOGGEDIN): # Make sure to close socket and logout from BW.
        print ('The modified subs are :    ' + str(modified_subs_list) )
        conn.bwlogout()   
        conn.close()


if __name__ == "__main__":
#    print ('Start')
    main() 

