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
DEBUGKA=False
DEBUGDETAILPROC=False
KAVERBOSE=False

WARNING=False
# configuration
USEALT2=True

import re

def string_found(string1, string2):
    # check whether string1 has string2 as the destination of write or not
    #print 'string1 > '+string1
    #print 'string2 > '+string2

    if(string2.find('=')==-1):
        return False
    else:
        destin=string2.split('=')[0]
        if re.search(r"\b" + re.escape(string1) + r"\b", destin):
        #if(destin.find(string1)!=-1):
            return True
        else:
            return False

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
                if dim=='':
                    arr.append('(dynamic)')
                else:
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
            # name 
            varnames.append(name.strip())
            # type 
            clearType=''
            for mT in type: #.strip().split():
                 if mT!='static': # filter out keywords
                     clearType+=mT+' '
            types.append((clearType+('*'*(len(arr)))).strip())
            #types.append(' '.join(type)+('*'*(len(arr)-1)))
            # size 
            #arr.append('sizeof('+' '.join(type)+')')
            arr.append('sizeof('+clearType+')')
            varsizes.append(('*'.join(arr)).strip())
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
        for fcn in root.findall(".//function"):
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

    def getVarDetails_core(self, fcn, root):
        e_vnames=[]
        e_vsizes=[]
        e_vtypes=[]
        vnames=[]
        vtypes=[]
        if USEALT2:
            # ALT 2
            for stm in fcn.findall(".//parameter_list/param") + fcn.findall(".//for"):
                for ch in stm.findall(".//decl"):
                    arg_stmt=self.getAllText(ch).strip()+';'
                    #print arg_stmt
                    [e_vars, e_types, e_sizes]=get_variable_size_type(arg_stmt)
                    e_vnames+=e_vars
                    e_vsizes+=e_sizes
                    e_vtypes+=e_types
            decls=fcn.findall(".//decl_stmt") #local variables
            if tostring(fcn).strip()=='<dummy />':
                decls+=root.findall(".//decl_stmt") #get all variables you see
                decls+=root.findall(".//decl") #get all variables you see
                # print tostring(root)
                # print len(decls)
            else:
                decls+=root.findall("./decl_stmt") #global variables
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
            decls=fcn.findall(".//decl_stmt")+fcn.findall(".//parameter_list/param")
            for ch in decls:
                #stmt=self.getAllText(ch).strip()
                #[e_vars, e_types, e_sizes]=get_variable_size_type(stmt)
                #if DEBUGST:
                #    print '==== statement: '+stmt
                #e_vnames+=e_vars
                #e_vsizes+=e_sizes
                #e_vtypes+=e_types
                type=self.getAllText(ch.find(".//decl/type")).strip()
                vlist=ch.findall(".//decl/name")
                for v in vlist:
                    [vname,arr]=self.cleanVarName(self.getAllText(v))
                    type+=arr.count('[')*'*'
                    if DEBUG: print 'vname('+type+')> '+vname+(' array '+arr if arr!='' else '')
                    # clear up the type from keywords like `static`
                    clearType=''
                    for mT in type.strip().split():
                         if mT!='static':
                             clearType+=mT+' '
                    vtypes.append(clearType.strip())
                    vnames.append(vname.strip())
        return [e_vnames, e_vsizes, e_vtypes, root, vnames, vtypes] 

    def getVarDetails(self, root, fname):
        if fname=='':
            [e_vnames, e_vsizes, e_vtypes, root, vnames, vtypes] = self.getVarDetails_core(ET.Element('dummy'), root)
        else:
            for fcn in root.findall(".//function"):
                ch=fcn.find("name")
                if ch.text==fname:
                    [e_vnames, e_vsizes, e_vtypes, root, vnames, vtypes] = self.getVarDetails_core(fcn, root)
                    # #<parameter_list>(<param><decl><type>
                    # if USEALT2:
                    #     # ALT 2
                    #     for stm in fcn.findall(".//parameter_list/param") + fcn.findall(".//for"):
                    #         for ch in stm.findall(".//decl"):
                    #             arg_stmt=self.getAllText(ch).strip()+';'
                    #             #print arg_stmt
                    #             [e_vars, e_types, e_sizes]=get_variable_size_type(arg_stmt)
                    #             e_vnames+=e_vars
                    #             e_vsizes+=e_sizes
                    #             e_vtypes+=e_types
                    #     decls=fcn.findall(".//decl_stmt") #local variables
                    #     decls+=root.findall("./decl_stmt") #global variables
                    #     for ch in decls:
                    #         stmt=self.getAllText(ch).strip()
                    #         [e_vars, e_types, e_sizes]=get_variable_size_type(stmt)
                    #         if DEBUGST:
                    #             print '==== statement: '+stmt
                    #         e_vnames+=e_vars
                    #         e_vsizes+=e_sizes
                    #         e_vtypes+=e_types
                    # else:
                    #     # ALT 1
                    #     decls=fcn.findall(".//decl_stmt")+fcn.findall(".//parameter_list/param")
                    #     for ch in decls:
                    #         #stmt=self.getAllText(ch).strip()
                    #         #[e_vars, e_types, e_sizes]=get_variable_size_type(stmt)
                    #         #if DEBUGST:
                    #         #    print '==== statement: '+stmt
                    #         #e_vnames+=e_vars
                    #         #e_vsizes+=e_sizes
                    #         #e_vtypes+=e_types
                    #         type=self.getAllText(ch.find(".//decl/type")).strip()
                    #         vlist=ch.findall(".//decl/name")
                    #         for v in vlist:
                    #             [vname,arr]=self.cleanVarName(self.getAllText(v))
                    #             type+=arr.count('[')*'*'
                    #             if DEBUG: print 'vname('+type+')> '+vname+(' array '+arr if arr!='' else '')
                    #             # clear up the type from keywords like `static`
                    #             clearType=''
                    #             for mT in type.strip().split():
                    #                  if mT!='static':
                    #                      clearType+=mT+' '
                    #             vtypes.append(clearType.strip())
                    #             vnames.append(vname.strip())
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
        for v in root.findall(".//decl/name"):
            [vname,arr]=self.cleanVarName(self.getAllText(v))
            if vname!='':
                vnames.append(vname.strip())
        return vnames

    def getFunctionCalls_(self, root):
        # find the functions called in the root
        fcalls=[]
        for ch in root.findall(".//call/name"):
            fn=self.getAllText(ch).strip()
            if DEBUG: print 'functionCall> '+fn
            fcalls.append(fn)
        return fcalls

    def findTemplateOverFcn(self, root, fcn):
        if DEBUGTEMPLATE: print 'looking for template definition for '+fcn
        template=''
        for tmpl in root.findall(".//template"):
            #print 'template> '+self.getAllText(tmpl)
            try:
                nm=tmpl.find("./function/name")
                if nm.text==fcn:
                    template='template '+self.getAllText(tmpl.find("./parameter_list"))+' '
                    if DEBUGTEMPLATE: print 'template found for '+fcn+' ['+template+']'
                    #exit(-1)
                    break
            except:
                nonFunctionTemplate=True
        return template

    def findActiveTypesRecursively(self, root, calls, upper_declared, intrinsics):
        # recursively, returns name, prototype, and declration of the function calls listed in undecls
        if DEBUGFWD:
            print '===================================================='
            print 'recursive search for types within these calls: '+', '.join(calls)
            print tostring(root)

        here_declared=[]
        wcalls=[]
        for fcn in calls:
            # 0) if it is declared earlier, skip this
            skip_intr=True
            try:
                idx=intrinsics.index(fcn)
            except:
                skip_intr=False
            if skip_intr:
                continue
            skip_row =False
            for name in upper_declared:
                if name==fcn:
                    skip_row =True
                    break
            if skip_row:
                continue
            # 1) find fcn
            found=False
            template=self.findTemplateOverFcn(root, fcn)
            for oc in root.findall(".//function"):
                nm=oc.find("name")
                if nm.text==fcn:
                    # add the function
                    [vnamelist, vtypelist] = self.getVarDetails(root, fcn)
                    here_declared += vtypelist
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
        wcalls = list(set(wcalls))
        if len(wcalls)>0:
            lower_declared=self.findActiveTypesRecursively(root, wcalls, upper_declared+here_declared, intrinsics)
        return list(set(lower_declared+here_declared+upper_declared))

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
            for [tmp_name, tmp_proto, tmp_decl, tmp_rettype, tmp_qualifiers, tmp_params, tmp_local_vars, tmp_scope_vars, tmp_fcalls, tmp_ids, tmp_ex_params] in upper_declared:
                if tmp_name==fcn:
                    skip_decl=True
                    break
            if skip_decl:
                continue
            # 1) find fcn
            found=False
            template=self.findTemplateOverFcn(root, fcn)
            for oc in root.findall(".//function"):
                nm=oc.find("name")
                # print tostring(root)
                if nm.text==fcn:
                    #print tostring(root)
                    # get details about the function 
                    det_qualifiers = []
                    for qlf in oc.find("./type").findall(".//name"):
                        det_qualifiers.append(self.getAllText(qlf))
                    det_rettype = det_qualifiers[-1]
                    det_params_v = []
                    det_params_t = []
                    det_params_s = []
                    #print tostring(oc)
                    for prm in self.getAllText(oc.find("./parameter_list"))[1:-1].strip().split(','):
                        if len(prm.split())>0:
                            #det_params_t.append(' '.join(prm.split()[0:-1]).strip())
                            #det_params_v.append(prm.split()[-1].strip())
                            [e_vars, e_types, e_sizes]=get_variable_size_type(prm+';')
                            #print prm+'> '
                            #print e_vars
                            #print e_types
                            #print e_sizes
                            det_params_t+=e_types
                            det_params_v+=e_vars
                            det_params_s+=e_sizes
                    [det_scope_vlist, det_scope_tlist] = self.getVarDetails(root, fcn)
                    det_scope_slist = ['']*len(det_scope_vlist)
                    det_local_vlist = []
                    det_local_tlist = []
                    det_local_slist = []
                    det_local_vlist += det_params_v
                    det_local_tlist += det_params_t
                    det_local_slist += det_params_s
                    for tmp_ch in oc.findall(".//decl_stmt")+oc.findall(".//for/init"): #local variables
                        stmt=self.getAllText(tmp_ch).strip()
                        [e_vars, e_types, e_sizes]=get_variable_size_type(stmt)
                        if DEBUGST:
                            print '==== statement: '+stmt
                        det_local_vlist+=e_vars
                        det_local_tlist+=e_types
                        det_local_slist+=e_sizes
                    det_fcalls = self.getFunctionCalls_(oc)
                    det_ids = self.getAllNames(oc)
                    det_global_vars = 1 #ids - declared_in_body - declared_in_params - calls - keywords
                    if DEBUGDETAILPROC:
                        print '=================='
                        print 'fcn name> '+fcn
                        print 'qualifiers> '+', '.join(det_qualifiers[0:-1])
                        print 'return type> '+det_rettype
                        print 'call args name> '+', '.join(det_params_v)
                        print 'call args type> '+', '.join(det_params_t)
                        print 'call args size> '+', '.join(det_params_s)
                        print 'scope vars > '+', '.join(det_scope_vlist)
                        print 'scope typs > '+', '.join(det_scope_tlist)
                        print 'calls> '+', '.join(det_fcalls)
                        print 'all ids> '+', '.join(det_ids)
                        print 'local vars > '+', '.join(det_local_vlist)
                        print 'local typs > '+', '.join(det_local_tlist)
                    # add the function
                    proto =template
                    proto+=self.getAllText(oc.find("./type"))+' '
                    proto+=self.getAllText(oc.find("./name"))+' '
                    proto+=self.getAllText(oc.find("./parameter_list"))+';'
                    decl=template+self.getAllText(oc)
                    here_declared.append([fcn, proto, decl, det_rettype, det_qualifiers[0:-1], [det_params_t, det_params_v, det_params_s], [det_local_tlist, det_local_vlist, det_local_slist], [det_scope_tlist, det_scope_vlist, det_scope_slist], det_fcalls, det_ids, [[],[],[]]])
                    # find within calls
                    wcalls+=det_fcalls
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
        for [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11] in lower_declared+here_declared+upper_declared:
            unq=True
            for [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11] in merged:
                if p1==r1:
                    unq=False
                    break
            if unq:
                merged.append([p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11])
        return merged


    def findDeclsOfTypes(self, root, undecls, upper_declared, builtintypes, target_platform):
        # returns short and long declration of the undeclared type listed in undecls
        # note: forward declarations in the root are not returned back as declaration
        if DEBUGDCL:
            print 'looking for following undeclared types> '+str(undecls)
        # decls=[] # (name, declaration) pair of all structs
        here_declared=[]
        wtypes=[]
        for [tp, demandingTP] in undecls:
            # tp is the type we are looking for declaration
            # demandingTP is the parent type used tp (in nested case, otherwise it is '')
            # 0) if it is declared earlier, skip this
            skip_builtin=True
            try:
                idx=builtintypes.index(tp)
            except:
                skip_builtin=False
            if skip_builtin:
                continue
            skip_decl=False
            for [name, proto1, decl, proto2, parent] in upper_declared:
                if name.strip()==tp.strip():
                    skip_decl=True
                    break
            if skip_decl:
                continue
            # first, structs
            for stc in root.findall(".//struct"):
                try:
                    # 1) find type
                    nmroot=stc.find("name")
                    blkroot=stc.find("block")
                    decl=self.getAllText(stc)
                    name=self.getAllText(nmroot)
                    block=self.getAllText(blkroot)
                    if DEBUGDCL:
                        self.recursivePrint(stc, 0)
                        print 'declaration of "'+name+'" is "'+decl.replace('\n',' ')+'" blk="'+block+'"'
                        #print ('typedef struct '+block+' '+tp+';')
                    if tp==name:
                        #print 'struct name matched>'
                        if target_platform=='ISPC':
                            curl2curl = decl[decl.find('{'):][::-1]
                            curl2curl = curl2curl[curl2curl.find('}'):][::-1]
                            curl2curl = 'struct '+tp+' '+curl2curl+';\n'
                            here_declared.append([tp, 'struct '+tp+';', curl2curl, curl2curl, demandingTP])
                            #here_declared.append([tp, 'struct '+tp+';', decl, (('struct '+block+' ')[::-1].replace(';',(';'+tp[::-1]),1)[::-1]), demandingTP])
                        else:
                            here_declared.append([tp, 'typedef struct '+tp+';', decl, (('typedef struct '+block+' ')[::-1].replace(';',(';'+tp[::-1]),1)[::-1]), demandingTP])
                        # append undeclared fields to wtypes
                        for nestedDecl in stc.findall(".//decl_stmt"):
                            statement=self.getAllText(nestedDecl)
                            for wd in statement.split():
                                if wd.strip()=='typedef' or wd.strip()=='struct' or wd.strip()=='static': #FIXME: this does not seem to be systematic
                                    # skip forekeywords 
                                    continue
                                # capture the first word as the type
                                #print 'type is> '+wd
                                wtypes.append([wd, tp])
                                break
                        #print 'non'
                except:
                    # ignore, its forward declaration
                    nf=True
            # second, typedefs
            for tpd in root.findall(".//typedef"):
                try:
                    nmroot=tpd.find("name")
                    blkroot=tpd.find("type")
                    decl=self.getAllText(tpd)
                    name=self.getAllText(nmroot).split()[0]
                    block=self.getAllText(blkroot)
                    if DEBUGDCL:
                        self.recursivePrint(tpd, 0)
                        print 'declaration of "'+name+'" is "'+decl.replace('\n',' ')+'" blk="'+block+'"'
                        #print ('typedef struct '+block+' '+tp+';')
                    if tp==name:
                        #print 'type name matched>'
                        if target_platform=='ISPC':
                            curl2curl = decl[decl.find('{'):][::-1]
                            curl2curl = curl2curl[curl2curl.find('}'):][::-1]
                            curl2curl = 'struct '+tp+' '+curl2curl+';\n'
                            here_declared.append([tp, 'struct '+tp+';', curl2curl, curl2curl, demandingTP])
                        else:
                            here_declared.append([tp, 'typedef struct '+tp+';', decl, decl, demandingTP])
                        # append undeclared fields to wtypes
                        for nestedDecl in tpd.findall(".//decl_stmt"):
                            statement=self.getAllText(nestedDecl)
                            for wd in statement.split():
                                if wd.strip()=='typedef' or wd.strip()=='struct' or wd.strip()=='static': #FIXME: this does not seem to be systematic
                                    # skip forekeywords 
                                    continue
                                # capture the first word as the type
                                #print 'type is> '+wd
                                wtypes.append([wd, tp])
                                break
                        #print 'non'
                except:
                    # ignore, its forward declaration
                    nf=True
            # third,  unions   #FIXME: not implemented
            # fourth, enums    #FIXME: not implemented
            # fifth,  classes  #FIXME: not implemented
        # recursively, declare the types which are undeclared in elements of typdefs, structs, and unions 
        lower_declared=[]
        if len(wtypes)>0:
            lower_declared=self.findDeclsOfTypes(root, wtypes, here_declared+upper_declared, builtintypes, target_platform)
        # merge all levels
        merged=[]
        for [p1, p2, p3, p4, p5] in lower_declared+here_declared+upper_declared:
            unq=True
            for [r1, r2, r3, r4, r5] in merged:
                if p1==r1:
                    unq=False
                    break
            if unq:
                merged.append([p1, p2, p3, p4, p5])
        return merged

    def prefixFunction(self, root, kernelsParents):
        for id in range(0,len(kernelsParents)):
            found=False
            for tmpl in root.findall(".//template"):
                #print 'template> '+self.getAllText(tmpl)
                try:
                    nm=tmpl.find("./function/name")
                    if nm.text==kernelsParents[id]:
                        template='template '+self.getAllText(tmpl.find("./parameter_list"))+' '
                        try:
                            tmpl.text =' __ipmacc_prototypes_kernels_'+str(id)+' '+tmpl.text
                        except:
                            tmpl.text =' __ipmacc_prototypes_kernels_'+str(id)+' '
                        found=True
                        break
                except:
                    nonFunctionTemplate=True
            if not found:
                for fcn in root.findall(".//function"):
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
        for fcn in root.findall(".//function"):
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
                    for stm in fcn.findall(".//parameter_list/param"):
                        for ch in stm.findall(".//decl"):
                            arg_stmt=self.getAllText(ch).strip()+';'
                            [e_vars, e_types, e_sizes]=get_variable_size_type(arg_stmt)
                            e_vnames+=e_vars
                            e_vsizes+=e_sizes
                            e_vtypes+=e_types
                    decls=fcn.findall(".//decl_stmt")
                    decls+=root.findall("./decl_stmt")
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
                            # print 'found the size> '+e_size
                            return e_size
                else:
                    # ALT 1
                    decls=fcn.findall(".//decl_stmt")+fcn.findall(".//parameter_list/param")
                    for ch in decls:
                        # go through all declarations
                        vlist=ch.findall(".//decl/name")
                        for v in vlist:
                            # check all variable names declared in this statemet
                            [vn,arr]=self.cleanVarName(self.getAllText(v))
                            if vn==vname:
                                # here we found the variable
                                if DEBUG: print '============'
                                if DEBUG: print tostring(ch)
                                type=self.getAllText(ch.find(".//decl/type")).strip()
                                nDynDims=type.count('*')
                                #print 'ndim'
                                dims=[]
                                for dim in ch.findall(".//decl/name/index"):
                                    tmp_dimsize=self.getAllText(dim).strip()
                                    #print 'index size> '+tmp_dimsize
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
        for fcn in root.findall(".//function"):
            parent=fcn.find("name").text
            template=self.findTemplateOverFcn(root,parent)
            for ch in fcn.findall(".//call/name"):
                fn=self.getAllText(ch).strip()
                if DEBUG: print 'functionCall> '+fn
                if fn==fname:
                    return [template,parent]
        return [template,'']

    def getFunctionCalls(self, root, fname):
        fcalls=[]
        for fcn in root.findall(".//function"):
            ch=fcn.find("name")
            if ch.text==fname:
                for ch in fcn.findall(".//call/name"):
                    fn=self.getAllText(ch)
                    if DEBUG: print 'functionCall> '+fn
                    fcalls.append(fn)
                break
        return fcalls

    def getAllNames(self, root):
        names=[]
        for nm in root.findall(".//name"):
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
        #content=content.replace('xmlns:cpp=','namsp=')
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

    def getAllKernelArgs(self, root):
        print 'called'
        names=[]
        for np in root.findall(".//parameter_list/param"):
            #for nm in np.findall(".//decl/"):
            arg_stmt=self.getAllText(np).strip()+';'
            if DEBUG: print '========================='+arg_stmt
            [e_vars, e_types, e_sizes]=get_variable_size_type(arg_stmt)
            #if ','.join(e_vars)=='':
            #    continue
            if DEBUG: print 'vname > '+','.join(e_vars)
            if DEBUG: print 'vsize > '+','.join(e_sizes)
            if DEBUG: print 'vtype > '+','.join(e_types)
            if ','.join(e_sizes).find('dynamic')!=-1:
                names.append([','.join(e_vars), ','.join(e_sizes), ','.join(e_types)])
        return names
    def transDeclAnalyze(self,no):
        # no is a xml decl_stmt node
        dclWhole=self.getAllText(no)
        for np in no.findall(".//type"):
            dclType=self.getAllText(np)
        if dclType=='':
            print 'Fatal Error! type not found in decl_stmt'
            exit(-1)
        dclVars=dclWhole.replace(dclType,'')
        return [dclWhole, dclType, dclVars]

    def getAllArrayAccesses(self,root,arrnames):
        arraccs=[]
        indecis=[]
        dependt=[]
        csv=''
        rowid=0
        # find all types
        if DEBUGKA:
            for np in root.findall(".//decl"):
                print 'decl> '+self.getAllText(np)
                for nm in np.findall(".//expr"):
                    print 'expr> '+self.getAllText(nm)
                for nm in np.findall(".//type"):
                    print 'type> '+self.getAllText(nm)
        # find all array accesses
        for nl in root.findall(".//name"):
            for nm in nl.findall(".//index"):
                arrname=self.getAllText(nl).strip().split()[0]
                for a in arrnames:
                    if arrname==a:
                        ambigVars=set([])
                        ambigString=False
                        # if we are looking for this array access,
                        #  book the dependencies
                        indexString=self.getAllText(nm).strip()
                        print 'array> '+arrname+' index> '+indexString
                        csv+=str(rowid)+','+arrname+','
                        rowid+=1
                        # list all directly dependent variables
                        vnms=[]
                        for nn in nm.findall(".//name"):
                            vnms.append(self.getAllText(nn).split()[0])
                        vnms=set(vnms)
                        # recuresively, find the dependency tree
                        allNamesDependingOnThisVariable=[]
                        while len(allNamesDependingOnThisVariable)!=len(vnms):
                            if DEBUGKA: print ' round of variable tree construction: '+','.join(vnms)
                            allNamesDependingOnThisVariable=set(vnms)
                            for vnm in allNamesDependingOnThisVariable:
                                #print '\t'+vnm
                                # list all previous writes to this variable
                                # first, check declarations
                                if DEBUGKA: print '  parsing decl_stmts for '+vnm
                                for no in root.findall(".//decl_stmt"):
                                    # 1
                                    if DEBUGKA: print '   parsing '+self.getAllText(no)+' for '+vnm
                                    [dclWhole,dclType,dclVars]=self.transDeclAnalyze(no)
                                    if DEBUGKA: print '   declVars here: '+dclVars
                                    # 2 
                                    #if string_found(vnm,self.getAllText(no)) and len(self.getAllText(no).split(vnm))>1 and self.getAllText(no).split(vnm)[1].find('=')!=-1:
                                    if string_found(vnm,dclVars) and len(dclVars.split(vnm))>1 and dclVars.split(vnm)[1].find('=')!=-1:
                                        if DEBUGKA: print '    '+dclVars
                                        # ALT 1
                                        for np in no.findall(".//name"):
                                            if DEBUGKA: print '     adding '+self.getAllText(np).split()[0]+' to set' 
                                            vnms.add(self.getAllText(np).split()[0])
                                        # ALT 2
                                        #for np in dclVars.split(','):
                                        #    vnms.add(np.split()[0])
                                        #    if DEBUGKA: print '     adding '+np.split()[0]+' to set' 
                                        if DEBUGKA: print '    '+','.join(vnms)
                                # then, check all assignments 
                                for no in root.findall(".//expr_stmt/expr"):
                                    try:
                                        if DEBUGKA: print '    '+no.find("name").text
                                        if no.find("name").text==vnm and len(self.getAllText(no).split(vnm))>1 and self.getAllText(no).split(vnm)[1].find('=')!=-1:
                                            if DEBUGKA: print '    '+self.getAllText(no)
                                            for np in no.findall(".//name"):
                                                vnms.add(self.getAllText(np).split()[0])
                                                if DEBUGKA: print '     adding '+np.split()[0]+' to set' 
                                    except:
                                        nop=1
                        # remove data types from the list
                        ignoreSet=set(['int','float','double','char'])
                        for vnm in ignoreSet:
                            try:
                                allNamesDependingOnThisVariable.remove(vnm)
                            except:
                                keyNotFound=True
                        # we found all the dependent variables
                        if DEBUGKA: print ' Deps<>> '+','.join(set(allNamesDependingOnThisVariable))
                        csv+='&'.join(set(allNamesDependingOnThisVariable))+','
                        # report writes to dependent variables 
                        allWritesTodependingVars=[]
                        for vnm in allNamesDependingOnThisVariable:
                            writes=[]
                            #print '\t'+vnm
                            # first, check declarations
                            for no in root.findall(".//decl_stmt"):
                                [dclWhole,dclType,dclVars]=self.transDeclAnalyze(no)
                                # ALT 1
                                #if string_found(vnm,self.getAllText(no)) and len(self.getAllText(no).split(vnm))>1 and self.getAllText(no).split(vnm)[1].find('=')!=-1:
                                #    writes.append(self.getAllText(no))
                                #   print '\t\t'+self.getAllText(no)
                                # ALT 2
                                for np in dclVars.split(','):
                                    if string_found(vnm,np) and len(np.split(vnm))>1 and np.split(vnm)[1].find('=')!=-1:
                                        #writes.append(np)
                                        writes.append(np.split('=')[1])
                                        if DEBUGKA: print '   extracting '+vnm+' from '+np+'. found value> '+np.split('=')[1]
                            # then, check all assignments 
                            for no in root.findall(".//expr_stmt/expr"):
                                try:
                                    #print '\t\t'+no.find("name").text
                                    if no.find("name").text==vnm and len(self.getAllText(no).split(vnm))>1 and self.getAllText(no).split(vnm)[1].find('=')!=-1:
                                        tmpwrt=self.getAllText(no).split('=')[1]
                                        if DEBUGKA: print '   appending write <'+tmpwrt+'> for <'+vnm+'>'
                                        writes.append(tmpwrt)
                                        #print '\t\t'+self.getAllText(no)
                                except:
                                    nop=1
                            allWritesTodependingVars.append(writes)
                        if len(allNamesDependingOnThisVariable)!=len(allWritesTodependingVars):
                            print 'Fatal Error!'
                            exit(-1)
                        else:
                            # post-process writes and extract single self-included statement for the index
                            allValuesOfDependingVariables=[]
                            idx=0
                            for vnm in allNamesDependingOnThisVariable:
                                values=allWritesTodependingVars[idx]
                                if DEBUGKA: print '  checking writes to '+vnm
                                if DEBUGKA: print '   '+'   \n'.join(values)
                                # select a proper value.
                                # currently we assume there is only one.
                                # else we should check the variable scopes FIXME
                                appendingWrite=''
                                if len(values)==0:# or values[0].find('=')==-1:
                                    appendingWrite=vnm.replace(' ','').replace(';','')
                                else:
                                    if len(values)>1:
                                        ambigVars.add(vnm)
                                        if KAVERBOSE:
                                            print '   warning! selecting one of the multiple values: '+vnm
                                            print '    '+'","'.join(values)
                                    #appendingWrite=values[0].split('=')[1].replace(' ','').replace(';','')
                                    appendingWrite=values[0].replace(' ','').replace(';','')
                                if DEBUGKA: print '   '+'appending '+appendingWrite
                                allValuesOfDependingVariables.append(appendingWrite)
                                idx=idx+1
                            stringUpdated=True
                            if DEBUGKA: print ' starting string replacer:'
                            while stringUpdated:
                                stringUpdated=False
                                idx=0
                                if DEBUGKA: print '  processing string reconstruction... stringindex> '+indexString
                                for vnm in allNamesDependingOnThisVariable:
                                    if DEBUGKA: print '   checking <'+vnm+'> value <'+allValuesOfDependingVariables[idx]+'>'
                                    if re.search(r'\b%s\b'%vnm,indexString) and allValuesOfDependingVariables[idx]!=vnm:
                                        if vnm in ambigVars: ambigString=True
                                    #if indexString.find(vnm)!=-1 and allValuesOfDependingVariables[idx]!=vnm:
                                        stringUpdated=True
                                        indexString=re.sub(r'\b%s\b'%vnm,'('+allValuesOfDependingVariables[idx]+')',indexString)
                                        #indexString=indexString.replace(vnm,'('+allValuesOfDependingVariables[idx]+')')
                                    idx=idx+1
                        print '\tindex string> '+indexString.replace(' ','')
                        csv+=indexString.replace(' ','')+','+('ambig' if ambigString else '')+',\n'
                        #vnms=set(vnms)
                        arraccs.append(a)
                        indecis.append(self.getAllText(nm).strip())
                        dependt.append(allNamesDependingOnThisVariable)
        print csv
        return [arraccs,indecis,dependt]

    def is_written(self,root,vnm):
        #print 'srcml:debug: ', vnm
        for no in root.findall(".//expr_stmt/expr"):
            #print 'srcml:debug:', 'expression:', self.getAllText(no), no
            try:
                #print 'srcml:debug: ', 'name:', no.find(".//name").text
                #self.recursivePrint(no, 0)
                if self.getAllText(no).split('=')[0].split('[')[0].strip()==vnm:
                    return True
            except:
                nop=1
        for no in root.findall(".//decl_stmt"):
            # print '   parsing '+self.getAllText(no)+' for '+vnm
            [dclWhole,dclType,dclVars]=self.transDeclAnalyze(no)
            # print '   declVars here: '+dclVars
            if string_found(vnm,dclVars) and len(dclVars.split(vnm))>1 and dclVars.split(vnm)[1].find('=')!=-1:
                return True
        return False

    def getAllVarDependencies(self,root,arrnames):
        arraccs=[]
        indecis=[]
        dependt=[]
        csv=''
        rowid=0
        # find all types
        if DEBUGKA: print root
        if DEBUGKA:
            for np in root.findall(".//decl"):
                print 'decl> '+self.getAllText(np)
                for nm in np.findall(".//expr"):
                    print 'expr> '+self.getAllText(nm)
                for nm in np.findall(".//type"):
                    print 'type> '+self.getAllText(nm)
        # find all array accesses
        for nl in root.findall(".//name"):
            if True: #for nm in nl.findall(".//index"):
                arrname=self.getAllText(nl).strip().split()[0]
                for a in arrnames:
                    if DEBUGKA: print arrname+'!='+a
                    if arrname==a:
                        ambigVars=set([])
                        ambigString=False
                        # if we are looking for this array access,
                        #  book the dependencies
                        indexString=self.getAllText(nl).strip()
                        if DEBUGKA: print 'variable> '+arrname+' matched-name> '+indexString
                        csv+=str(rowid)+','+arrname+','
                        rowid+=1
                        # list all directly dependent variables
                        vnms=[arrname]
                        #for nn in nm.findall(".//name"):
                        #    vnms.append(self.getAllText(nn).split()[0])
                        vnms=set(vnms)
                        # recuresively, find the dependency tree
                        allNamesDependingOnThisVariable=[]
                        while len(allNamesDependingOnThisVariable)!=len(vnms):
                            if DEBUGKA: print ' round of variable tree construction: '+','.join(vnms)
                            allNamesDependingOnThisVariable=set(vnms)
                            for vnm in allNamesDependingOnThisVariable:
                                #print '\t'+vnm
                                # list all previous writes to this variable
                                # first, check declarations
                                if DEBUGKA: print '  parsing decl_stmts for '+vnm
                                for no in root.findall(".//decl_stmt"):
                                    # 1
                                    if DEBUGKA: print '   parsing '+self.getAllText(no)+' for '+vnm
                                    [dclWhole,dclType,dclVars]=self.transDeclAnalyze(no)
                                    if DEBUGKA: print '   declVars here: '+dclVars
                                    # 2 
                                    #if string_found(vnm,self.getAllText(no)) and len(self.getAllText(no).split(vnm))>1 and self.getAllText(no).split(vnm)[1].find('=')!=-1:
                                    if string_found(vnm,dclVars) and len(dclVars.split(vnm))>1 and dclVars.split(vnm)[1].find('=')!=-1:
                                        if DEBUGKA: print '    '+dclVars
                                        # ALT 1
                                        for np in no.findall(".//name"):
                                            if DEBUGKA: print '     adding '+self.getAllText(np).split()[0]+' to set' 
                                            vnms.add(self.getAllText(np).split()[0])
                                        # ALT 2
                                        #for np in dclVars.split(','):
                                        #    vnms.add(np.split()[0])
                                        #    if DEBUGKA: print '     adding '+np.split()[0]+' to set' 
                                        if DEBUGKA: print '    '+','.join(vnms)
                                # then, check all assignments 
                                for no in root.findall(".//expr_stmt/expr"):
                                    try:
                                        if DEBUGKA: print '    '+no.find("name").text
                                        if no.find("name").text==vnm and len(self.getAllText(no).split(vnm))>1 and self.getAllText(no).split(vnm)[1].find('=')!=-1:
                                            if DEBUGKA: print '    '+self.getAllText(no)
                                            for np in no.findall(".//name"):
                                                vnms.add(self.getAllText(np).split()[0])
                                                if DEBUGKA: print '     adding '+np.split()[0]+' to set' 
                                    except:
                                        nop=1
                        # remove data types from the list
                        ignoreSet=set(['int','float','double','char'])
                        for vnm in ignoreSet:
                            try:
                                allNamesDependingOnThisVariable.remove(vnm)
                            except:
                                keyNotFound=True
                        # we found all the dependent variables
                        if DEBUGKA: print ' Deps<>> '+','.join(set(allNamesDependingOnThisVariable))
                        csv+='&'.join(set(allNamesDependingOnThisVariable))+','
                        # report writes to dependent variables 
                        allWritesTodependingVars=[]
                        for vnm in allNamesDependingOnThisVariable:
                            writes=[]
                            #print '\t'+vnm
                            # first, check declarations
                            for no in root.findall(".//decl_stmt"):
                                [dclWhole,dclType,dclVars]=self.transDeclAnalyze(no)
                                # ALT 1
                                #if string_found(vnm,self.getAllText(no)) and len(self.getAllText(no).split(vnm))>1 and self.getAllText(no).split(vnm)[1].find('=')!=-1:
                                #    writes.append(self.getAllText(no))
                                #   print '\t\t'+self.getAllText(no)
                                # ALT 2
                                for np in dclVars.split(','):
                                    if string_found(vnm,np) and len(np.split(vnm))>1 and np.split(vnm)[1].find('=')!=-1:
                                        #writes.append(np)
                                        writes.append(np.split('=')[1])
                                        if DEBUGKA: print '   extracting '+vnm+' from '+np+'. found value> '+np.split('=')[1]
                            # then, check all assignments 
                            for no in root.findall(".//expr_stmt/expr"):
                                try:
                                    #print '\t\t'+no.find("name").text
                                    if no.find("name").text==vnm and len(self.getAllText(no).split(vnm))>1 and self.getAllText(no).split(vnm)[1].find('=')!=-1:
                                        tmpwrt=self.getAllText(no).split('=')[1]
                                        if DEBUGKA: print '   appending write <'+tmpwrt+'> for <'+vnm+'>'
                                        writes.append(tmpwrt)
                                        #print '\t\t'+self.getAllText(no)
                                except:
                                    nop=1
                            allWritesTodependingVars.append(writes)
                        if len(allNamesDependingOnThisVariable)!=len(allWritesTodependingVars):
                            print 'Fatal Error!'
                            exit(-1)
                        else:
                            # post-process writes and extract single self-included statement for the index
                            allValuesOfDependingVariables=[]
                            idx=0
                            for vnm in allNamesDependingOnThisVariable:
                                values=allWritesTodependingVars[idx]
                                if DEBUGKA: print '  checking writes to '+vnm
                                if DEBUGKA: print '   '+'   \n'.join(values)
                                # select a proper value.
                                # currently we assume there is only one.
                                # else we should check the variable scopes FIXME
                                appendingWrite=''
                                if len(values)==0:# or values[0].find('=')==-1:
                                    appendingWrite=vnm.replace(' ','').replace(';','')
                                else:
                                    if len(values)>1:
                                        ambigVars.add(vnm)
                                        if KAVERBOSE:
                                            print '   warning! selecting one of the multiple values: '+vnm
                                            print '    '+'","'.join(values)
                                    #appendingWrite=values[0].split('=')[1].replace(' ','').replace(';','')
                                    appendingWrite=values[0].replace(' ','').replace(';','')
                                if DEBUGKA: print '   '+'appending '+appendingWrite
                                allValuesOfDependingVariables.append(appendingWrite)
                                idx=idx+1
                            stringUpdated=True
                            if DEBUGKA: print ' starting string replacer:'
                            while stringUpdated:
                                stringUpdated=False
                                idx=0
                                if DEBUGKA: print '  processing string reconstruction... stringindex> '+indexString
                                for vnm in allNamesDependingOnThisVariable:
                                    if DEBUGKA: print '   checking <'+vnm+'> value <'+allValuesOfDependingVariables[idx]+'>'
                                    if re.search(r'\b%s\b'%vnm,indexString) and allValuesOfDependingVariables[idx]!=vnm:
                                        if vnm in ambigVars: ambigString=True
                                    #if indexString.find(vnm)!=-1 and allValuesOfDependingVariables[idx]!=vnm:
                                        stringUpdated=True
                                        indexString=re.sub(r'\b%s\b'%vnm,'('+allValuesOfDependingVariables[idx]+')',indexString)
                                        #indexString=indexString.replace(vnm,'('+allValuesOfDependingVariables[idx]+')')
                                    idx=idx+1
                        if DEBUGKA: print '\tindex string> '+indexString.replace(' ','')
                        csv+=indexString.replace(' ','')+','+('ambig' if ambigString else '')+',\n'
                        #vnms=set(vnms)
                        arraccs.append(a)
                        indecis.append(self.getAllText(nl).strip())
                        dependt.append(allNamesDependingOnThisVariable)
        if DEBUGKA: print csv
        return [arraccs,indecis,dependt]


#           try:
#               str=nm.text.strip()
#               #if DEBUG: print 'new identifier > '+str
#               print 'new identifier > '+str
#               names.append(str)
#           except:
#               str=''

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

def srcml_get_fwdecls(code, undeclsTypes, undeclsFuncs, intrinsics, builtintypes, target_platform):
    # undeclsTypes: types which are used, but not declared on accelerator
    # undeclsFuncs: functions which are called, but not declared on accelerator
    srcml_sample = srcML()
    root=srcml_sample.codeToXML(code)
    declFuncs=srcml_sample.findDeclsOfFuncs(root, undeclsFuncs, [], intrinsics)
    declTypes=srcml_sample.findDeclsOfTypes(root, [[tp, ''] for tp in undeclsTypes], [], builtintypes, target_platform)
    return [declTypes, declFuncs]

def srcml_get_active_types(code, calls, intrinsics):
    srcml_sample = srcML()
    root=srcml_sample.codeToXML(code)
    return srcml_sample.findActiveTypesRecursively(root, calls, [], intrinsics)

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
def srcml_is_written(root,vname):
    srcml_sample = srcML()
    return srcml_sample.is_written(root,vname)

# kernel analyzer additions
def srcml_get_kernelargs(root):
    srcml_sample = srcML()
    return srcml_sample.getAllKernelArgs(root)
def srcml_get_arrayaccesses(root,arrnames):
    srcml_sample = srcML()
    return srcml_sample.getAllArrayAccesses(root,arrnames)
def srcml_get_dependentVars(root,varNames):
    srcml_sample = srcML()
    return srcml_sample.getAllVarDependencies(root,varNames)
