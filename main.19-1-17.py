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
    print ('Starting Stage 1 My Sockets')
    conn = mysockets.BWconnect()
    if (conn.bwlogin()):
        userlist = ocip.ocip_user_get_list_in_system(conn.sessionid, '353766875900')
        LOGGEDIN = True
    if (LOGGEDIN):
        print('Trying to send in userlist')
        result = conn.sendreceive(userlist)
        print (result)
        tree = ET.fromstring(result)
       
        for elem in tree.iter():
            print(elem.tag, elem.text)
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
        csv_writer(data,path)
        returned_list = csv_reader_column(path, 0)
        print (returned_list)

        for elem in returned_list:
            userlist = ocip.ocip_user_get(conn.sessionid, elem)
            result = conn.sendreceive(userlist)
            print (result)
            tree = ET.fromstring(result)
            for elem in tree.iter():
                print (elem.tag, elem.text)

            for elem in tree.iter():
                print (elem.tag, elem.attrib, elem.text)

        command = ocip.ocip_user_modify(conn.sessionid, 'CB-UC-testing')
        result = conn.sendreceive(command)
        print (result)
        tree = ET.fromstring(result)
        for elem in tree.iter():
            print (elem.tag, elem.text)        

           
    if (LOGGEDIN):
        conn.bwlogout()   
        conn.close()


if __name__ == "__main__":
#    print ('Start')
    main() 

