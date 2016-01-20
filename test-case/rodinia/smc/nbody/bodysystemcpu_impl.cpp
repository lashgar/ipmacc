#define __CUDA_INTERNAL_COMPILATION__
#include "math_functions.h"
#undef __CUDA_INTERNAL_COMPILATION__
//#include <math_functions.h>
//#include "math.h"

#ifndef __CUDACC__
typedef struct {
    float x;
    float y;
    float z;
} float3;
typedef struct {
    float x;
    float y;
    float z;
    float w;
} float4;
#endif

//#include "bodysystemcpu_impl.h"

void bodyBodyInteraction(float3 *accel, float4 posMass0, float4 posMass1, float softeningSquared)
{
    float3 r;

    // r_01  [3 FLOPS]
    r.x = posMass1.x - posMass0.x;
    r.y = posMass1.y - posMass0.y;
    r.z = posMass1.z - posMass0.z;

    // d^2 + e^2 [6 FLOPS]
    float distSqr = r.x * r.x + r.y * r.y + r.z * r.z;
    distSqr += softeningSquared;

    // invDistCube =1/distSqr^(3/2)  [4 FLOPS (2 mul, 1 sqrt, 1 inv)]
    //float invDist = (float)1.0 / (float)rsqrtf(distSqr);
    float invDist = rsqrtf(distSqr);
    float invDistCube =  invDist * invDist * invDist;

    // s = m_j * invDistCube [1 FLOP]
    float s = posMass1.w * invDistCube;

    // (m_1 * r_01) / (d^2 + e^2)^(3/2)  [6 FLOPS]
    accel->x += r.x * s;
    accel->y += r.y * s;
    accel->z += r.z * s;
}


float3 bodyBodyInteraction_ret(float4 posMass0, float4 posMass1, float softeningSquared)
{
    float3 r;
    float3 accel;

    // r_01  [3 FLOPS]
    r.x = posMass1.x - posMass0.x;
    r.y = posMass1.y - posMass0.y;
    r.z = posMass1.z - posMass0.z;

    // d^2 + e^2 [6 FLOPS]
    float distSqr = r.x * r.x + r.y * r.y + r.z * r.z;
    distSqr += softeningSquared;

    // invDistCube =1/distSqr^(3/2)  [4 FLOPS (2 mul, 1 sqrt, 1 inv)]
    //float invDist = (float)1.0 / (float)rsqrtf(distSqr);
    float invDist = rsqrtf(distSqr);
    float invDistCube =  invDist * invDist * invDist;

    // s = m_j * invDistCube [1 FLOP]
    float s = posMass1.w * invDistCube;

    // (m_1 * r_01) / (d^2 + e^2)^(3/2)  [6 FLOPS]
    accel.x = r.x * s;
    accel.y = r.y * s;
    accel.z = r.z * s;

    return accel;
}


#define TILESIZE    256
#define TILESIZELOG 8
void _computeNBodyGravitation_openacc(float *m_pos_f,
        float *m_force_f,
        float m_softeningSquared,
        int m_numBodies)
{
    float3* m_force=(float3*)m_force_f;
    float4* m_pos=(float4*)m_pos_f;

    //#pragma acc kernels present(m_force[0:m_numBodies],m_pos[0:m_numBodies])
    #pragma acc data pcopyin(m_force[0:m_numBodies],m_pos[0:m_numBodies])
    #pragma acc kernels present(m_force[0:m_numBodies],m_pos[0:m_numBodies])
    #pragma acc loop independent vector(TILESIZE)
    for (int i = 0; i < m_numBodies; i++)
    {
        //int indexForce = 3*i;

        float3 acc; //[3] = {0, 0, 0};
        acc.x = acc.y = acc.z = 0;
        float4 pos_p = m_pos[i];
        
        
        for(int tile = 0; tile <= ((m_numBodies>>TILESIZELOG)+1); tile++){
            int bound = ((tile+1)*TILESIZE)<m_numBodies ? ((tile+1)*TILESIZE) : m_numBodies;
            //#pragma acc cache (m_pos[0:m_numBodies:FETCH_CHANNEL:(tile*TILESIZE):0:0:false:0:0])
            //#pragma acc cache (m_pos[0:m_numBodies:FETCH_CHANNEL:(tile*TILESIZE):0:0:false:0:0])
            #pragma acc cache (m_pos[0:m_numBodies:FETCH_CHANNEL:(tile*TILESIZE):0:TILESIZE:true:0:0])
            {
                for(int j=( tile*TILESIZE); j<bound; j++){
                    //bodyBodyInteraction(&acc, pos_p, m_pos[j], m_softeningSquared);
                    float3 acc_c = bodyBodyInteraction_ret( pos_p, m_pos[j], m_softeningSquared);
                    acc.x += acc_c.x;
                    acc.y += acc_c.y;
                    acc.z += acc_c.z;
                }
            }
        }
        
        
        

        
        /*
        int j = 0;
        // We unroll this loop 4X for a small performance boost.
        #pragma unroll 128
        for(j=0; j< m_numBodies; j++)
        {
            float3 acc_c = bodyBodyInteraction_ret( pos_p, m_pos[j], m_softeningSquared);
            acc.x += acc_c.x;
            acc.y += acc_c.y;
            acc.z += acc_c.z;
            //j++;
            //bodyBodyInteraction(&acc, pos_p, m_pos[j], m_softeningSquared);
            //j++;
            //bodyBodyInteraction(&acc, pos_p, m_pos[j], m_softeningSquared);
            //j++;
            //bodyBodyInteraction(&acc, pos_p, m_pos[j], m_softeningSquared);
            //j++;
        }
        */
        
        

        //m_force[i]   = acc;  
        m_force[i].x = acc.x;
        m_force[i].y = acc.y;
        m_force[i].z = acc.z;
    }
}


void _updateNBodyGravitation_openacc(float *m_pos_f,
        float *m_force_f,
        float *m_vel_f,
        float m_softeningSquared,
        int m_numBodies,
        float m_damping,
        float deltaTime)
{
    //float3* m_force=(float3*)m_force_f;
    //float3* m_vel  =(float3*)m_vel_f;
    //float4* m_pos  =(float4*)m_pos_f;
    float* m_force=(float*)m_force_f;
    float* m_vel  =(float*)m_vel_f;
    float* m_pos  =(float*)m_pos_f;

        //#pragma acc kernels pcopyin(m_force[0:m_numBodies],m_vel[0:m_numBodies]) pcopyout(m_pos[0:m_numBodies])
        #pragma acc kernels pcopyin(m_force[0:m_numBodies*3],m_vel[0:m_numBodies*4],m_pos[0:m_numBodies*4]) pcopyout(m_pos[0:m_numBodies*4])
        #pragma acc loop independent
        for (int i = 0; i < m_numBodies; ++i)
        {
        int index = 4*i;
        int indexForce = 3*i;


        float pos[3], vel[3], force[3];
        pos[0] =    m_pos[index+0];
        pos[1] =    m_pos[index+1];
        pos[2] =    m_pos[index+2];
        float invMass = m_pos[index+3];

        vel[0] = m_vel[index+0];
        vel[1] = m_vel[index+1];
        vel[2] = m_vel[index+2];

        force[0] = m_force[indexForce+0];
        force[1] = m_force[indexForce+1];
        force[2] = m_force[indexForce+2];

        // acceleration = force / mass;
        // new velocity = old velocity + acceleration * deltaTime
        vel[0] += (force[0] * invMass) * deltaTime;
        vel[1] += (force[1] * invMass) * deltaTime;
        vel[2] += (force[2] * invMass) * deltaTime;

        vel[0] *= m_damping;
        vel[1] *= m_damping;
        vel[2] *= m_damping;

        // new position = old position + velocity * deltaTime
        pos[0] += vel[0] * deltaTime;
        pos[1] += vel[1] * deltaTime;
        pos[2] += vel[2] * deltaTime;

        m_pos[index+0] = pos[0];
        m_pos[index+1] = pos[1];
        m_pos[index+2] = pos[2];

        m_vel[index+0] = vel[0];
        m_vel[index+1] = vel[1];
        m_vel[index+2] = vel[2];

            /*
            float4 pos;
            float3 vel, force;
            pos =    m_pos[i];
            float invMass = pos.w;

            vel = m_vel[i];
            force = m_force[i];

            // acceleration = force / mass;
            // new velocity = old velocity + acceleration * deltaTime
            vel.x += (force.x * invMass) * deltaTime;
            vel.y += (force.y * invMass) * deltaTime;
            vel.z += (force.z * invMass) * deltaTime;

            vel.x *= m_damping;
            vel.y *= m_damping;
            vel.z *= m_damping;

            // new position = old position + velocity * deltaTime
            pos.x += vel.x * deltaTime;
            pos.y += vel.y * deltaTime;
            pos.z += vel.z * deltaTime;

            m_pos[i].x = pos.x;
            m_pos[i].y = pos.y;
            m_pos[i].z = pos.z;
            m_vel[i].x = vel.x;
            m_vel[i].y = vel.y;
            m_vel[i].z = vel.z;
        */
            
        }
}
