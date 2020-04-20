

def clean_clause(stmti):
    stmt=' '.join(stmti.split())
    print stmt.strip()
    stmt=stmt.replace(', ',',')
    stmt=stmt.replace(' ,',',')
    stmt=stmt.replace('] ',']')
    stmt=stmt.replace(' [','[')
    stmt=stmt.replace(') ',')')
    stmt=stmt.replace(' (','(')
    stmt=stmt.replace(' = ','=')
    stmt=stmt.replace(' =','=')
    stmt=stmt.replace('= ','=')
    stmt=stmt.replace('*',' * ')
    print stmt.strip()
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
        print 'seprator:'+sep+' word:'+word+' init:'+str(nextinit)+' vardecl:'+str(vardeclr)+' typedecl:'+str(typedecl)
        if typedecl:
            type.append(word)
        if vardeclr:
            vname+=word+' '
        if vname!='' and ((not vardeclr) or sep==',' or sep==';' or sep=='=' or idx==(len(words_list)-1)):
            # flush vname
            [name,arr]=decomposeWord(vname)
            varnames.append(name)
            arr.append('('+' '.join(type)+')')
            varsizes.append('*'.join(arr))
            types.append(' '.join(type)+('*'*(len(arr)-1)))
            vname=''
            vardeclr=False
        nextinit= sep=='='

    for i in range(0,len(types)):
        print 'type:('+types[i]+') name:('+varnames[i]+') size:('+varsizes[i]+')'


#statement='unsigned long long int* a = NULL, b=0, *c=a==3, *  e = NULL , kk[8];'
statement='unsigned long long int tic , toc ;'
#statement='unsigned long long int ki [ 12 ] , a = 8, asd = functionCall(10, 9, asd), taghi[3] = {0,1,2} , taghi[ function8(asd, wert) ]= {func(h) , func(g) , s[0]}, *pointer[19][20];'
#statement="float s   =  0 ;"
#statement="float  * a , * b , * c ;"
#statement='float *a=NULL, *b=NULL, *c=NULL;'
get_variable_size_type(statement)
