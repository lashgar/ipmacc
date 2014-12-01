
def clauseDecomposer(clause):
    clist=[]
    index=1
    if len(clause)>0:
        lastchar=clause[0]
        while index<len(clause):
            print str(len(clist))+'->'+lastchar
            tclause=''
            # read spacing
            while index<len(clause) and (lastchar==' ' or lastchar=='\t'):
                tclause+=lastchar
                lastchar=clause[index]
                index+=1
            # read clause name
            while index<len(clause) and (str.isalpha(lastchar) or str.isdigit(lastchar) or lastchar=='_'):
                tclause+=lastchar
                lastchar=clause[index]
                index+=1
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

print '^'.join(clauseDecomposer('private(a) reduction(+:sum)'))
print '^'.join(clauseDecomposer('copyin(a[0:list(N)]) private(a) reduction(+:sum)'))
print '^'.join(clauseDecomposer('copyin(a[0:list(N)])private(a)reduction(+:sum)'))
