// inserting into a vector
#include <iostream>
#include <vector>

int main ()
{
    std::vector<int> myvector;

    for(int i=0; i<10; i++){
        myvector.push_back(i);
    }
    int size=myvector.size();

    #pragma acc data copy(myvector)
    #pragma acc kernels 
    #pragma acc loop independent 
    for(int i=0; i<size; i++){
        myvector[i]=myvector[i]*2;
    }

    std::cout << "myvector contains:";
    std::vector<int>::iterator it;
    for (it=myvector.begin(); it<myvector.end(); it++)
        std::cout << ' ' << *it;
    std::cout << '\n';

    return 0;
}
