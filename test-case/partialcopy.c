#include <stdio.h>

void foo (int n, int *v) {
  int i;
  #pragma acc data copy(v[5:n])
  #pragma acc kernels
  #pragma acc loop independent
  for (i = 5; i < n; i++)
    v[i] = i;
}

int main() {
  int v[1000];
  foo (1000, v);
  return 0;
}
