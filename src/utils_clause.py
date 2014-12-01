
def clauseDecomposer_break(clause):
    DEBUG=False
    clist=[]
    index=1
    if len(clause)>0:
        lastchar=clause[0]
        while index<len(clause):
            name=''
            value=''
            if DEBUG: print str(len(clist))+'->'+lastchar
            tclause=''
            # read spacing
            while index<len(clause) and (lastchar==' ' or lastchar=='\t'):
                tclause+=lastchar
                lastchar=clause[index]
                index+=1
            # read clause name
            while (str.isalpha(lastchar) or str.isdigit(lastchar) or lastchar=='_'):
                name+=lastchar
                if(index<len(clause)):
                    lastchar=clause[index]
                    index+=1
                else:
                    break
            tclause+=name
            # read spacing
            while index<len(clause) and (lastchar==' ' or lastchar=='\t'):
                tclause+=lastchar
                lastchar=clause[index]
                index+=1
            # read parenteces
            if lastchar=='(':
                depth=1
                while index<len(clause) and (not (lastchar==')' and depth==0)):
                    value+=lastchar
                    lastchar=clause[index]
                    index+=1
                    if   lastchar=='(':
                        depth+=1
                    elif lastchar==')':
                        depth-=1
                value+=lastchar
                tclause+=value
                if index<len(clause):
                    lastchar=clause[index]
                    index+=1
#            tclause+=lastchar
            value = value[1:-1] if value!='' else ''
            clist.append([name, value])
            if DEBUG:
                print 'tople: '+name+'  (  '+value+'  )'
    return clist

def clauseDecomposer(clause):
    DEBUG=False
    clist=[]
    index=1
    if len(clause)>0:
        lastchar=clause[0]
        while index<len(clause):
            if DEBUG: print str(len(clist))+'->'+lastchar
            tclause=''
            # read spacing
            while index<len(clause) and (lastchar==' ' or lastchar=='\t'):
                tclause+=lastchar
                lastchar=clause[index]
                index+=1
            # read clause name
            while (str.isalpha(lastchar) or str.isdigit(lastchar) or lastchar=='_'):
                tclause+=lastchar
                if(index<len(clause)):
                    lastchar=clause[index]
                    index+=1
                else:
                    break
            # read spacing
            while index<len(clause) and (lastchar==' ' or lastchar=='\t'):
                tclause+=lastchar
                lastchar=clause[index]
                index+=1
            # read parenteces
            if lastchar=='(':
                depth=1
                while index<len(clause) and (not (lastchar==')' and depth==0)):
                    tclause+=lastchar
                    lastchar=clause[index]
                    index+=1
                    if   lastchar=='(':
                        depth+=1
                    elif lastchar==')':
                        depth-=1
                tclause+=lastchar
                if index<len(clause):
                    lastchar=clause[index]
                    index+=1
#            tclause+=lastchar
            clist.append(tclause)
    return clist

#print ', '.join(clauseDecomposer('copyin(a[0:N]) independent copyout(c[0:getLen()],d(0,S))'))
