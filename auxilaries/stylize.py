import sys
import os
from optparse import OptionParser

sys.path.extend(['.', '..', './pycparser/'])
from pycparser import c_parser, c_ast, c_generator, parse_file
import tempfile
from subprocess import call, Popen, PIPE
import re

DEBUG=1
TOSDTOUT=0

class uncommentor(object):
    def __init__(self, fname=None, foname=None):
        self.fname = fname  #path to the input c file
        self.fhandle = open(self.fname) #handler to the input c file
        self.foname = foname  #path to the output XML file
        self.fohandle = open(self.foname,'w') #handler to the output XML file
        self.fohandle.write('\n') #initial the output XML file
        self.lastchar = self.fhandle.read(1)    #last token character by the scanner, not parsed yet
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
        self.lastchar = self.fhandle.read(1)

    def temp_read(self):
        self.tagbodytemp = self.tagbodytemp+self.lastchar
        self.plastchar = self.lastchar
        self.lastchar = self.fhandle.read(1)

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
        self.printi(self.tagbody)
        self.tagbody=''

    def labeling(self):
        loopid=1
        while self.lastchar:
            #print self.lastchar
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
            elif self.lastchar=='\n' and self.bcomment==False and self.inquota==False and self.lcomment==True:
                #line termination
                if DEBUG==1: print "</linecomment>"
                self.lcomment=False
                self.temp_clear()
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
#                    self.temp_append()
                    self.temp_clear()
#                    self.read()
                else:
                #    self.temp_append()
                    self.temp_read()
            elif (self.lastchar=='"' and self.plastchar!='\\' and self.lcomment==False and self.bcomment==False):
                self.inquota=not self.inquota 
                self.read()
            elif self.lcomment==True or self.bcomment==True:
                self.temp_read()
            else:
                self.read()
        self.poptag()
        self.terminate()

class fullyBracket(object):
    def __init__(self, fname=None, foname=None):
        self.fname = fname  #path to the input c file
        self.foname = foname  #path to the output c file
        self.fohandle = open(self.foname,'w') #handler to the output c file
        self.fohandle.write('\n') 

    def bracket(self):
        ast = parse_file(self.fname, use_cpp=True)
        generator = c_generator.CGenerator()
        text = generator.visit(ast)
        self.fohandle.write(text)
        self.fohandle.close()

def test_uncommentor():
    parser = OptionParser()
    # pre-process the code and make it suitable for scanner
    parser = OptionParser()
    parser.add_option("-i", "--infile", dest="infnm",
                      help="Path to input C file", metavar="FILE", default="")
    parser.add_option("-o", "--outfile", dest="outfnm",
                      help="Path to output C file", metavar="FILE", default="")

    (options, args) = parser.parse_args()

    if options.infnm=="":
        parser.print_help()
        exit(-1)
    if os.path.isfile(options.infnm):       
        code="#define __attribute__(x)\n"+"#define __asm__(x)\n"+"#define __builtin_va_list int\n"+"#define __const\n"+"#define __restrict\n"+"#define __extension__\n"+"#define __inline__\n"
        f = tempfile.NamedTemporaryFile(delete=False)
        p1 = Popen(["cat", options.infnm], stdout=PIPE)
        p2 = Popen(["cpp", "-E"], stdin=p1.stdout, stdout=PIPE)
        code+=p2.communicate()[0]
        code=re.sub(r'(#\ ).*.(\n)', '', code)
        code=code.strip()
        f.write(code)
        f.close()
#        J=uncommentor(options.infnm,f.name)
#        J.labeling()
        K=fullyBracket(f.name,options.outfnm)
        K.bracket()
        os.remove(f.name)
    else:
        print "preprocessor: file not found: "+options.infnm
        exit(-1)

# on comment the following line to run the preprocessor in the standalone mode
test_uncommentor()
