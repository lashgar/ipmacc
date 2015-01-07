
#include <math_functions.h>

void bodyBodyInteraction(float3 &accel, float4 posMass0, float4 posMass1, float softeningSquared)
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
    float invDist = (float)1.0 / (float)sqrtf((double)distSqr);
    float invDistCube =  invDist * invDist * invDist;

    // s = m_j * invDistCube [1 FLOP]
    float s = posMass1.w * invDistCube;

    // (m_1 * r_01) / (d^2 + e^2)^(3/2)  [6 FLOPS]
    accel.x += r.x * s;
    accel.y += r.y * s;
    accel.z += r.z * s;
}

void _computeNBodyGravitation_openacc(float *m_pos_f,
        float *m_force_f,
        float m_softeningSquared,
        int m_numBodies)
{
    float3* m_force=(float3*)m_force_f;
    float4* m_pos=(float4*)m_pos_f;

    #pragma acc kernels copy(m_force[0:m_numBodies],m_pos[0:m_numBodies])
    #pragma acc loop independent smc(m_pos[0:m_numBodies:READ_ONLY:false])
    for (int i = 0; i < m_numBodies; i++)
    {
        //int indexForce = 3*i;

        float3 acc;//[3] = {0, 0, 0};
        acc.x=0;
        acc.y=0;
        acc.z=0;
        float4 mypos= m_pos[i];

        // We unroll this loop 4X for a small performance boost.
        int j = 0;

        #pragma acc smc_sweep(m_pos)
        for(j=0; j<m_numBodies; j++){
            bodyBodyInteraction(acc, mypos, m_pos[j], m_softeningSquared);
            //j++;
            //bodyBodyInteraction(acc, mypos, m_pos[j], m_softeningSquared);
            //j++;
            //bodyBodyInteraction(acc, mypos, m_pos[j], m_softeningSquared);
            //j++;
            //bodyBodyInteraction(acc, mypos, m_pos[j], m_softeningSquared);
            //j++;
        }

        m_force[i].x = acc.x;
        m_force[i].y = acc.y;
        m_force[i].z = acc.z;
    }
}
