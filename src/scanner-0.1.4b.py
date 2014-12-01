from lxml.builder import E
from lxml import etree
import sys
import os

from optparse import OptionParser

DEBUG=0
TOSDTOUT=0

class scanner(object):
    def __init__(self, fname=None, foname=None):
        self.fname = fname  #path to the input c file
        self.fhandle = open(self.fname) #handler to the input c file
        self.foname = foname  #path to the output XML file
        self.fohandle = open(self.foname,'w') #handler to the output XML file
        self.fohandle.write('<scanner version=\'0.1.4b\'>\n') #initial the output XML file
        self.lastchar = self.fhandle.read(1)    #last token character by the scanner, not parsed yet
        self.tagbody = ""   #store the last read characters, soon will be popped as a c, cuda, or acc pragma code
        self.tagbodytemp = ""   #store the last read characters, soon will be appended to tagbody
        self.lcomment = False   #indicating the scanner is not in the commented line
        self.bcomment = False   #indicating the scanner is not in the commented block
        self.pragma = False #indicating the scanner is in the openacc pragma line
        self.nopenbrac = 0 #the scanner is in the 0 { bracket
        self.pendingloop = 0    #the scanner is looking for 0 loop boundry. start point '{' or end point ';'
        self.pendingpragma = 0    #the scanner is looking for a pragma boundry. start point '{'
        self.loopstack = [] #the stack of loop depths. indicating where the terminating '}' is a loop-end
        self.pragmastack = [] #the stack of pragma depths. indicating where the terminating '}' is a pragma region end
#        self.expectloop = False #when True, indicates the scanner expect a parallel loop, usually immediately after 'pragma acc loop'
    def __del__(self):
        self.fohandle.write('</scanner>\n') #finalize the output XML file
        self.fohandle.close()
        self.fhandle.close()
        
    def error(self, prompt):
        print "error: "+prompt
        sys.exit(1)

    def printi(self, text):
        if (TOSDTOUT==1):
            print text
        else:
            self.fohandle.write(text+'\n')

    def encode(self, text):
        return text.replace('&','&amp;').replace('>','&gt;').replace('<','&lt;')
    #
    #
    #
    # SYNTAX VALIDITY CHECKERS
    def validity_directive(self, directive):
        # check the validity of directive
        if (directive=="loop" or
            directive=="kernels" or
            directive=="data" or
            directive=="parallel") :
            return True
        else:
            self.error("undefined directive: "+directive)
            return False

    def validity_clause(self, directive, clause):
        # check the validity of clause
        return True
    
#    def expectation(self, directive, clause):
#        if directive=="loop":
#            self.expectloop=True;


    #
    #
    #
    # INPUT READING
    def read(self):
        # append the last read character to tagbody and read a new character from fhandle 
        self.tagbody = self.tagbody+self.lastchar
        self.lastchar = self.fhandle.read(1)

    def temp_read(self):
        self.tagbodytemp = self.tagbodytemp+self.lastchar
        self.lastchar = self.fhandle.read(1)

    def ignorewst(self):
        # similar to read, but ignores white spaces (' ') and '\t'
        self.read()
        while ( self.lastchar==' ' or self.lastchar=='\t'):
            self.read()
       
    def ignorewstn(self):
        # similar to read, but ignores white spaces (' '), '\t', and '\n'
        self.read()
        while ( self.lastchar==' ' or self.lastchar=='\t' or self.lastchar=='\n'):
            self.read()
 
    def temp_ignorewst(self):
        # similar to read, but ignores white spaces (' '), '\t', and '\n'
        self.temp_read()
        while ( self.lastchar==' ' or self.lastchar=='\t'):
            self.temp_read()

    def temp_ignorewstn(self):
        # similar to read, but ignores white spaces (' '), '\t', and '\n'
        self.temp_read()
        while ( self.lastchar==' ' or self.lastchar=='\t' or self.lastchar=='\n'):
            self.temp_read()

    def temp_clear(self):
        # reset the tagbodytemp
        self.tagbodytemp = ""
    
    def temp_append(self):
        # clear and append temp to tagbody
        self.tagbody = self.tagbody + self.tagbodytemp
        self.temp_clear()

    def poptag(self):
        # end of the code block has been detected
        # dumpout tagbody, c, cuda, or pragma acc tag
        if self.pragma==True:
            # the last code block is pragma acc tag, dump out regular pragma tag for parser
            # find directive and clauses
            a=self.tagbody
            w=a.split()
            directive=w[0]
            clause=' '.join(w[1:len(w)])
            # check validity
            self.validity_directive(directive)
            self.validity_clause(directive, clause)
            # exepectation set > move to parser
            # self.expectation(directive,clause)
            # construct tag
            tagtoprint="<pragma "
            tagtoprint=tagtoprint+"directive='"+directive+"' "
            tagtoprint=tagtoprint+"clause='"+clause+"' "
            tagtoprint=tagtoprint+">"
            if (directive=="kernels" or directive=="data" or directive=="loop"):
                # find the region
                self.pendingpragma = self.pendingpragma + 1
            else:
               tagtoprint=tagtoprint+"</pragma>"
            # print tag
            self.printi(tagtoprint)
        else:
            self.printi("<c><![CDATA[")
            self.printi(self.tagbody)
            self.printi("]]></c>")
        self.tagbody=''

    def dump_forloop(self):
        a=self.tagbodytemp[1:len(self.tagbodytemp)-1]
        w=a.split(';')
#        text="<for statement='"+self.tagbodytemp+"'>"
        text="<for initial='"+self.encode(w[0]).split('=')[1].strip()+"' boundary='"+self.encode(w[1])
        text=text+"' increment='"+self.encode(w[2])+"'"+" iterator='"+self.encode(w[0]).split('=')[0].strip()+"' >"
        self.printi(text)
        self.tagbodytemp=""

    def dump_endoffor(self):
        self.poptag()
        text="</for>"
        self.printi(text)

    def dump_endofpragma(self):
        self.poptag()
        text="</pragma>"
        self.printi(text)

    def labeling(self):
        while self.lastchar:
            #print self.lastchar
            if self.lastchar=='/':
                #potentially comment
                self.temp_read()
                #self.temp_read()
                if self.lastchar=='/':
                    #line comment
                    if DEBUG==1: print "line comment >"
                    self.lcomment=True
                    self.temp_read()
                elif self.lastchar=='*':
                    #block comment
                    if DEBUG==1: print "block comment >"
                    self.bcomment=True
                    self.temp_read()
                else:
                    self.temp_append()
            elif self.lastchar=='\n':
                if self.lcomment==True:
                    #line termination
                    if DEBUG==1: print "< line comment"
                    self.lcomment=False
                    self.temp_clear()
                elif self.pragma==True:
                    #pragma termination
                    self.poptag()
                    self.pragma=False
                self.read()
            elif self.lastchar=='*' and self.bcomment==True:
                #potentially block comment end
                self.temp_read()
                #self.read()
                if self.lastchar=='/':
                    #block comment end
                    if DEBUG==1: print "< block comment"
                    self.bcomment=False
                    self.temp_clear()
                    self.read()
                else:
                    self.temp_append()
#            elif (self.lastchar=='#' and self.lcomment==False and self.bcomment==False):
#                #potentially ACC pragma
#                self.ignorewst()
#                if self.lastchar=='p':
#                    self.read()
#                    if self.lastchar=='r':
#                        self.read()
#                        if self.lastchar=='a':
#                            self.read()
#                            if self.lastchar=='g':
#                                self.read()
#                                if self.lastchar=='m':
#                                    self.read()
#                                    if self.lastchar=='a':
#                                        self.ignorewst()
#                                        if self.lastchar=='a':
#                                            self.read()
#                                            if self.lastchar=='c':
#                                                self.read()
#                                                if self.lastchar=='c':
#                                                    self.ignorewst()
#                                                    self.poptag()
#                                                    self.pragma=True

            elif (self.lastchar=='#' and self.lcomment==False and self.bcomment==False):
                #potentially ACC pragma
                broken=1
                self.temp_ignorewst()
                if self.lastchar=='p':
                    self.temp_read()
                    if self.lastchar=='r':
                        self.temp_read()
                        if self.lastchar=='a':
                            self.temp_read()
                            if self.lastchar=='g':
                                self.temp_read()
                                if self.lastchar=='m':
                                    self.temp_read()
                                    if self.lastchar=='a':
                                        self.temp_ignorewst()
                                        if self.lastchar=='a':
                                            self.temp_read()
                                            if self.lastchar=='c':
                                                self.temp_read()
                                                if self.lastchar=='c':
                                                    self.temp_ignorewst()
                                                    self.poptag()
                                                    self.pragma=True
                                                    broken=0
                if broken==1:
                    self.temp_append()

            elif (self.lastchar=='f' and self.lcomment==False and self.bcomment==False and len(self.pragmastack)>0):
                #potentially `for` loop in pragma
                self.temp_read()
                if self.lastchar=='o':
                    self.temp_read()
                    if self.lastchar=='r':
                        # found a loop at self.nopenbrac depth
                        self.poptag()
                        # find loop statement
                        self.temp_ignorewstn()
                        # clear the temp
                        self.temp_clear()
                        # capture the loop statement
                        if self.lastchar=='(':
                            # read all the statement of for
                            indent=1
                            while True:
                                self.temp_read()
                                if self.lastchar=='(':
                                    indent=indent+1
                                elif self.lastchar==')':
                                    indent=indent-1
                                if indent==0:
                                    break
                                
                                if indent<0:
                                    self.error("unbalanced number of paranteces")
                            self.temp_read()
                            self.dump_forloop()
                            # find the loop region
                            self.pendingloop = self.pendingloop + 1
                        else:
                            self.error("expecting '(' before "+self.lastchar)
                    else:
                        self.temp_append()
                else:
                    self.temp_append()
            elif (self.lastchar=='{' and self.lcomment==False and self.bcomment==False):
                self.nopenbrac = self.nopenbrac+1
                if self.pendingloop>0 :
                    # start of loop boundry
                    self.loopstack.append(self.nopenbrac)
                    self.pendingloop = self.pendingloop - 1
                elif self.pendingpragma>0:
                    # start of pragma boundary
                    self.pragmastack.append(self.nopenbrac)
                    self.pendingpragma = self.pendingpragma - 1
                self.read()
            elif (self.lastchar=='}' and self.lcomment==False and self.bcomment==False):
                # potentially end of the loop
                self.read()
                if len(self.loopstack)>0 and self.loopstack[len(self.loopstack)-1]==self.nopenbrac :
                    # end of the for
                    self.dump_endoffor()
                    self.loopstack.pop()
                elif len(self.pragmastack)>0 and self.pragmastack[len(self.pragmastack)-1]==self.nopenbrac :
                    # end of the pragma
                    self.dump_endofpragma()
                    self.pragmastack.pop()
                # update bracket tracking
                self.nopenbrac = self.nopenbrac-1
                if self.nopenbrac<0:
                    self.error("unbalanced number of paranteces");
            elif self.lcomment==True or self.bcomment==True:
                self.temp_read()
            else:
                self.read()
        self.poptag()
        #    sys.stdout.write(self.lastchar)
        #    if self.lastchar=='/':
                

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="Path to input C file", metavar="FILE", default="")
#parser.add_option("-q", "--quiet",
#                  action="store_False", dest="verbose", default=True,
#                                    help="don't print status messages to stdout")

(options, args) = parser.parse_args()

if options.filename=="":
    parser.print_help()
    exit(-1)
if os.path.isfile(options.filename):       
    J=scanner(options.filename,"__inter.xml")
    J.labeling()
else:
    print "scanner: file not found: "+options.filename
    exit(-1)
