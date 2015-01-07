#include "common.h"

void* openacc_container_map::allocate(size_t size){
    void *ptr=(void*)malloc(size);
    if(IPMACCCONTAINER_VERBOSE) cout<<"IPMACCCONTAINER: allocating "<<size<<" bytes!"<<endl;
    return ptr;
};


/*
#define IPMACCCONTAINER_VERBOSE getenv("IPMACCCONTAINER_VERBOSE")

// OVERLOAD FOLLOWING FUNCTIONS
//
// get size of the container
template <class T>
size_t openacc_container_map::get_container_size(std::vector<T> &container){
    return sizeof(T)*container.size();
}

// copy container into the buffer allocated befor
template <class T>
void* openacc_container_map::copyin(std::vector<T> &container)
{
    //std::vector<T>::iterator it=container.begin();
    T* ptr=(T*)get_buffer_ptr(container);
    if(ptr){
        for(int i=0; i<container.size(); i++){
            ptr[i]=container[i];
        }
    }else{
        cout<<"IPMACC fatal error: std container not found in buffer map! [copyin]"<<endl;
        exit(-1);
    }
}

// copy container into the buffer allocated befor
template <class T>
void openacc_container_map::copyout(std::vector<T> &container)
{
    //std::vector<T>::iterator it=container.begin();
    T* ptr=(T*)get_buffer_ptr(container);
    if(ptr){
        for(int i=0; i<container.size(); i++){
            container[i]=ptr[i];
        }
    }else{
        cout<<"IPMACC fatal error: std container not found in buffer map! [copyout]"<<endl;
        exit(-1);
    }
}

/////////////////////////////////////////// 
/////////// DO NOT MODIFY FOLLOWING LINE //
///////////////////////////////////////////

void* openacc_container_map::allocate(size_t size){
    void *ptr=(void*)malloc(size);
    if(IPMACCCONTAINER_VERBOSE) cout<<"IPMACCCONTAINER: allocating "<<size<<" bytes!"<<endl;
    return ptr;
};

template <class T>
void* openacc_container_map::addmap(T &container){
    if(IPMACCCONTAINER_VERBOSE) cout<<"IPMACCCONTAINER: mapping new pointer> "<<(void*)&container<<endl;
    void* ptr=(void*)allocate(get_container_size(container));
    container_buffer_map.insert(std::pair<void*,void*>((void*)&container,(void*)ptr));
    return ptr;
};

template <class T>
void openacc_container_map::removemap(T &container){
    if(container_buffer_map.find((void*)&container)!=container_buffer_map.end()){
        free(container_buffer_map.find((void*)&container)->second);
        container_buffer_map.erase(container_buffer_map.find((void*)&container));
        if(IPMACCCONTAINER_VERBOSE) cout<<"IPMACCCONTAINER: freeing buffer for ["<<&container<<"] done";
    }else{
        if(IPMACCCONTAINER_VERBOSE) cout<<"IPMACCCONTAINER: freeing buffer for ["<<&container<<"] failed: no match found!";
    }
}

template <class T>
void*  openacc_container_map::get_buffer_ptr(T &container)
{
    if(container_buffer_map.find((void*)&container)!=container_buffer_map.end()){
        if(IPMACCCONTAINER_VERBOSE) cout<<"IPMACCCONTAINER: container found!"<<endl;
        return container_buffer_map.find((void*)&container)->second;
    }else{
        if(IPMACCCONTAINER_VERBOSE){
            cout<<"IPMACCCONTAINER: content of mapping list:"<<endl;
            for(std::map<void*, void*>::iterator it=container_buffer_map.begin();
                it!=container_buffer_map.end();
                it++)
            {
                cout<<"\t"<<it->first<<"<>"<<it->second<<endl;
            }
            cout<<"IPMACCCONTAINER: container not found! key: "<<(void*)&container<<endl;
        }
        return NULL;
    }
}
*/

#ifndef OBJ
int main()
{
    std::vector<int> myvector;
    myvector.push_back(10);
    myvector.push_back(12);
    myvector.push_back(14);
    __ipmacc_contmap.addmap(myvector);
    __ipmacc_contmap.copyin(myvector);

    int *ptr=(int*)__ipmacc_contmap.get_buffer_ptr(myvector);
    for(int i=0; i<myvector.size(); i++)
    {
        cout<<ptr[i]<<endl;
    }

    __ipmacc_contmap.removemap(myvector);
    int *ptr2=(int*)__ipmacc_contmap.get_buffer_ptr(myvector);
    assert(ptr2==NULL);

    cout<<"test passed!"<<endl;
    return 0;
}
#endif

