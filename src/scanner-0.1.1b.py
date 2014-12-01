from lxml.builder import E
from lxml import etree
import sys

false=0
true=1
DEBUG=0
TOSDTOUT=0

class scanner(object):
    def __init__(self, fname=None, foname=None):
        self.fname = fname  #path to the input c file
        self.fhandle = open(self.fname) #handler to the input c file
        self.foname = foname  #path to the output XML file
        self.fohandle = open(self.foname,'w') #handler to the output XML file
        self.fohandle.write('<scanner version=\'0.1\'>\n') #initial the output XML file
        self.lastchar = self.fhandle.read(1)    #last token character by the scanner, not parsed yet
        self.tagbody = ""   #store the last read characters, soon will be popped as a c, cuda, or acc pragma code
        self.tagbodytemp = ""   #store the last read characters, soon will be appended to tagbody
        self.lcomment = false   #indicating the scanner is not in the commented line
        self.bcomment = false   #indicating the scanner is not in the commented block
        self.pragma = false #indicating the scanner is in the openacc pragma line
        self.nopenbrac = 0 #the scanner is in the 0 { bracket
        self.pendingloop = 0    #the scanner is looking for 0 loop boundry. start point '{' or end point ';'
        self.loopstack = [] #the stack of loop depths. indicating where the terminating '}' is a loop-end
#        self.expectloop = false #when true, indicates the scanner expect a parallel loop, usually immediately after 'pragma acc loop'
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
        return text.replace('<','&lt;')
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
            return true
        else:
            self.error("undefined directive: "+directive)
            return false

    def validity_clause(self, directive, clause):
        # check the validity of clause
        return true
    
#    def expectation(self, directive, clause):
#        if directive=="loop":
#            self.expectloop=true;


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
        if self.pragma==true:
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
            tagtoprint=tagtoprint+"></pragma>"
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
        text="<for initial='"+self.encode(w[0])+"' boundary='"+self.encode(w[1])+"' increment='"+self.encode(w[2])+"' >"
        self.printi(text)
        self.tagbodytemp=""

    def dump_endoffor(self):
        self.poptag()
        text="</for>"
        self.printi(text)

    def labeling(self):
        while self.lastchar:
            #print self.lastchar
            if self.lastchar=='/':
                #potentially comment
                self.read()
                if self.lastchar=='/':
                    #line comment
                    if DEBUG==1: print "line comment >"
                    self.lcomment=true
                    self.read()
                elif self.lastchar=='*':
                    #block comment
                    if DEBUG==1: print "block comment >"
                    self.bcomment=true
                    self.read()
            elif self.lastchar=='\n':
                if self.lcomment==true:
                    #line termination
                    if DEBUG==1: print "< line comment"
                    self.lcomment=false
                    self.read()
                elif self.pragma==true:
                    #pragma termination
                    self.poptag()
                    self.pragma=false
                    self.read()
                else:
                    self.read()
            elif self.lastchar=='*':
                #potentially block comment end
                self.read()
                if self.lastchar=='/':
                    #block comment end
                    if DEBUG==1: print "< block comment"
                    self.bcomment=false
                    self.read()

#            elif (self.lastchar=='#' and self.lcomment==false and self.bcomment==false):
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
#                                                    self.pragma=true

            elif (self.lastchar=='#' and self.lcomment==false and self.bcomment==false):
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
                                                    self.pragma=true
                                                    broken=0
                if broken==1:
                    self.temp_append()

            elif (self.lastchar=='f' and self.lcomment==false and self.bcomment==false):
                #potentially `for` loop
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
                            while true:
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
            elif (self.lastchar=='{' and self.lcomment==false and self.bcomment==false):
                self.nopenbrac = self.nopenbrac+1
                if self.pendingloop>0 :
                    # start of loop boundry
                    self.loopstack.append(self.nopenbrac)
                    self.pendingloop = self.pendingloop - 1
                self.read()
            elif (self.lastchar=='}' and self.lcomment==false and self.bcomment==false):
                # potentially end of the loop
                self.read()
                if len(self.loopstack)>0 and self.loopstack[len(self.loopstack)-1]==self.nopenbrac :
                    # end of the for
                    self.dump_endoffor()
                    self.loopstack.pop()
                # update bracket tracking
                self.nopenbrac = self.nopenbrac-1
                if self.nopenbrac<0:
                    self.error("unbalanced number of paranteces");
            else:
                self.read()
        self.poptag()
        #    sys.stdout.write(self.lastchar)
        #    if self.lastchar=='/':
                
        

J=scanner("vectorAdd4.c","inter.xml")
J.labeling()

k = """
f=open("vectorAdd4.c")
c=f.read(1)

    while True:
        c = f.read(1)
        if c == '/':
            c = f.read(1)
            if c == '/':
                print "Line comment started"
            elif c == '*':
                print "Block comment started"
        if not c:
            print "End of file"
            break
        sys.stdout.write(c)"""

#page = printToken()

#print(etree.tostring(page, pretty_print=True))
