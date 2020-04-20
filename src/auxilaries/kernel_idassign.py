
totalThread=1
fSizes=[2, 3]
for i in fSizes:
    totalThread=totalThread*i

blockDimx=256
for i in range(0,totalThread):
    if i<totalThread:
        threadIdxx=i%blockDimx
        blockIdxx=i/blockDimx
        uid=threadIdxx+(blockDimx*blockIdxx)
        
        dim=[]
        dim.append(uid%fSizes[0])
        for k in range(1,len(fSizes)):
            # find the index at each iteration
            res=fSizes[0]
            for l in range(1,k):
                res=res*fSizes[l]
            dim.append((uid/res)%fSizes[k])
        exp='(bid='+str(blockIdxx)+' tid='+str(threadIdxx)+')'
        for k in range(0,len(dim)):
            exp=exp+' dim'+str(k)+'->'+str(dim[k])
        print exp
