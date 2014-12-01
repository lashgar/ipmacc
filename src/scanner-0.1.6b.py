from lxml.builder import E
from lxml import etree
import sys
import os
import xml.etree.ElementTree as ET
import tempfile

from optparse import OptionParser

sys.path.extend(['.', '..', './pycparser/'])
from pycparser import c_parser, c_ast
from preprocessor import preprocr

DEBUG=0
TOSDTOUT=0

class scanner(object):
    def __init__(self, fname=None, foname=None):
        self.fname = fname  #path to the input c file
        self.fhandle = open(self.fname) #handler to the input c file
        self.foname = foname  #path to the output XML file
        self.fohandle = open(self.foname,'w') #handler to the output XML file
        self.fohandle.write('<scanner version=\'0.1.6b\'>\n') #initial the output XML file
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
    
    def decode(self, text):
        return text.replace('&amp;','&').replace('&gt;','>').replace('&lt;','<')
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

    def removeall(self, str, occ):
        cp=str
        for i in occ:
            cp=cp.replace(i,'')
        return cp

    def dump_forloop(self):
        a=self.tagbodytemp[1:len(self.tagbodytemp)-1]
        w=a.split(';')
#        text="<for statement='"+self.tagbodytemp+"'>"
        f_initial=self.encode(w[0]).split('=')[1].strip()
        f_condition=self.encode(w[1])
        f_iterator=self.encode(w[0]).split('=')[0].strip()
        f_incrementor=self.encode(w[2])

        [afc_flag, f_i, f_expr] = self.analyze_forloop_condition(self.decode(f_iterator.strip()), self.pycparser_getAstTree(self.decode(f_condition)))
        f_terminate=self.removeall(f_expr, ['<=', '>=', '<', '>', self.decode(f_iterator)])
        print '===condition=='+str(f_i)+' '+f_terminate+(' with ambiguity!' if afc_flag else '')
        [itcount, afi_flag, operator, step] = self.analyze_forloop_step(self.decode(f_iterator.strip()), self.pycparser_getAstTree(self.decode(f_incrementor)), 0)
        print '===increment=='+' op:'+str(operator)+' code:'+step+(' with ambiguity!' if itcount>1 or afi_flag else '')
        
        text="<for"
        text=text+" initial='"+self.encode(w[0])+"'"
        text=text+" init='"+f_initial+"' boundary='"+f_condition+"' "
        text=text+" increment='"+f_incrementor+"'"+" iterator='"+f_iterator+"' "
        text=text+" terminate='"+f_terminate+"'"+" incstep='"+step+"' incoperator='"+operator+"' "
        text=text+">"
 


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
    
    # `for` loop analyzers


    def pycparser_getAstTree(self,statement):
        text='int main(){\n'+statement+';\n}'
        #print text
        # create a pycparser
        parser = c_parser.CParser()
        ast = parser.parse(text, filename='<none>')
        # generate the XML tree
        #ast.show()
        codeAstXml = open('code_ast.xml','w')
        ast.showXml(codeAstXml)
        codeAstXml.close()
        tree = ET.parse('code_ast.xml')
        os.remove('code_ast.xml')
        root = tree.getroot()
        return root.find(".//FuncDef/Compound")

    def is_arithmc_op(self,opt):
        list=['+', '-', '*', '/', '%']
        try:
            list.index(opt)
            return True
        except:
            return False

    def is_compare_op(self,opt):
        list=['<', '>', '>=', '<=']
        try:
            list.index(opt)
            return True
        except:
            return False

    def is_logical_op(self,opt):
        list=['&&', '||']
        try:
            list.index(opt)
            return True
        except:
            return False
    def analyze_forloop_condition(self,iterator,root):
        if root.tag.strip()=='ID':
            return [False, (True if iterator==root.get('uid').strip() else False), root.get('uid').strip()]
        elif root.tag.strip()=='Constant':
            return [False, False, root.get('uid').split(',')[-1].strip()]
        code=''
        flag=False  # indicator whether expression contains iterator
        ambig=False # indicator of ambiguity in loop boundary detection
        if root.tag.strip()=='BinaryOp':
            [am1, cr1, op1]=self.analyze_forloop_condition(iterator,root[0])
            opt=root.get('uid')
            [am2, cr2, op2]=self.analyze_forloop_condition(iterator,root[1])
            #print '('+str(cr1)+','+op1+')'+' '+opt+' '+'('+str(cr2)+','+op2+')'
            if self.is_arithmc_op(opt) or (self.is_logical_op(opt) and ((cr1 and cr2)or(not(cr1) and not(cr2)))):
                # pass arithmetic operators
                code='('+op1+opt+op2+')'
                flag=cr1 or cr2
            elif self.is_logical_op(opt):
                # put non-effective element
                code='('+(op1 if cr1 else op2)+')'
                flag=cr1 or cr2
            elif self.is_compare_op(opt) and (cr1 or cr2):
                # loop terminating condition
                code='('+op1+opt+op2+')'
                flag=True
            elif cr1:
                code=op1
                flag=True
            elif cr2:
                code=op2
                flag=True
            ambig = am1 or am2 or (cr1 and cr2)
        else:
            for it in root:
                [am, cr, cd] = self.analyze_forloop_condition(iterator, it)
                code=code+'('+cd+')'
                flag=flag or cr
                ambig=ambig or am
        return [ambig, flag, code]

    def is_pp_op(self,opt):
        list=['++', 'p++']
        try:
            list.index(opt)
            return True
        except:
            return False

    def is_mm_op(self,opt):
        list=['--', 'p--']
        try:
            list.index(opt)
            return True
        except:
            return False

    def analyze_forloop_step(self,iterator, root, dep):
        ambig=0 # counter of the number of appearences of iterator
        flag=False  # indicator of whether the expression has ambiguity or not
        op=''
        code=''
        if root.tag.strip()=='ID':
            code=root.get('uid').strip()
            ambig=(1 if code==iterator else 0)
        elif root.tag.strip()=='Constant':
            code=root.get('uid').split(',')[-1].strip()
        elif root.tag.strip()=='UnaryOp':
            if self.is_pp_op(root.get('uid').strip()) and root[0].get('uid').strip()==iterator:
                op='+'
                code='1'
            elif self.is_mm_op(root.get('uid').strip()) and root[0].get('uid').strip()==iterator:
                op='-'
                code='1'
            else:
                # ambiguity
                flag=True
        elif root.tag.strip()=='BinaryOp' and (root[0].get('uid').strip()==iterator or root[1].get('uid').strip()==iterator):
            if root[0].get('uid').strip()==iterator:
                op=root.get('uid')
                [ambig, flag, op1, code] = self.analyze_forloop_step(iterator, root[1], dep+1)
            elif root[1].get('uid').strip()==iterator:
                op=root.get('uid')
                [ambig, flag, op2, code] = self.analyze_forloop_step(iterator, root[0], dep+1)
        elif root.tag.strip()=='BinaryOp':
            [ambig1, flag1, op1, code1] = self.analyze_forloop_step(iterator, root[0], dep+1)
            [ambig2, flag2, op2, code2] = self.analyze_forloop_step(iterator, root[1], dep+1)
            ambig = ambig + ambig1 + ambig2
            flag = True
            op = op+op1+op2
            code = code+code2+root.get('uid').strip()+code1
        elif root.tag.strip()=='Assignment':
            if root[0].get('uid')==iterator:
                [ambig, flag, op, code] = self.analyze_forloop_step(iterator, root[1], dep+1)
            else:
                flag=True
        else:
            for it in root:
                [ambig1, flag1, op1, code1] = self.analyze_forloop_step(iterator, it, dep+1)
                ambig = ambig + ambig1
                flag = flag or flag1
                op = op+op1
                code = code+code1
        return [ambig, flag, op, code] 



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
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(" ")
    f.close()

    K=preprocr(options.filename,f.name)
    K.labeling()

    J=scanner(f.name,"__inter.xml")
    J.labeling()
    os.remove(f.name)
else:
    print "scanner: file not found: "+options.filename
    exit(-1)
