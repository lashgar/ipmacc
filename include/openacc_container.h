#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <vector>
#include <map>
#include <malloc.h>
#include <assert.h>

using namespace std;

class openacc_container_map{
    private:
        std::map<void*,void*> container_buffer_map;
    public:
        openacc_container_map(){};
        ~openacc_container_map(){};

        void* allocate(size_t size);

        template <class T>
        void* addmap(T &container);

        template <class T>
        void removemap(T &container);

        template <class T>
        void*  get_buffer_ptr(T &container);

        // OVERLOAD FOLLOWING FUNCTIONS
        // get size of the container
        template <class T>
        size_t get_container_size(std::vector<T> &container);
        // copy the container into the allocated space,
        // if no match found, stop and abort
        template <class T>
        void* copyin(std::vector<T> &container);
        // copy the content of allocated space into container,
        // if no match found, stop and abort
        template <class T>
        void* copyout(std::vector<T> &container);
};

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
    return ptr;
}

// copy container into the buffer allocated befor
template <class T>
void* openacc_container_map::copyout(std::vector<T> &container)
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
    return ptr;
}

/////////////////////////////////////////// 
/////////// DO NOT MODIFY FOLLOWING LINE //
///////////////////////////////////////////

template <class T>
void* openacc_container_map::addmap(T &container){

    if(IPMACCCONTAINER_VERBOSE){
        cout<<"IPMACCCONTAINER: mapping new pointer> "<<(void*)&container<<endl;
        if(container_buffer_map.find((void*)&container)!=container_buffer_map.end()){
            cout<<"IPMACCCONTAINER: warning: potentially about to lose the pointer! [reallocation]"<<(void*)&container<<endl;
        }
    }
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

extern openacc_container_map __ipmacc_contmap;
