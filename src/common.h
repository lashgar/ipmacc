#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "msr.h"
#include <sys/time.h>

///////////////////////////
// INTERFACING FUNCTIONS //
///////////////////////////

void ipmacc_prompt(char *s){
	if (getenv("IPMACC_VERBOSE"))
		printf("%s",s);
}

#ifdef __cplusplus
#include "../include/openacc_container.h"
openacc_container_map __ipmacc_contmap;
#endif
