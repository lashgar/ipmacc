from subprocess import call, Popen, PIPE
import tempfile
import os
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring
import xml

# debugging levels
DEBUG=0
DEBUGST=0
DEBUGDCL=False
DEBUGTEMPLATE=False
DEBUGFWD=False

WARNING=False
# configuration
USEALT2=True

def clean_clause(stmti):
    stmt=' '.join(stmti.split())
    stmt=stmt.replace(', ',',')
    stmt=stmt.replace(' ,',',')
    stmt=stmt.replace('] ',']')
    stmt=stmt.replace(' [','[')
    stmt=stmt.replace(') ',')')
    stmt=stmt.replace(' (','(')
    stmt=stmt.replace(' =','=')
    stmt=stmt.replace('= ','=')
    stmt=stmt.replace('*',' * ')
    return stmt.strip()

def split_words(stmti):
    # words are: word[word] or word(word) or word or alpha/numeric
    stmt=clean_clause(stmti)
    words=[]
    word=''
    idx=0
    opbrac=0
    oppran=0
    opcros=0
    opstrg=False
    opchar=False
    while idx<len(stmt):
        ch=stmt[idx]
        # 
        newword=False
        if   ch=='[':
            opbrac+=1
        elif ch==']':
            opbrac-=1
        elif ch=='(':
            oppran+=1
        elif ch==')':
            oppran-=1
        elif ch=='{':
            opcros+=1
        elif ch=='}':
            opcros-=1
        elif ch=='"':
            opstrg=not opstrg
        elif ch=="'":
            opchar=not opchar
        elif ((idx==(len(stmt)-1)) or ch==';' or ch=='\n' or ch=='\t' or ch==' ' or ch==',' or (ch=='=' and (stmt[idx-1]!='=') and (stmt[idx+1]!='='))) and oppran==0 and opbrac==0 and opcros==0 and (not opchar) and (not opstrg):
            newword=True
        # 
        if newword and word.strip()!='':
            words.append([word.strip(),ch])
            word=''
        else:
            word+=ch
        # 
        idx+=1
    return words

def decomposeWord(vname):
    arr=[] #indices
    name=''
    idx=0
    opbrac=0
    dim=''
    while idx<len(vname):
        ch=vname[idx]
        if ch=='[':
            opbrac+=1
            dim+=ch
        elif ch==']':
            opbrac-=1
            dim+=ch
            if opbrac==0:
                # top-level brac close, array notation
                # dim starts with '[' and ends with ']'
                dim=dim[1:-1]
                arr.append(dim.strip())
                dim=''
        elif opbrac>0:
            dim+=ch
        elif ch=='*':
            arr.append('(dynamic)')
        elif opbrac==0:
            name+=ch
        idx+=1
    return [name.strip(),arr]

def get_variable_size_type(statement):
    if DEBUGST:
        print statement
    type=[]
    types=[]
    varnames=[]
    varsizes=[]
    nextinit=False
    typedecl=True
    vname=''
    vardeclr=False

    words_list=split_words(statement)
    #for [word, sep] in split_words(statement):
    for idx in range(0,len(words_list)):
        [word, sep] = words_list[idx]
        vardeclr= vardeclr or (sep=='=') or ((sep==',' or sep==';' or idx==(len(words_list)-1))and not nextinit) or (word.strip()=='*')
        #vardeclr= (sep=='=') or ((sep==',' or sep==';')and not nextinit) or (word.strip()=='*')
        typedecl= typedecl and not vardeclr
        if DEBUGST:
            print 'separator:'+sep+' word:'+word+' init:'+str(nextinit)+' vardecl:'+str(vardeclr)+' typedecl:'+str(typedecl)
        if typedecl:
            type.append(word)
        if vardeclr:
            vname+=word+' '
        if vname!='' and ((not vardeclr) or sep==',' or sep==';' or sep=='=' or idx==(len(words_list)-1)):
            # flush vname
            [name,arr]=decomposeWord(vname)
            varnames.append(name.strip())
            arr.append('sizeof('+' '.join(type)+')')
            varsizes.append('*'.join(arr))
            types.append(' '.join(type)+('*'*(len(arr)-1)))
            vname=''
            vardeclr=False
        nextinit= sep=='='

    if DEBUGST:
        for i in range(0,len(types)):
            print 'type:('+types[i]+') name:('+varnames[i]+') size:('+varsizes[i]+')'
    return [varnames, types, varsizes]

def statement_parser_selftest():
    #statement='unsigned long long int* a = NULL, b=0, *c=a==3, *  e = NULL , kk[8];'
    statement='unsigned long long int ki [ 12 ] , a = 8, asd = functionCall(10, 9, asd), taghi[3] = {0,1,2} , taghi[ function8(asd, wert) ]= {func(h) , func(g) , s[0]}, *pointer[19][20];'
    #statement='float *a=NULL, *b=NULL, *c=NULL;'
    get_variable_size_type(statement)


class srcML:
    def __init__(self):
        self.oacc_kernelId=0     # number of kernels which are replaced by function calls
        self.code=0
        self.root=0

    def getFunctionNames(self, root):
        fcn_names=[]
        fcn_roots=[]
        for fcn in root.findall(".//function/"):
            ch=fcn.find("name")
            fcn_names.append(ch.text)
            fcn_roots.append(ch)
    #        print ch.text
        return [fcn_names, fcn_roots]

    def getAllText(self, root):
        code=''
        code=root.text or ""
        for ch in root:
            code+=' '+self.getAllText(ch)
        code+=' '+(root.tail or "")
        if DEBUG:
            print 'getall> '+code+' < tag:'+(root.tag or '')+' text:'+(root.text or '')+' tail:'+(root.tail or '')
        return code.strip()

    def cleanVarName(self, vname):
        name=''
        array=''
        v=vname
        v=v.replace(',','')
        v=v.replace('=','')
        v=v.strip()
        if v.find('[')!=-1 and v.find(']')!=-1:
            name=v.split('[')[0]
            array=']'.join(('['+'['.join(v.split('[')[1:])).split(']')[0:-1])+']'
        else:
            name=v
        return [name.strip(), array]

    def getVarDetails(self, root, fname):
        e_vnames=[]
        e_vsizes=[]
        e_vtypes=[]
        vnames=[]
        vtypes=[]
        for fcn in root.findall(".//function/"):
            ch=fcn.find("name")
            if ch.text==fname:
                #<parameter_list>(<param><decl><type>
                if USEALT2:
                    # ALT 2
                    for stm in fcn.findall(".//parameter_list/param/"):
                        for ch in stm.findall(".//decl/"):
                            arg_stmt=self.getAllText(ch).strip()+';'
                            [e_vars, e_types, e_sizes]=get_variable_size_type(arg_stmt)
                            e_vnames+=e_vars
                            e_vsizes+=e_sizes
                            e_vtypes+=e_types
                    decls=fcn.findall(".//decl_stmt/")
                    decls+=root.findall("./decl_stmt")
                    for ch in decls:
                        stmt=self.getAllText(ch).strip()
                        [e_vars, e_types, e_sizes]=get_variable_size_type(stmt)
                        if DEBUGST:
                            print '==== statement: '+stmt
                        e_vnames+=e_vars
                        e_vsizes+=e_sizes
                        e_vtypes+=e_types
                else:
                    # ALT 1
                    decls=fcn.findall(".//decl_stmt/")+fcn.findall(".//parameter_list/param/")
                    for ch in decls:
                        #stmt=self.getAllText(ch).strip()
                        #[e_vars, e_types, e_sizes]=get_variable_size_type(stmt)
                        #if DEBUGST:
                        #    print '==== statement: '+stmt
                        #e_vnames+=e_vars
                        #e_vsizes+=e_sizes
                        #e_vtypes+=e_types
                        type=self.getAllText(ch.find(".//decl/type/")).strip()
                        vlist=ch.findall(".//decl/name/")
                        for v in vlist:
                            [vname,arr]=self.cleanVarName(self.getAllText(v))
                            type+=arr.count('[')*'*'
                            if DEBUG: print 'vname('+type+')> '+vname+(' array '+arr if arr!='' else '')
                            vtypes.append(type.strip())
                            vnames.append(vname.strip())
                break
        # compares old and new:
        if DEBUGST:
            print '== previous detection:'
            print '\tvnames: '+', '.join(vnames)
            print '\tvtypes: '+', '.join(vtypes)
            print '== new      detection:'
            print '\tvnames: '+', '.join(e_vnames)
            print '\tvtypes: '+', '.join(e_vtypes)
        if USEALT2:
            return [e_vnames, e_vtypes]
        else:
            return [vnames, vtypes]

    def getDeclaredVars(self, root):
        vnames=[]
        for v in root.findall(".//decl/name/"):
            [vname,arr]=self.cleanVarName(self.getAllText(v))
            if vname!='':
                vnames.append(vname.strip())
        return vnames

    def getFunctionCalls_(self, root):
        # find the functions called in the root
        fcalls=[]
        for ch in root.findall(".//call/name/"):
            fn=self.getAllText(ch).strip()
            if DEBUG: print 'functionCall> '+fn
            fcalls.append(fn)
        return fcalls

    def findTemplateOverFcn(self, root, fcn):
        if DEBUGTEMPLATE: print 'looking for template definition for '+fcn
        template=''
        for tmpl in root.findall(".//template/"):
            #print 'template> '+self.getAllText(tmpl)
            try:
                nm=tmpl.find("./function/name/")
                if nm.text==fcn:
                    template='template '+self.getAllText(tmpl.find("./parameter_list"))+' '
                    if DEBUGTEMPLATE: print 'template found for '+fcn+' ['+template+']'
                    #exit(-1)
                    break
            except:
                nonFunctionTemplate=True
        return template
    def findDeclsOfFuncs(self, root, undecls, upper_declared, intrinsics):
        # recursively, returns name, prototype, and declration of the function calls listed in undecls
        if DEBUGFWD:
            print '===================================================='
            print 'recursive search for the declaration of these calls: '+', '.join(undecls)
            print tostring(root)

        here_declared=[]
        wcalls=[]
        for fcn in undecls:
            # 0) if it is declared earlier, skip this
            skip_intr=True
            try:
                idx=intrinsics.index(fcn)
            except:
                skip_intr=False
            if skip_intr:
                continue
            skip_decl=False
            for [name, proto, decl] in upper_declared:
                if name==fcn:
                    skip_decl=True
                    break
            if skip_decl:
                continue
            # 1) find fcn
            found=False
            template=self.findTemplateOverFcn(root, fcn)
            for oc in root.findall(".//function/"):
                nm=oc.find("name")
                if nm.text==fcn:
                    # add the function
                    proto =template
                    proto+=self.getAllText(oc.find("./type"))+' '
                    proto+=self.getAllText(oc.find("./name"))+' '
                    proto+=self.getAllText(oc.find("./parameter_list"))+';'
                    decl=template+self.getAllText(oc)
                    here_declared.append([fcn, proto, decl])
                    # find within calls
                    wcalls+=self.getFunctionCalls_(oc)
                    found=True
                    break
            if WARNING and not found:
                print 'Warning: unable to locate the declaration of function called in the region.'
                print '\tfunction name: '+fcn
                #print '\tintrinsics are: '+', '.join(intrinsics)
                #exit(-1)
        # 3) recursively, find the other undeclared calls of here
        lower_declared=[]
        if len(wcalls)>0:
            lower_declared=self.findDeclsOfFuncs(root, wcalls, upper_declared+here_declared, intrinsics)
        # merge all levels
        merged=[]
        for [p1, p2, p3] in lower_declared+here_declared+upper_declared:
            unq=True
            for [r1, r2, r3] in merged:
                if p1==r1:
                    unq=False
                    break
            if unq:
                merged.append([p1, p2, p3])
        return merged
            

    def findDeclsOfTypes(self, root, undecls):
        # returns short and long declration of the undeclared type listed in undecls
        # note: forward declarations in the root are not returned back as declaration
        decls=[] # (name, declaration) pair of all structs
        # first, structs
        for stc in root.findall(".//struct/"):
            try:
                nmroot=stc.find("name")
                blkroot=stc.find("block")
                decl=self.getAllText(stc)
                name=self.getAllText(nmroot)
                block=self.getAllText(blkroot)
                if DEBUGDCL:
                    print 'declaration of "'+name+'" is "'+decl.replace('\n',' ')+'" blk="'+block+'"'
                    #print ('typedef struct '+block+' '+tp+';')
                for tp in undecls:
                    if tp==name:
                        decls.append([tp, 'struct '+tp+';', decl, (('typedef struct '+block+' ')[::-1].replace(';',(';'+tp[::-1]),1)[::-1])])
            except:
                # ignore, its forward declaration
                nf=True
        # second, typedefs
        for tpd in root.findall(".//typedef/"):
            try:
                nmroot=tpd.find("name")
                blkroot=tpd.find("type")
                decl=self.getAllText(tpd)
                name=self.getAllText(nmroot).split()[0]
                block=self.getAllText(blkroot)
                if DEBUGDCL:
                    print 'declaration of "'+name+'" is "'+decl.replace('\n',' ')+'" blk="'+block+'"'
                    #print ('typedef struct '+block+' '+tp+';')
                for tp in undecls:
                    if tp==name:
                        decls.append([tp, 'typedef struct '+tp+';', decl, decl])
            except:
                # ignore, its forward declaration
                nf=True
        # third,  unions
        # fourth, enums
        # fifth,  classes
        # recursively, declare the types which are undeclared in elements of typdefs, structs, and unions 
        return decls

    def prefixFunction(self, root, kernelsParents):
        for id in range(0,len(kernelsParents)):
            found=False
            for tmpl in root.findall(".//template/"):
                #print 'template> '+self.getAllText(tmpl)
                try:
                    nm=tmpl.find("./function/name/")
                    if nm.text==kernelsParents[id]:
                        template='template '+self.getAllText(tmpl.find("./parameter_list/"))+' '
                        try:
                            tmpl.text =' __ipmacc_prototypes_kernels_'+str(id)+' '+tmpl.text
                        except:
                            tmpl.text =' __ipmacc_prototypes_kernels_'+str(id)+' '
                        found=True
                        break
                except:
                    nonFunctionTemplate=True
            if not found:
                for fcn in root.findall(".//function/"):
                    nm=fcn.find("name")
                    if nm.text==kernelsParents[id]:
                        try:
                            fcn.text+=' __ipmacc_prototypes_kernels_'+str(id)+' '
                        except:
                            fcn.text =' __ipmacc_prototypes_kernels_'+str(id)+' '


#        for fcn in root.findall(".//function/"):
#            nm=fcn.find("name")
#            for id in range(0,len(kernelsParents)):
#                if nm.text==kernelsParents[id]:
#                    try:
#                        fcn.text+=' __ipmacc_prototypes_kernels_'+str(id)+' '
#                    except:
#                        fcn.text =' __ipmacc_prototypes_kernels_'+str(id)+' '

        return self.XMLtocode(root)

    def findVarSize(self, root, fname, vname):
        e_vnames=[]
        e_vsizes=[]
        e_vtypes=[]
        if DEBUG:
            print 'Looking for the size of '+vname+' in following XML'
            print '============'
            print tostring(root)
        for fcn in root.findall(".//function/"):
#            found=False
            parent=fcn.find("name").text
#            for ch in fcn.findall(".//call/name"):
#                fn=self.getAllText(ch).strip()
            if parent==fname:
#                found=True
#                break
#            if found:
                #print 'function found!'
                if USEALT2:
                    # ALT 2
                    for stm in fcn.findall(".//parameter_list/param/"):
                        for ch in stm.findall(".//decl/"):
                            arg_stmt=self.getAllText(ch).strip()+';'
                            [e_vars, e_types, e_sizes]=get_variable_size_type(arg_stmt)
                            e_vnames+=e_vars
                            e_vsizes+=e_sizes
                            e_vtypes+=e_types
                    decls=fcn.findall(".//decl_stmt/")
                    decls+=root.findall("./decl_stmt/")
                    for ch in decls:
                        stmt=self.getAllText(ch).strip()
                        [e_vars, e_types, e_sizes]=get_variable_size_type(stmt)
                        if DEBUGST:
                            print '==== statement: '+stmt
                        e_vnames+=e_vars
                        e_vsizes+=e_sizes
                        e_vtypes+=e_types
                    e_size=''
                    for idx in range(0,len(e_vnames)):
                        if vname==e_vnames[idx]:
                            e_size=e_vsizes[idx]
                            return e_size
                else:
                    # ALT 1
                    decls=fcn.findall(".//decl_stmt/")+fcn.findall(".//parameter_list/param/")
                    for ch in decls:
                        # go through all declarations
                        vlist=ch.findall(".//decl/name/")
                        for v in vlist:
                            # check all variable names declared in this statemet
                            [vn,arr]=self.cleanVarName(self.getAllText(v))
                            if vn==vname:
                                # here we found the variable
                                if DEBUG: print '============'
                                if DEBUG: print tostring(ch)
                                type=self.getAllText(ch.find(".//decl/type/")).strip()
                                nDynDims=type.count('*')
                                dims=[]
                                for dim in ch.findall(".//decl/name/index/"):
                                    if DEBUG:
                                        print 'dim > '+self.getAllText(dim)
                                        print 'size >'+' ('+self.getAllText(dim).replace('[','',1)[::-1].replace(']','',1)[::-1].strip()+')'
                                    dims.append('('+self.getAllText(dim).replace('[','',1)[::-1].replace(']','',1)[::-1].strip()+')')
                                if nDynDims>0:
                                    for kk in range(0,nDynDims):
                                        dims.append('(dynamic)')
                                    if DEBUG: print 'dynDims > '+str(nDynDims)
                                dims.append('sizeof('+type.replace('*','')+')')
                                size='*'.join(dims)
                                if DEBUG: print 'the size of variable:'+vname+' is '+size
                                if DEBUGST:
                                    print '===== VARIABLE SIZE DETECTION '+vname+' == old detection:'+size
                                    print '===== VARIABLE SIZE DETECTION '+vname+' == new detection:'+e_size
                                return size
                            else:
                                if DEBUG:
                                    print '== variable:'+vn+' is ignored'
            else:
                if DEBUG: print 'function:'+fname+' not found!'
        if DEBUG: print '============'
        return ''

    def getFunctionParernt(self, root, fname):
        fcalls=[]
        for fcn in root.findall(".//function/"):
            parent=fcn.find("name").text
            template=self.findTemplateOverFcn(root,parent)
            for ch in fcn.findall(".//call/name/"):
                fn=self.getAllText(ch).strip()
                if DEBUG: print 'functionCall> '+fn
                if fn==fname:
                    return [template,parent]
        return [template,'']

    def getFunctionCalls(self, root, fname):
        fcalls=[]
        for fcn in root.findall(".//function/"):
            ch=fcn.find("name")
            if ch.text==fname:
                for ch in fcn.findall(".//call/name/"):
                    fn=self.getAllText(ch)
                    if DEBUG: print 'functionCall> '+fn
                    fcalls.append(fn)
                break
        return fcalls

    def getAllNames(self, root):
        names=[]
        for nm in root.findall(".//name/"):
            try:
                str=nm.text.strip()
                if DEBUG: print 'new identifier > '+str
                names.append(str)
            except:
                str=''
        return names

#    def getAllTypes(self, root, fname):
#        for fcn in root.findall(".//function"):
#            ch=fcn.find("name")
#            if ch.text==fname:
#                for ch in fcn.findall(".//decl_stmt"):
#                    type=self.getAllText(ch.find(".//decl/type/"))
#                    print 'type> '+type
#                break

    def recursivePrint(self, root, depth):
        print (' '*depth)+root.tag+'<'+str(root.text)+'>'
        for ch in root:
            self.recursivePrint(ch, depth+1)

    def codeToXML(self, code):
        self.code = code
        #root = 0
        f=tempfile.NamedTemporaryFile(suffix='.cpp', delete=False)
        #code='//this is the content\n'
        f.write(code)
        f.close()
        #print f.name
        #fpath='./test.c'
        #g=open(f.name)
        #print '\n'.join(g.readlines())
        #g.close()
        try:
            p1 = Popen([os.path.dirname(os.path.realpath(__file__))+"/../bin/src2srcml", f.name], stdout=PIPE)
        except:
            print 'unable to open src2srcml binary'
            exit(-1)
        #print p1.stdout.read()
        #content='<unit>\n'+'\n'.join(p1.stdout.read().split('\n')[2:])
        content='\n'.join(p1.stdout.read().split('\n')[1:])
        content=content.replace('xmlns=','namsp=')
        #content=p1.stdout.read()
        if DEBUG: print content
        #os.remove(f.name)
        root = ET.fromstring(content)
        if DEBUG: print tostring(root)
        #del root.attrib["xmlns"]
        self.root = root
        return root

    def XMLtocode(self, root):
        self.root = root
        #root = 0
        f=tempfile.NamedTemporaryFile(suffix='.xml', delete=False)
        f.write(tostring(root))
        f.close()
        #print f.name
        #fpath='./test.c'
        #g=open(f.name)
        #print '\n'.join(g.readlines())
        #g.close()
        try:
            p1 = Popen([os.path.dirname(os.path.realpath(__file__))+"/../bin/srcml2src", f.name], stdout=PIPE)
        except:
            print 'unable to open srcml2src binary'
            exit(-1)
        #print p1.stdout.read()
        #content='<unit>\n'+'\n'.join(p1.stdout.read().split('\n')[2:])
        content='\n'.join(p1.stdout.read().split('\n')[1:])
        #content=content.replace('xmlns=','namsp=')
        #content=p1.stdout.read()
        if DEBUG: print content
        #os.remove(f.name)
        #root = ET.fromstring(content)
        #if DEBUG: print tostring(root)
        #del root.attrib["xmlns"]
        #self.root = root
        return content


def srcml_code2xml(code):
    srcml_sample = srcML()
    if DEBUG:
        print 'HERE:'
        tostring(srcml_sample.codeToXML(code))
        print '2HERE:'
    return srcml_sample.codeToXML(code)

def srcml_get_parent_fcn(root, func):
    srcml_sample = srcML()
#    root=srcml_sample.codeToXML(code)
    return srcml_sample.getFunctionParernt(root, func)

def srcml_get_fcn_calls(root):
    srcml_sample = srcML()
    return srcml_sample.getFunctionCalls_(root)
    
def srcml_get_var_details(root, fcn):
    srcml_sample = srcML()
    [vnames, vtypes]=srcml_sample.getVarDetails(root,fcn)
    return [vnames, vtypes]

def srcml_get_all_ids(root):
    srcml_sample = srcML()
    return srcml_sample.getAllNames(root)

def srcml_get_declared_vars(root):
    srcml_sample = srcML()
    return srcml_sample.getDeclaredVars(root)

def srcml_find_var_size(root, funcName, varName):
    srcml_sample = srcML()
    return srcml_sample.findVarSize(root, funcName, varName)

def srcml_get_fwdecls(code, undeclsTypes, undeclsFuncs, intrinsics):
    # undeclsTypes: types which are used, but not declared on accelerator
    # undeclsFuncs: functions which are called, but not declared on accelerator
    srcml_sample = srcML()
    root=srcml_sample.codeToXML(code)
    declFuncs=srcml_sample.findDeclsOfFuncs(root, undeclsFuncs, [], intrinsics)
    declTypes=srcml_sample.findDeclsOfTypes(root, undeclsTypes)
    return [declTypes, declFuncs]

def srcml_prefix_functions(code, funcs):
    srcml_sample = srcML()
    root=srcml_sample.codeToXML(code)
    code=srcml_sample.prefixFunction(root, funcs)
    return code


def srcml_selftest():
    srcml_sample = srcML()
    #print tostring(srcml_sample.codeToXML('int main(){\n}\n'))
    root=srcml_sample.codeToXML('int main(){\n}\n')
    #print 'ast root:'
    #srcml_sample.recursivePrint(root, 0)
    #
    [fnames, froots]=srcml_sample.getFunctionNames(root)
    for fcn in fnames:
        print 'function names: '+fcn
        [vnames, vtypes]=srcml_sample.getVarDetails(root,fcn)
        fcalls=srcml_sample.getFunctionCalls(root,fcn)

