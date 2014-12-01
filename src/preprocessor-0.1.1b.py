import sys
import os
from optparse import OptionParser

#sys.path.extend(['.', '..', './pycparser/'])
#from pycparser import c_parser, c_ast

DEBUG=0
TOSDTOUT=0

class preprocr(object):
    def __init__(self, fname=None, foname=None):
        self.fname = fname  #path to the input c file
        self.fhandle = open(self.fname) #handler to the input c file
        self.foname = foname  #path to the output XML file
        self.fohandle = open(self.foname,'w') #handler to the output XML file
        self.fohandle.write('\n') #initial the output XML file
        self.lastchar = self.fhandle.read(1)    #last token character by the scanner, not parsed yet
        self.tagbody = ""   #store the last read characters, soon will be popped as a c, cuda, or acc pragma code
        self.tagbodytemp = ""   #store the last read characters, soon will be appended to tagbody
        self.lcomment = False   #indicating the scanner is not in the commented line
        self.bcomment = False   #indicating the scanner is not in the commented block
        self.pragma = False #indicating the scanner is in the openacc pragma line
        self.nopenbrac = 0 #the scanner is in the 0 { bracket
        self.pendingpragma = 0    #the scanner is looking for a pragma boundry. start point '{'
        self.pragmastack = [] #the stack of pragma depths. indicating where the terminating '}' is a pragma region end
        self.closebrac = 0 # number of closing brackets if we reach the end of statement
        self.nopenpran = 0 # the number of opened paranteces
    def terminate(self):
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

    #
    # INPUT READING
    def read(self):
        # append the last read character to tagbody and read a new character from fhandle 
        self.tagbody = self.tagbody+self.lastchar
        self.lastchar = self.fhandle.read(1)

    def temp_read(self):
        self.tagbodytemp = self.tagbodytemp+self.lastchar
        self.lastchar = self.fhandle.read(1)

    def temp_ignorewst(self):
        # similar to read, but ignores white spaces (' '), '\t', and '\n'
        self.temp_read()
        while ( self.lastchar==' ' or self.lastchar=='\t'):
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
            # exepectation set > move to parser
            # self.expectation(directive,clause)
            # construct tag
            tagtoprint="#pragma acc "
            tagtoprint=tagtoprint+directive+" "
            tagtoprint=tagtoprint+clause+"\n{\n"
            if (directive=="kernels" or directive=="data" or directive=="loop"):
                # find the region
                self.pendingpragma = self.pendingpragma + 1
            else:
               tagtoprint=tagtoprint+"\n}"
            # print tag
            self.printi(tagtoprint)
        else:
#            self.printi("<c><![CDATA[")
            self.printi(self.tagbody)
#            self.printi("]]></c>")
        self.tagbody=''

    def dump_endofpragma(self):
        self.poptag()
        text="}"
        if DEBUG==1:
            text=text+"//end of pragma"
        #text="</pragma>"
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

            elif (self.lastchar=='(' and self.lcomment==False and self.bcomment==False):
                self.nopenpran = self.nopenpran + 1
                self.read()
            elif (self.lastchar==')' and self.lcomment==False and self.bcomment==False):
                self.nopenpran = self.nopenpran - 1
                if self.nopenpran<0:
                    self.error("unbalanced number of paranteces");
                self.read()
            elif (self.lastchar=='{' and self.lcomment==False and self.bcomment==False):
                self.nopenbrac = self.nopenbrac+1
                if self.pendingpragma>0:
                    # start of pragma boundary
                    self.pragmastack.append(self.nopenbrac)
                    self.pendingpragma = self.pendingpragma - 1
                self.read()
            elif (self.lastchar=='}' and self.lcomment==False and self.bcomment==False):
                # potentially end of the loop
                self.read()
                while True:
                    if len(self.pragmastack)>0 and self.pragmastack[len(self.pragmastack)-1]==self.nopenbrac :
                        # end of the pragma
                        self.dump_endofpragma()
                        self.pragmastack.pop()
                    else:
                        break
                # update bracket tracking
                self.nopenbrac = self.nopenbrac-1
                if self.nopenbrac<0:
                    self.error("unbalanced number of paranteces");
                # closing one-statement pragmas
                while True:
                    if len(self.pragmastack)>0 and self.pragmastack[len(self.pragmastack)-1]==self.nopenbrac:
                        # end of the pragma
                        self.dump_endofpragma()
                        self.pragmastack.pop()
                        self.closebrac = self.closebrac - 1
                    else:
                        break
            elif (self.lastchar==';' and self.closebrac>0 and self.nopenpran==0 and self.lcomment==False and self.bcomment==False):
                self.read()
                while True:
                    if len(self.pragmastack)>0 and self.pragmastack[len(self.pragmastack)-1]==self.nopenbrac:
                        # end of the pragma
                        self.dump_endofpragma()
                        self.pragmastack.pop()
                        self.closebrac = self.closebrac - 1
                    else:
                        break
            elif (self.pendingpragma>0 and self.lcomment==False and self.bcomment==False):
                # mark to look for closing statement
                self.pendingpragma = self.pendingpragma - 1
                self.closebrac = self.closebrac + 1
                self.pragmastack.append(self.nopenbrac)
                self.read()
            elif self.lcomment==True or self.bcomment==True:
                self.temp_read()
            else:
                self.read()
        self.poptag()
        self.terminate()

def test_preprocr():
    parser = OptionParser()
#    parser.add_option("-f", "--file", dest="filename",
#                      help="Path to input C file", metavar="FILE", default="")
    #parser.add_option("-q", "--quiet",
    #                  action="store_False", dest="verbose", default=True,
    #                                    help="don't print status messages to stdout")

    # pre-process the code and make it suitable for scanner
    parser = OptionParser()
    parser.add_option("-i", "--infile", dest="infnm",
                      help="Path to input C file", metavar="FILE", default="")
    parser.add_option("-o", "--outfile", dest="outfnm",
                      help="Path to output C file", metavar="FILE", default="")
    #parser.add_option("-q", "--quiet",
    #                  action="store_False", dest="verbose", default=True,
    #                                    help="don't print status messages to stdout")

    (options, args) = parser.parse_args()

    if options.infnm=="":
        parser.print_help()
        exit(-1)
    if os.path.isfile(options.infnm):       
        J=preprocr(options.infnm,options.outfnm)
        J.labeling()
    else:
        print "preprocessor: file not found: "+options.infnm
        exit(-1)


# test_preprocr()
