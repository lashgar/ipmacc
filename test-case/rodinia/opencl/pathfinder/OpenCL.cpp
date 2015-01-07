#include "OpenCL.h"

OpenCL::OpenCL(int displayOutput)
{
	VERBOSE = displayOutput;
}

OpenCL::~OpenCL()
{
	// Flush and kill the command queue...
	clFlush(command_queue);
	clFinish(command_queue);
	
	// Release each kernel in the map kernelArray
	map<string, cl_kernel>::iterator it;
	for ( it=kernelArray.begin() ; it != kernelArray.end(); it++ )
		clReleaseKernel( (*it).second );
		
	// Now the program...
	clReleaseProgram(program);
	
	// ...and finally, the queue and context.
	clReleaseCommandQueue(command_queue);
	clReleaseContext(context);
}

size_t OpenCL::localSize()
{
	return this->lwsize;
}

cl_command_queue OpenCL::q()
{
	return this->command_queue;
}

void OpenCL::launch(string toLaunch)
{
	// Launch the kernel (or at least enqueue it).
	ret = clEnqueueNDRangeKernel(command_queue, 
	                             kernelArray[toLaunch],
	                             1,
	                             NULL,
	                             &gwsize,
	                             &lwsize,
	                             0, 
	                             NULL, 
	                             NULL);
	
	if (ret != CL_SUCCESS)
	{
		printf("\nError attempting to launch %s. Error in clCreateProgramWithSource with error code %i\n\n", toLaunch.c_str(), ret);
		exit(1);
	}
}

void OpenCL::gwSize(size_t theSize)
{
	this->gwsize = theSize;
}

cl_context OpenCL::ctxt()
{
	return this->context;
}

cl_kernel OpenCL::kernel(string kernelName)
{
	return this->kernelArray[kernelName];
}

void OpenCL::createKernel(string kernelName)
{
	cl_kernel kernel = clCreateKernel(this->program, kernelName.c_str(), NULL);
	kernelArray[kernelName] = kernel;
	
	// Get the kernel work group size.
	clGetKernelWorkGroupInfo(kernelArray[kernelName], __ipmacc_cldevs[0], CL_KERNEL_WORK_GROUP_SIZE, sizeof(size_t), &lwsize, NULL);
	if (lwsize == 0)
	{
		cout << "Error: clGetKernelWorkGroupInfo() returned a max work group size of zero!" << endl;
		exit(1);
	}
	
	// Local work size must divide evenly into global work size.
	size_t howManyThreads = lwsize;
	if (lwsize > gwsize)
	{
		lwsize = gwsize;
		printf("Using %zu for local work size. \n", lwsize);
	}
	else
	{
		//while (gwsize % howManyThreads != 0)
		//{
		//	howManyThreads--;
		//}
		//if (VERBOSE)
		//	printf("Max local threads is %zu. Using %zu for local work size. \n", lwsize, howManyThreads);

		//this->lwsize = howManyThreads;
        this->lwsize = 256;
	}
}

void OpenCL::buildKernel()
{
	/* Load the source code for all of the kernels into the array source_str */
	FILE*  theFile;
	char*  source_str;
	size_t source_size;
	
	theFile = fopen("kernels.cl", "r");
	if (!theFile)
	{
		fprintf(stderr, "Failed to load kernel file.\n");
		exit(1);
	}
	// Obtain length of source file.
	fseek(theFile, 0, SEEK_END);
	source_size = ftell(theFile);
	rewind(theFile);
	// Read in the file.
	source_str = (char*) malloc(sizeof(char) * source_size);
	printf("file size: %u\n", source_size);
	fread(source_str, 1, source_size, theFile);
	fclose(theFile);

	// Create a program from the kernel source.
	program = clCreateProgramWithSource(context,
	                                    1,
	                                    (const char **) &source_str,
	                                    NULL,           // Number of chars in kernel src. NULL means src is null-terminated.
	                                    &ret);          // Return status message in the ret variable.

	if (ret != CL_SUCCESS)
	{
		printf("\nError at clCreateProgramWithSource! Error code %i\n\n", ret);
		exit(1);
	}

	// Memory cleanup for the variable used to hold the kernel source.
	free(source_str);
	
	// Build (compile) the program.
	// depreciated
	//ret = clBuildProgram(program, 0, NULL, NULL, NULL, NULL);
	//if (ret != CL_SUCCESS)
	//{
	//	printf("\nError at clBuildProgram! Error code %i\n\n", ret);
	//	cout << "\n*************************************************" << endl;
	//	cout << "***   OUTPUT FROM COMPILING THE KERNEL FILE   ***" << endl;
	//	cout << "*************************************************" << endl;
	//	// Shows the log
	//	char*  build_log;
	//	size_t log_size;
	//	// First call to know the proper size
	//	clGetProgramBuildInfo(program, device_id[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
	//	build_log = new char[log_size + 1];
	//	// Second call to get the log
	//	clGetProgramBuildInfo(program, device_id[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
	//	build_log[log_size] = '\0';
	//	cout << build_log << endl;
	//	delete[] build_log;
	//	cout << "\n*************************************************" << endl;
	//	cout << "*** END OUTPUT FROM COMPILING THE KERNEL FILE ***" << endl;
	//	cout << "*************************************************\n\n" << endl;
	//	exit(1);
	//}
        char __ipmacc_clcompileflags0[128];
        sprintf(__ipmacc_clcompileflags0, " ");
        cl_uint __ipmacc_clerr=clBuildProgram(program, 0, NULL, __ipmacc_clcompileflags0, NULL, NULL);
        if(__ipmacc_clerr!=CL_SUCCESS){
                printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);

                size_t log_size=1024;
                char *build_log=NULL;
                __ipmacc_clerr=clGetProgramBuildInfo(program, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
                if(__ipmacc_clerr!=CL_SUCCESS){
                        printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
                }
                build_log = (char*)malloc((log_size+1));
                // Second call to get the log
                __ipmacc_clerr=clGetProgramBuildInfo(program, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
                if(__ipmacc_clerr!=CL_SUCCESS){
                        printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
                }
                build_log[log_size] = '\0';
                printf("--- Build log (%d)---\n ",log_size);
                fprintf(stderr, "%s\n", build_log);
                free(build_log);exit(-1);
        }
	// END OF REPLACER




	/* Show error info from building the program. */
	//if (VERBOSE)
	//{
	//	cout << "\n*************************************************" << endl;
	//	cout << "***   OUTPUT FROM COMPILING THE KERNEL FILE   ***" << endl;
	//	cout << "*************************************************" << endl;
	//	// Shows the log
	//	char*  build_log;
	//	size_t log_size;
	//	// First call to know the proper size
	//	clGetProgramBuildInfo(program, device_id[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
	//	build_log = new char[log_size + 1];
	//	// Second call to get the log
	//	clGetProgramBuildInfo(program, device_id[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
	//	build_log[log_size] = '\0';
	//	cout << build_log << endl;
	//	delete[] build_log;
	//	cout << "\n*************************************************" << endl;
	//	cout << "*** END OUTPUT FROM COMPILING THE KERNEL FILE ***" << endl;
	//	cout << "*************************************************\n\n" << endl;
	//}
}

void OpenCL::getDevices(cl_device_type deviceType)
{
	cl_uint         platforms_n = 0;
	cl_uint         devices_n   = 0;
	
	/* The following code queries the number of platforms and devices, and
	 * lists the information about both.
	 */
/*
	clGetPlatformIDs(100, platform_id, &platforms_n);
	if (VERBOSE)
	{
		printf("\n=== %d OpenCL platform(s) found: ===\n", platforms_n);
		for (int i = 0; i < platforms_n; i++)
		{
			char buffer[10240];
			printf("  -- %d --\n", i);
			clGetPlatformInfo(platform_id[i], CL_PLATFORM_PROFILE, 10240, buffer,
			                  NULL);
			printf("  PROFILE = %s\n", buffer);
			clGetPlatformInfo(platform_id[i], CL_PLATFORM_VERSION, 10240, buffer,
			                  NULL);
			printf("  VERSION = %s\n", buffer);
			clGetPlatformInfo(platform_id[i], CL_PLATFORM_NAME, 10240, buffer, NULL);
			printf("  NAME = %s\n", buffer);
			clGetPlatformInfo(platform_id[i], CL_PLATFORM_VENDOR, 10240, buffer, NULL);
			printf("  VENDOR = %s\n", buffer);
			clGetPlatformInfo(platform_id[i], CL_PLATFORM_EXTENSIONS, 10240, buffer,
			                  NULL);
			printf("  EXTENSIONS = %s\n", buffer);
		}
	}
	
	clGetDeviceIDs(platform_id[0], deviceType, 100, device_id, &devices_n);
	if (VERBOSE)
	{
		printf("Using the default platform (platform 0)...\n\n");
		printf("=== %d OpenCL device(s) found on platform:\n", devices_n);
		for (int i = 0; i < devices_n; i++)
		{
			char buffer[10240];
			cl_uint buf_uint;
			cl_ulong buf_ulong;
			printf("  -- %d --\n", i);
			clGetDeviceInfo(device_id[i], CL_DEVICE_NAME, sizeof(buffer), buffer,
			                NULL);
			printf("  DEVICE_NAME = %s\n", buffer);
			clGetDeviceInfo(device_id[i], CL_DEVICE_VENDOR, sizeof(buffer), buffer,
			                NULL);
			printf("  DEVICE_VENDOR = %s\n", buffer);
			clGetDeviceInfo(device_id[i], CL_DEVICE_VERSION, sizeof(buffer), buffer,
			                NULL);
			printf("  DEVICE_VERSION = %s\n", buffer);
			clGetDeviceInfo(device_id[i], CL_DRIVER_VERSION, sizeof(buffer), buffer,
			                NULL);
			printf("  DRIVER_VERSION = %s\n", buffer);
			clGetDeviceInfo(device_id[i], CL_DEVICE_MAX_COMPUTE_UNITS,
			                sizeof(buf_uint), &buf_uint, NULL);
			printf("  DEVICE_MAX_COMPUTE_UNITS = %u\n", (unsigned int) buf_uint);
			clGetDeviceInfo(device_id[i], CL_DEVICE_MAX_CLOCK_FREQUENCY,
			                sizeof(buf_uint), &buf_uint, NULL);
			printf("  DEVICE_MAX_CLOCK_FREQUENCY = %u\n", (unsigned int) buf_uint);
			clGetDeviceInfo(device_id[i], CL_DEVICE_GLOBAL_MEM_SIZE,
			                sizeof(buf_ulong), &buf_ulong, NULL);
			printf("  DEVICE_GLOBAL_MEM_SIZE = %llu\n",
			       (unsigned long long) buf_ulong);
			clGetDeviceInfo(device_id[i], CL_DEVICE_LOCAL_MEM_SIZE,
			                sizeof(buf_ulong), &buf_ulong, NULL);
			printf("  CL_DEVICE_LOCAL_MEM_SIZE = %llu\n",
			       (unsigned long long) buf_ulong);
		}
		printf("\n");
	}
*/	
/*
	// Create an OpenCL context.
//	context = clCreateContext(NULL, devices_n, device_id, NULL, NULL, &ret);
        cl_device_id device_id = NULL;   
        cl_uint ret_num_devices;
	cl_platform_id platform_id_s;
	//cl_platform_id platform_id;
	if (clGetPlatformIDs(1, &platform_id_s, NULL) != CL_SUCCESS) { printf("ERROR: clGetPlatformIDs(1,*,0) failed\n"); exit(-1);}
	cl_context_properties ctxprop[] = { CL_CONTEXT_PLATFORM, (cl_context_properties)platform_id_s, 0};
	//device_type = use_gpu ? CL_DEVICE_TYPE_GPU : CL_DEVICE_TYPE_CPU;

        ret = clGetDeviceIDs( platform_id_s, CL_DEVICE_TYPE_DEFAULT, 1, &device_id, &ret_num_devices);
        if(ret!=CL_SUCCESS){
            printf("Runtime error! unable to retrieve the device id of CL_DEVICE_TYPE_DEFAULT\n");
            exit(-1);
        }
	cl_device_id* __ipmacc_cldevs;
        __ipmacc_cldevs=(cl_device_id*)malloc(sizeof(cl_device_id)*1);
	__ipmacc_cldevs[0]=device_id;
        context = clCreateContext( NULL, 1, &device_id, NULL, NULL, &ret);
        if(ret!=CL_SUCCESS){
            printf("Runtime error! Cannot open context on the device %d of CL_DEVICE_TYPE_DEFAULT\n",device_id);
            exit(-1);
        }
//	if (ret != CL_SUCCESS)
//	{
//		printf("\nError at clCreateContext! Error code %i\n\n", ret);
//		exit(1);
//	}
	// Create a command queue.
	command_queue = clCreateCommandQueue(context, __ipmacc_cldevs[0], 0, &ret);
	if (ret != CL_SUCCESS)
	{
		printf("\nError at clCreateCommandQueue! Error code %i\n\n", ret);
		exit(1);
	}

 */



/// HIHA
	cl_int result;
	size_t size;

	// create OpenCL context
	cl_platform_id platform_id;
	if (clGetPlatformIDs(1, &platform_id, NULL) != CL_SUCCESS) { printf("ERROR: clGetPlatformIDs(1,*,0) failed\n"); exit(-1); }
	cl_context_properties ctxprop[] = { CL_CONTEXT_PLATFORM, (cl_context_properties)platform_id, 0};
	//device_type = 1==1 ? CL_DEVICE_TYPE_GPU : CL_DEVICE_TYPE_CPU;

	// DEPRECIATED
	// This:
	// context = clCreateContextFromType( ctxprop, device_type, NULL, NULL, NULL );
	// if( !context ) { printf("ERROR: clCreateContextFromType(%s) failed\n", use_gpu ? "GPU" : "CPU"); exit(-1); }
	// is replaced by this:
        // Create an OpenCL context
        cl_device_id device_id = NULL;   
        cl_uint ret_num_devices;
        result = clGetDeviceIDs( platform_id, CL_DEVICE_TYPE_DEFAULT, 1, &device_id, &ret_num_devices);
        if(result!=CL_SUCCESS){
            printf("Runtime error! unable to retrieve the device id of CL_DEVICE_TYPE_DEFAULT\n");
            exit(-1);
        }
        __ipmacc_cldevs=(cl_device_id*)malloc(sizeof(cl_device_id)*1);
	__ipmacc_cldevs[0]=device_id;
        context = clCreateContext( NULL, 1, &device_id, NULL, NULL, &result);
        if(result!=CL_SUCCESS){
            printf("Runtime error! Cannot open context on the device %d of CL_DEVICE_TYPE_DEFAULT\n",device_id);
            exit(-1);
        }
	// END OF CODE


	// get the list of GPUs
	result = clGetContextInfo( context, CL_CONTEXT_DEVICES, 0, NULL, &size );
	int num_devices = (int) (size / sizeof(cl_device_id));
	printf("num_devices = %d\n", num_devices);
	
	if( result != CL_SUCCESS || num_devices < 1 ) { printf("ERROR: clGetContextInfo() failed\n"); exit(-1); }
	device_list = new cl_device_id[num_devices];
	//device_list = (cl_device_id *)malloc(sizeof(cl_device_id)*num_devices);
	if( !device_list ) { printf("ERROR: new cl_device_id[] failed\n"); exit(-1); }
	result = clGetContextInfo( context, CL_CONTEXT_DEVICES, size, device_list, NULL );
	if( result != CL_SUCCESS ) { printf("ERROR: clGetContextInfo() failed\n"); exit(-1); }

	// create command queue for the first device
	command_queue = clCreateCommandQueue( context, device_list[0], 0, NULL );
	if( !command_queue ) { printf("ERROR: clCreateCommandQueue() failed\n"); exit(-1); }
	//return 0;




/// HOHA














}

void OpenCL::init(int isGPU)
{
	if (isGPU)
		getDevices(CL_DEVICE_TYPE_GPU);
	else
		getDevices(CL_DEVICE_TYPE_CPU);

	buildKernel();
}
