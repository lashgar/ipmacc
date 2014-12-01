
import xml.etree.ElementTree as ET
#from termcolor import colored

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

def printDescendent(root,depth):
    if root.tag == 'pragma':
        if root.attrib.get('directive')=='kernels':
            root.tag='cuda'
    if root.getchildren()==[]:
        print bcolors.WARNING, '\t'*depth, root.tag, root.attrib , bcolors.ENDC
        #print root.text
    else:
        print bcolors.WARNING, '\t'*depth, root.tag, root.attrib , bcolors.ENDC
        for child in root:
            printDescendent(child,depth+1)


tree = ET.parse('inter.xml')
root = tree.getroot()

printDescendent(root,0)
