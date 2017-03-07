#!/usr/bin/python

""" This Library will contain the iput and file information for this script..
    #
    # 0851742253
    # <mholbrook@eircom.ie>
    07/3/2017 :- Initial Draft.
    
    
"""

from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import string
import csv

import logging_config

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

sys.path.insert(0, '/root/Dropbox/PYTHON/Marc/ACTIVE/BW')  # Insert your base path here for libraries
logger = logging_config.logger


UserGetListInSystemRequestPath = './UserGetListInSystemRequest.csv'
GroupNetworkClassOfServiceGetAssignedListRequestPath = './GroupNetworkClassOfServiceGetAssignedListRequest.csv'
ServiceProviderNetworkClassOfServiceGetAssignedListRequestPath = './ServiceProviderNetworkClassOfServiceGetAssignedListRequest.csv'
SystemNetworkClassOfServiceGetListRequestPath = './SystemNetworkClassOfServiceGetListRequestPath.csv'
SystemNetworkClassOfServiceGetAssignedServiceProviderListRequestPath =  './SystemNetworkClassOfServiceGetAssignedServiceProviderListRequestPath.csv'

def cleanse_files():
    '''
        Remove csv files.
    '''
    try:
        #Remove Old CSV files
        os.remove(UserGetListInSystemRequestPath)
        os.remove(GroupNetworkClassOfServiceGetAssignedListRequestPath)
        os.remove(ServiceProviderNetworkClassOfServiceGetAssignedListRequestPath)
        os.remove(SystemNetworkClassOfServiceGetListRequestPath)
        os.remove(SystemNetworkClassOfServiceGetAssignedServiceProviderListRequestPath)
    except:
        pass
    return

    
def csv_writer(data, path):
    """
    Write data to a CSV file path
    """
    with open(path, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for line in data:
            writer.writerow(line)
    return

def csv_append(data, path):
    """
    Write data to a CSV file path
    """
    with open(path, "a") as csv_file:
        writer = csv.writer(csv_file, delimiter=',' )
        for line in data:
            writer.writerow(line)
    return
    
def csv_reader_column(file_obj, col_number):
    """
    Read a single column from a csv file
    Retruns List
    """
    data = []
    with open(file_obj, 'r') as csv_file:
        reader = csv.reader((csv_file))
        reader.next() #Move to second line, skip header titles
        for row in reader:
            data.append(row[col_number])
    return data

    
def send_ColumnRowResponse_to_file(xml, filename):
    '''
        Sends BW reposnses to csv file and returns status and data listing.
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
        csv_append(datalist, filename)  # Write data to CSV file
        exit_code = True
        
    except IOError as e:
        print (e)
        
    return exit_code , datalist
