import requests, time, re
from lxml import html
import logging, os, platform, sys
import xml.dom.minidom, xml.sax.saxutils

#ENVIRONMENTAL INFORMATION
__author__ = "george@georgestarcher.com (George Starcher)"
_MI_APP_NAME = 'TA-laundryview'
_SPLUNK_HOME = os.getenv("SPLUNK_HOME")
if _SPLUNK_HOME == None:
    _SPLUNK_HOME = os.getenv("SPLUNKHOME")
if _SPLUNK_HOME == None:
    _SPLUNK_HOME = "/opt/splunk"

_OPERATING_SYSTEM = platform.system()
_APP_HOME = _SPLUNK_HOME + "/etc/apps/TA-laundryview"
_LIB_PATH = _APP_HOME + "bin/lib"
_PID = os.getpid()
_IS_WINDOWS = False

if _OPERATING_SYSTEM.lower() == "windows":
    _IS_WINDOWS = True
    _LIB_PATH.replace("/","\\")
    _APP_HOME.replace("/","\\")

#SYSTEM EXIT CODES
_SYS_EXIT_FAILED_LAUNDRY = 7 
_SYS_EXIT_GPARENT_PID_ONE = 8

#Setup logging
logging.root
logging.root.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.root.addHandler(handler)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S%z')
logging.Formatter.converter = time.gmtime

#Set timestamp and define machine error types
logTime = time.strftime("%Y-%m-%d %H:%M:%S%z")
machineError = ['Offline','Out of service','Unknown']

SCHEME = """<scheme>
    <title>TA-laundryview</title>
    <description>Collect laundry room machine data.</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>simple</streaming_mode>
    <endpoint>
        <args>
            <arg name="siteCode">
                <title>LaundyView SiteCode</title>
                <description>The LaundryView SiteCode</description>
            </arg>
        </args>
    </endpoint>
</scheme>
"""

def doPrint(s):
    """ A wrapper Function to output data by same method (print vs sys.stdout.write)"""
    sys.stdout.write(s)

def do_scheme():
    """ Prints the Scheme """
    doPrint(SCHEME)

def get_source(config):
    return "laundryview:" + config

def validate_arguments():
    pass

def getSiteCode():
    try:
        # read everything from stdin
        config_str = sys.stdin.read()

        #parse the config XML
        doc = xml.dom.minidom.parseString(config_str)
        root = doc.documentElement
        conf_node = root.getElementsByTagName("configuration")[0]
        if conf_node:
            stanza = conf_node.getElementsByTagName("stanza")[0]
            if stanza:
                stanza_name = stanza.getAttribute("name")
                if stanza_name:
                    params = stanza.getElementsByTagName("param")
                    for param in params:
                        param_name = param.getAttribute("name")
                        if param_name and param.firstChild and \
                           param.firstChild.nodeType == param.firstChild.TEXT_NODE and \
                           param_name == "siteCode":
                            return param.firstChild.data
    except Exception, e:
        raise Exception, "Error getting Splunk configuration via STDIN: %s" % str(e)

    return ""

def getSitePage(siteCode):
    """ fetch the web page contents for the site """
    page = requests.get('http://lite.laundryview.com/laundry_room.php?lr='+siteCode)
    tree = html.fromstring(page.text)
    return(tree)

def getSiteName(pageTree):
    """ parse the site page tree for the location site name (school) """
    site_name = pageTree.xpath('//table/tr//h1/text()')
    return(site_name[0])

def getSiteRoom(pageTree):
    """ parse the site page tree for the location site room name (laundry room) """
    room_name = pageTree.xpath('//table/tr//strong/text()')
    return(room_name[0])

def isInUse(machineStatus):
    """ generate the machine in use field """
    if machineStatus in machineError:
        return('No')
    if machineStatus=="Avail":
        return('No')
    else:
        return('Yes')

def getMachineID(machine):
    """ parse the machine ID and Number """
    rexPattern = '^(.*?)\s\((.*?)\)'
    machineID = re.search(rexPattern, machine).group(1)
    machineNumber = re.search(rexPattern, machine).group(2)
    return(machineID, machineNumber)

def outputWashers(pageTree, siteName, siteRoom):
    """ parse the site page tree for the washers and their status """
    washers = pageTree.xpath('//tr/td[1]/div/span[1]/text()')
    washer_status = pageTree.xpath('//tr/td[1]/div/span[2]/text()')
    washer_dict = zip(washers, washer_status)
    for washer,status in washer_dict:
        inUse = isInUse(status)
        machineID, machineNumber = getMachineID(washer)
        print logTime+" site_name=\""+siteName+"\" room_name=\""+siteRoom+"\" type=washer machineID="+machineID+" machineNumber="+machineNumber+" inUse="+inUse+" status=\""+status+"\""

def outputDryers(pageTree, siteName, siteRoom):
    """ parse the site page tree for the dryers and their status """
    dryers = pageTree.xpath('//tr/td[3]/div/span[1]/text()')
    dryer_status = pageTree.xpath('//tr/td[3]/div/span[2]/text()')
    dryer_dict = zip(dryers, dryer_status)
    for dryer,status in dryer_dict:
        inUse = isInUse(status)
        machineID, machineNumber = getMachineID(dryer)
        print logTime+" site_name=\""+siteName+"\" room_name=\""+siteRoom+"\" type=dryer machineID="+machineID+" machineNumber="+machineNumber+" inUse="+inUse+" status=\""+status+"\""

def getSite(siteCode):
    try:
       sitePageTree = getSitePage(siteCode)
       siteName = getSiteName(sitePageTree)
       siteRoom = getSiteRoom(sitePageTree)
       outputWashers(sitePageTree, siteName, siteRoom)
       outputDryers(sitePageTree, siteName, siteRoom)
    except Exception, e:
        logging.debug("script="+_MI_APP_NAME+" %s" % str(e))
        exit(_SYS_EXIT_FAILED_LAUNDRY)

if __name__ == "__main__":

    UoAsiteCodes = ['455621', '1937659', '1937660', '1937645', '1937611', '19376136', '1937663', '1937664', '1937671', '1937672', '1937669', '1937670', '1937665', '1937666', '1937656', '1937655', '1937651', '1937652', '1937653', '1937654', '1937618']

    if len(sys.argv) > 1:
        if sys.argv[1] == "--scheme":
            do_scheme()
        if sys.argv[1] == "--validate-arguments":
            validate_arguments()
        else:
            pass
    else:
        siteCode = getSiteCode()
        getSite(siteCode)

    sys.exit(0)
