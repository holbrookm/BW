#!/usr/bin/python

""" This script will access the ocip via http commands with SOAP XML content.
    #Marc Holbrook
    # 0851742253
    # <mholbrook@eircom.ie>

    Modified 15-9-16: Added Get DNS Function

"""


import debug
import logging_config

_ociuser = 'admin@web.ngv.eircom.net'
_ocipass = '&VQ|FrDb*)'
#_ociuser = 'holbrookm@web.ngv.eircom.net'
#_ocipass = 'manu16!Q'
_timeout = 30


logger = logging_config.logger

def __readinxml__(f):
    ''' Internal method to read in XML file for use within package functions.
    '''
    #logger.debug('Method : ocip_functions.__readinxml__')

    XML = open(f,'r')
    _xml = XML.read()
    #logger.debug ('**Leaving FUNC :::: ocip_functions.__readinxml__')
    XML.close()
    return (_xml)


def ocip_head(_session_id):
    """
    """
    head_xml = __readinxml__('/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK/xml/head.xml.tmpl').format(_session_id)
    #head_xml = XML.read().format(_session_id)
    return head_xml

def ocip_bottom():
    """
    """
    return __readinxml__('/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK/xml/bottom.xml.tmpl')
    
def ocip_authentication(user):
    '''
    '''
    xml = __readinxml__('/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK/xml/auth.xml.tmpl').format(user)
    return xml

def ocip_login2(signedPW):
    '''
    '''
    xml = __readinxml__('/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK/xml/login.xml.tmpl').format(_ociuser, signedPW)
    return xml

def ocip_logout(session_id):
    ''' This function will logout of the ocip platform using the session id supplied.'''
    logger.debug(" FUNC: ocip_logut   : ")
    head = ocip_head(session_id)
    _xml = __readinxml__('/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK/xml/logout.xml.tmpl').format(_ociuser)
    tail = ocip_bottom()
    logout_xml = head + _xml + tail
    encoded_body = logout_xml.replace("\n", "")
    logger.debug(encoded_body)
    logger.debug(" EXIT: ocip_logut   : ")
    return encoded_body
    

def ocip_password():
    return _ocipass

def ocip_login(session =''):
    ''' This function will login into the ocip platform using the user name and password supplied.
    '''
    logger.debug(" FUNC: ocip_function.ocipLogin(session)       : ")
    head = ocip_head(session)
    auth = ocip_authentication(_ociuser)
    tail = ocip_bottom()

    insert_xml = head + auth + tail
    encoded_body = insert_xml.replace("\n", "")
    logger.debug(encoded_body)
    logger.debug(" EXIT: ocip_function.ocipLogin(session)       : ")
    
    return (encoded_body) # Return login information for future requests

def ocip_auth_response(_sessionid, signedPW):
        '''
        '''
        logger.debug(" FUNC: ocip_function.ocip_auth_response(session, signedPW)       :  ")
        head = (ocip_head(_sessionid))
        tail = (ocip_bottom())
        command = (ocip_login2(signedPW))
        xml = head + command + tail
        encoded_body = xml.replace("\n", "")
        logger.debug(" EXIT: ocip_function.ocip_auth_response(session, signedPW)       :  ")
        return encoded_body


def ocip_user_get_list_in_system(session, search):
    '''
    '''
    logger.debug(" FUNC: ocip_function.ocip_user_get_list_in_system(session)       : ")
    head = ocip_head(session)
    command = __readinxml__('/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK/xml/getuserlistfromsystem.xml.tmpl').format(search)
    tail = ocip_bottom()

    insert_xml = head + command + tail
    encoded_body = insert_xml.replace("\n", "")
    logger.debug(encoded_body)
    logger.debug(" EXIT: ocip_function.ocip_user_get_list_in_system(session)       : ")
    
    return (encoded_body) 


def ocip_user_get(session, search):
    '''
    '''
    logger.debug(" FUNC: ocip_function.ocip_user_get(session, search)       : ")
    head = ocip_head(session)
    command = __readinxml__('/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK/xml/getuser.xml.tmpl').format(search)
    tail = ocip_bottom()

    insert_xml = head + command + tail
    encoded_body = insert_xml.replace("\n", "")
    logger.debug(encoded_body)
    logger.debug(" EXIT: ocip_function.ocip_user_get(session, search)       : ")
    
    return (encoded_body) 

def ocip_user_modify(session, search):
    '''
    '''
    logger.debug(" FUNC: ocip_function.ocip_user_modify(session, search)       : ")
    head = ocip_head(session)
    command = __readinxml__('/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK/xml/usermodifyrequest17sp4.xml.tmpl').format(search)
    tail = ocip_bottom()

    insert_xml = head + command + tail
    encoded_body = insert_xml.replace("\n", "")
    logger.debug(encoded_body)
    logger.debug(" EXIT: ocip_function.ocip_user_modify(session, search)       : ")
    
    return (encoded_body) 

def ocip_modify_user_ncos(session, userid, ncos):
    '''
    '''
    logger.debug(" FUNC: ocip_function.ocip_modify_user_ncos(session, userid, search)       : ")
    head = ocip_head(session)
    command = __readinxml__('/root/Dropbox/PYTHON/Marc/ACTIVE/BWWORK/xml/usermodifyncos.xml.tmpl').format(userid, ncos)
    tail = ocip_bottom()

    insert_xml = head + command + tail
    encoded_body = insert_xml.replace("\n", "")
    logger.debug(encoded_body)
    logger.debug(" EXIT: ocip_function.ocip_modify_user_ncos(session, userid, search)       : ")
    
    return (encoded_body)     

def ocip_modify_dynamic(session, command):
    '''
    '''
    logger.debug(" FUNC: ocip_function.ocip_modify_dynamic(session, search)       : ")
    head = ocip_head(session)
    tail = ocip_bottom()

    insert_xml = head + command + tail
    encoded_body = insert_xml.replace("\n", "")
    logger.debug(encoded_body)
    logger.debug(" EXIT: ocip_function.ocip_modify_dynamic(session, search)       : ")
    
    return (encoded_body) 





if __name__ == "__main__":
    main()




