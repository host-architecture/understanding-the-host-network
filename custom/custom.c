#include <immintrin.h>
#include <stdlib.h>
#include <stdio.h>

int main() {

    char *memarea = NULL;
    if(posix_memalign(&memarea, 64, 1024*1024*1024) != 0) {
        printf("Failed to allocate mem region\n");
        exit(-1);
    }

    _mm512_load_epi64(memarea);

    return 0;
}