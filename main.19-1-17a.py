#!/usr/bin/python

""" This script will access the EMA via http commands with SOAP XML content.
    This will test Ivica's xml for vobb.
    # 0851742253
    # <mholbrook@eircom.ie>
"""

from __future__ import print_function
import sys
sys.path.insert(0, '/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK')  # Insert your base path here for libraries

import string
import ocip_functions as ocip
import mysockets
import sys
from time import sleep
import csv

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
    

ocip_username = 'admin'
ocip_password = 'admin'

#xsp_host = '10.147.21.198'  # Live Node
xsp_host = '10.144.134.198'   # Test Plant
ocip_port = '2208'
_sessionid = ''

path = './output.csv'

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
    Read a csv file
    """
    data = []
    with open(path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        reader.next() #Move to second line, skip header titles
        for row in reader:
            data.append(row[col_number])
    return data


def main():
    """
        Testing
    """ 
    LOGGEDIN = False

    data = []
    row = []
    conn = mysockets.BWconnect()
    if (conn.bwlogin()):
        userlist = ocip.ocip_user_get_list_in_system(conn.sessionid, '353766875900')
        LOGGEDIN = True
    if (LOGGEDIN):
        print('Trying to send in userlist')
        result = conn.sendreceive(userlist)    #Retrieve subscripbtion information using UserGetListinSystem command
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

        returned_list = csv_reader_column(path, 0) #Read particular column from CSV file to list
        
        # Now get individual user info using UserGetResponse21 command        
        # For every user, check NCOS and change it.
        for elem in returned_list: 
            userlist = ocip.ocip_user_get(conn.sessionid, elem)
            result = conn.sendreceive(userlist)
            print (result)

            tree = ET.fromstring(result)
            for branch in tree.iter():
                if branch.text == 'Outgoing Service Barred': #Check for incorrect NCOS
                    command = ocip.ocip_modify_user_ncos(conn.sessionid, elem, 'CB-UC-testing')
                    print ('MODIFYING COMMAND')
                    print (command)
                    result = conn.sendreceive(command)            
                    print (result)
            '''
            \Try Dynamic request : Failing due to retrieved xml not having all required fields.
            print('*******************')
            tree = ET.fromstring(result)
            for elem in tree.iter():
                if elem.tag =='command':
                    key = (elem.attrib.keys()[0])
                    elem.attrib[key] = 'UserModifyRequest17sp4'
                if elem.tag == 'networkClassOfService':
                    elem.text = 'Outgoing Service Barred'
            xml_string = ET.tostring(tree)
        #xml_string = xml_string.replace("\n", "")
        #xml_string = xml_string.replace("ns0:", "")
        _start = xml_string.find('<command')
        _stop = xml_string.find('</ns0:Broadsoft')
        command = xml_string[_start:_stop]
        print('SUB Command is :')
        print (command)

        new_command = ocip.ocip_modify_dynamic(conn.sessionid, command)
        print('Submitted Command is:   ')
        print (new_command)
        result = conn.sendreceive(new_command)
        print (result)
        tree = ET.fromstring(result)
        for elem in tree.iter():
            print (elem.tag, elem.text)        
        '''
           
    if (LOGGEDIN):
        conn.bwlogout()   
        conn.close()


if __name__ == "__main__":
#    print ('Start')
    main() 

