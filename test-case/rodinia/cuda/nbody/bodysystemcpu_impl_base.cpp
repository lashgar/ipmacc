
#include <math_functions.h>

void bodyBodyInteraction(float accel[3], float posMass0[4], float posMass1[4], float softeningSquared)
{
    float r[3];

    // r_01  [3 FLOPS]
    r[0] = posMass1[0] - posMass0[0];
    r[1] = posMass1[1] - posMass0[1];
    r[2] = posMass1[2] - posMass0[2];

    // d^2 + e^2 [6 FLOPS]
    float distSqr = r[0] * r[0] + r[1] * r[1] + r[2] * r[2];
    distSqr += softeningSquared;

    // invDistCube =1/distSqr^(3/2)  [4 FLOPS (2 mul, 1 sqrt, 1 inv)]
    float invDist = (float)1.0 / (float)sqrtf((double)distSqr);
    float invDistCube =  invDist * invDist * invDist;

    // s = m_j * invDistCube [1 FLOP]
    float s = posMass1[3] * invDistCube;

    // (m_1 * r_01) / (d^2 + e^2)^(3/2)  [6 FLOPS]
    accel[0] += r[0] * s;
    accel[1] += r[1] * s;
    accel[2] += r[2] * s;
}

void _computeNBodyGravitation_openacc(float *m_pos,
        float *m_force,
        float m_softeningSquared,
        int m_numBodies)
{
    #pragma acc kernels copy(m_force[0:3*m_numBodies],m_pos[0:4*m_numBodies])
    #pragma acc loop independent
    for (int i = 0; i < m_numBodies; i++)
    {
        int indexForce = 3*i;

        float acc[3] = {0, 0, 0};

        // We unroll this loop 4X for a small performance boost.
        int j = 0;

        while (j < m_numBodies)
        {
            bodyBodyInteraction(acc, &m_pos[4*i], &m_pos[4*j], m_softeningSquared);
            j++;
            bodyBodyInteraction(acc, &m_pos[4*i], &m_pos[4*j], m_softeningSquared);
            j++;
            bodyBodyInteraction(acc, &m_pos[4*i], &m_pos[4*j], m_softeningSquared);
            j++;
            bodyBodyInteraction(acc, &m_pos[4*i], &m_pos[4*j], m_softeningSquared);
            j++;
        }

        m_force[indexForce  ] = acc[0];
        m_force[indexForce+1] = acc[1];
        m_force[indexForce+2] = acc[2];
    }
}
