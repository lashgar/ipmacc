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
        self.fcontent = self.fhandle.read() # read entire file
        self.fcontent = self.fcontent.replace('\\\n','')
        self.fcontent = self.fcontent.replace('\\\r\n','')
        self.findex=0
        self.lastchar = self.fcontent[self.findex]    #last token character by the scanner, not parsed yet
        self.findex+=1
        self.plastchar = '' # the previous value of lastchar
        self.tagbody = ""   #store the last read characters, soon will be popped as a c, cuda, or acc pragma code
        self.tagbodytemp = ""   #store the last read characters, soon will be appended to tagbody
        self.lcomment = False   #indicating the scanner is not in the commented line
        self.bcomment = False   #indicating the scanner is not in the commented block
        self.pragma = False #indicating the scanner is in the openacc pragma line
        self.nopenbrac = 0 #the scanner is in the 0 { bracket
        self.pendingpragma = 0    #the scanner is looking for a pragma boundry. start point '{'
        self.pragmastack = [] #the stack of pragma depths. indicating where the terminating '}' is a pragma region end
        self.closebrac = 0 # number of closing brackets if we reach the end of statement
        self.pendingloop = 0
        self.loopstack = [] # the stack of for-loop depths. indicating where the terminating '}' is a for-loop region end
        self.unifiedstack = [] # the stack of for-loop/prgma depths. indicating where the terminating '}' is a for-loop/pragma region end
        self.nopenpran = 0 # the number of opened paranteces
        self.inquota = False
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
        self.plastchar = self.lastchar
        if self.findex<len(self.fcontent):
            self.lastchar = self.fcontent[self.findex]
            self.findex+=1
        else:
            self.lastchar=''

    def temp_read(self):
        self.tagbodytemp = self.tagbodytemp+self.lastchar
        self.plastchar = self.lastchar
        if self.findex<len(self.fcontent):
            self.lastchar = self.fcontent[self.findex]
            self.findex+=1
        else:
            self.lastchar=''

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
            if (directive=="kernels" or directive=="data" or directive=="loop" or directive=="cache" or directive=="atomic"):
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
            text=text+"//end of pragma\n"
        #text="</pragma>"
        self.printi(text)
    def dump_endoffor(self):
        self.poptag()
        text="}"
        if DEBUG==1:
            text=text+"//end of for\n"
        #text="</pragma>"
        self.printi(text)

    def labeling(self):
        loopid=1
        linefeed=False
        while self.lastchar:
            #print self.lastchar
            #if self.lastchar=='\\' and self.lcomment==False and self.bcomment==False and self.inquota==False:
            #    # ignore next \n
            #    self.temp_read()
            #    if self.lastchar=='\n' or self.lastchar=='\r':
            #        self.temp_clear()
            #    else:
            #        self.temp_append()
            if self.lastchar=='/' and self.lcomment==False and self.bcomment==False and self.inquota==False:
                #potentially comment
                self.temp_read()
                #self.temp_read()
                if self.lastchar=='/':
                    #line comment
                    if DEBUG==1: print "<linecomment>"
                    self.lcomment=True
                    self.temp_read()
                elif self.lastchar=='*':
                    #block comment
                    if DEBUG==1: print "<blockcomment>"
                    self.bcomment=True
                    self.temp_read()
                else:
                    self.temp_append()
            elif self.lastchar=='\n' and self.bcomment==False and self.inquota==False:
                if self.lcomment==True:
                    #line termination
                    if DEBUG==1: print "</linecomment>"
                    self.lcomment=False
                    self.temp_append()
                elif self.pragma==True:
                    #pragma termination
                    self.poptag()
                    self.pragma=False
                self.read()
            elif self.lastchar=='*' and self.bcomment==True and self.lcomment==False and self.inquota==False:
                #potentially block comment end
                self.temp_read()
                #self.read()
                if self.lastchar=='/':
                    #block comment end
                    if DEBUG==1: print "</blockcomment>"
                    self.bcomment=False
                    self.temp_read()
                    self.temp_append()
                    #self.temp_clear()
                else:
                #    self.temp_append()
                    self.temp_read()
            elif (self.lastchar=='#' and self.lcomment==False and self.bcomment==False and self.inquota==False):
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
                                                    self.temp_clear()
                                                    self.poptag()
                                                    self.pragma=True
                                                    broken=0
                if broken==1:
                    self.temp_append()
            elif ((not(self.plastchar.isalpha() or self.plastchar.isdigit())) and self.lastchar=='f' and self.lcomment==False and self.bcomment==False and self.inquota==False):
                #potentially for loop
                broken=1
                self.temp_read()
                #self.temp_ignorewst()
                if self.lastchar=='o':
                    self.temp_read()
                    if self.lastchar=='r':
                        self.temp_read()
                        if not((self.plastchar.isalpha() or self.plastchar.isdigit())):
                            broken=0
                            self.temp_append()
                            self.read()
                            if DEBUG==1:
                                self.tagbody=self.tagbody+'/*forloop'+str(loopid)+'*/\n'
    
                            while self.lastchar==' ' or self.lastchar=='\t' or self.lastchar=='\n':
                                self.read()
                            depth=self.nopenpran
                            while True:
                                t=self.lastchar
                                if   self.lastchar=='(' and self.lcomment==False and self.bcomment==False:
                                    depth=depth+1
                                    self.read()
                                elif self.lastchar==')' and self.lcomment==False and self.bcomment==False:
                                    depth=depth-1
                                    self.read()
                                elif self.lastchar=='\n' and self.lcomment==True:
                                    self.lcomment=False
                                    self.read()
                                elif self.lastchar=='*' and self.bcomment==True:
                                    self.read()
                                    if self.lastchar=='/':
                                        self.bcomment=False
                                        self.read()
                                elif self.lastchar=='/' and self.lcomment==False and self.bcomment==False:
                                    self.read()
                                    if self.lastchar=='*':
                                        self.bcomment=True
                                        self.read()
                                    elif self.lastchar=='/':
                                        self.lcomment=True
                                        self.read()
                                else:
                                    self.read()
                                if ((t==')' and depth==self.nopenpran) or self.lastchar==''):
                                    break
                            #print self.lastchar
                            while self.lastchar==' ' or self.lastchar=='\t' or self.lastchar=='\n':
                                self.read()
                            if self.lastchar!='{':
                                self.pendingloop=self.pendingloop+1
                                self.tagbody=self.tagbody+'{//forloop'+str(loopid)+'\n'
                            loopid+=1
                if broken==1:
                    self.temp_append()
                    
            elif (self.lastchar=='(' and self.lcomment==False and self.bcomment==False and self.inquota==False):
                self.nopenpran = self.nopenpran + 1
                self.read()
            elif (self.lastchar==')' and self.lcomment==False and self.bcomment==False and self.inquota==False):
                self.nopenpran = self.nopenpran - 1
                if self.nopenpran<0:
                    self.error("unbalanced number of paranteces");
                self.read()
            elif (self.lastchar=='"' and self.plastchar!='\\' and self.lcomment==False and self.bcomment==False):
                self.inquota=not self.inquota 
                self.read()
            elif (self.lastchar=='{' and self.lcomment==False and self.bcomment==False and self.inquota==False):
                self.nopenbrac = self.nopenbrac+1
                while True:
                    if self.pendingpragma>0:
                        # start of pragma boundary
                        self.unifiedstack.append(self.nopenbrac)
                        self.pragmastack.append(self.nopenbrac)
                        self.pendingpragma = self.pendingpragma - 1
                    elif self.pendingloop>0:
                        # start of the loop
                        self.unifiedstack.append(self.nopenbrac)
                        self.loopstack.append(self.nopenbrac)
                        self.pendingloop = self.pendingloop - 1
                    else:
                        break
                self.read()
            elif (self.lastchar=='}' and self.lcomment==False and self.bcomment==False and self.inquota==False):
                # potentially end of the loop
                self.read()
                while True:
                    # handle matching regions
                    if len(self.unifiedstack)>0 and len(self.pragmastack)>0 and self.pragmastack[len(self.pragmastack)-1]==self.nopenbrac :
                        # end of the pragma
                        self.dump_endofpragma()
                        self.pragmastack.pop()
                        self.unifiedstack.pop()
                    elif len(self.unifiedstack)>0 and len(self.loopstack)>0 and self.loopstack[len(self.loopstack)-1]==self.nopenbrac :
                        # end of the for-loop
                        self.dump_endoffor()
                        self.loopstack.pop()
                        self.unifiedstack.pop()
                    else:
                        break
                # update bracket tracking
                self.nopenbrac = self.nopenbrac-1
                if self.nopenbrac<0:
                    self.error("unbalanced number of paranteces");
                # handle carried statements
                # closing one-statement pragmas/for-loops
                while True:
                    if len(self.unifiedstack)>0 and len(self.pragmastack)>0 and self.pragmastack[len(self.pragmastack)-1]==self.nopenbrac :
                        # end of the pragma
                        self.dump_endofpragma()
                        self.pragmastack.pop()
                        self.unifiedstack.pop()
                        self.closebrac = self.closebrac - 1
                    elif len(self.unifiedstack)>0 and len(self.loopstack)>0 and self.loopstack[len(self.loopstack)-1]==self.nopenbrac :
                        # end of the for-loop
                        self.dump_endoffor()
                        self.loopstack.pop()
                        self.unifiedstack.pop()
                        self.closebrac = self.closebrac - 1
                    else:
                        if DEBUG==1:
                            self.tagbody+='// this is '+str(self.nopenbrac)+' and the size of unifiedstack is '+str(len(self.unifiedstack))+'\n'
                            self.tagbody+=(('// forloop waits for '+str(self.loopstack[len(self.loopstack)-1])+'\n') if len(self.loopstack)>0 else '// no loop pending\n')
                            self.tagbody+=(('// pragma  waits for '+str(self.pragmastack[len(self.pragmastack)-1])+'\n') if len(self.pragmastack)>0 else '// no pragma pending\n')
                        break
#                    if len(self.pragmastack)>0 and self.pragmastack[len(self.pragmastack)-1]==self.nopenbrac:
#                        # end of the pragma
#                        self.dump_endofpragma()
#                        self.pragmastack.pop()
#                        self.closebrac = self.closebrac - 1
#                    else:
#                        break

            elif (self.lastchar==';' and self.closebrac>0 and self.nopenpran==0 and self.lcomment==False and self.bcomment==False and self.inquota==False):
                self.read()
                while True:
                    if len(self.unifiedstack)>0 and len(self.pragmastack)>0 and self.pragmastack[len(self.pragmastack)-1]==self.nopenbrac :
                        # end of the pragma
                        self.dump_endofpragma()
                        self.pragmastack.pop()
                        self.unifiedstack.pop()
                        self.closebrac = self.closebrac - 1
                    elif len(self.unifiedstack)>0 and len(self.loopstack)>0 and self.loopstack[len(self.loopstack)-1]==self.nopenbrac :
                        # end of the for-loop
                        self.dump_endoffor()
                        self.loopstack.pop()
                        self.unifiedstack.pop()
                        self.closebrac = self.closebrac - 1
                    else:
                        break
#                    if len(self.pragmastack)>0 and self.pragmastack[len(self.pragmastack)-1]==self.nopenbrac:
#                        # end of the pragma
#                        self.dump_endofpragma()
#                        self.pragmastack.pop()
#                        self.closebrac = self.closebrac - 1
#                    else:
#                        break

            elif ((self.pendingpragma>0 or self.pendingloop>0) and self.lcomment==False and self.bcomment==False and self.inquota==False):
                # mark to look for closing statement
                if self.pendingpragma>0:
                    self.pendingpragma = self.pendingpragma - 1
                    self.pragmastack.append(self.nopenbrac)
                    self.unifiedstack.append(self.nopenbrac)
                elif self.pendingloop>0:
                    self.pendingloop = self.pendingloop - 1
                    self.loopstack.append(self.nopenbrac)
                    self.unifiedstack.append(self.nopenbrac)
                self.closebrac = self.closebrac + 1
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

# on comment the following line to run the preprocessor in the standalone mode
#test_preprocr()
