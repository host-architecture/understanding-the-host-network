#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>

int main() {
    int configfd;
    configfd = open("/sys/kernel/debug/miomap", O_RDWR);
    if(configfd < 0) {
        perror("open");
    return -1;
    }

    char * address = NULL;
    address = mmap(NULL, 16*1024*1024, PROT_READ|PROT_WRITE, MAP_SHARED, configfd, 0);
    if (address == MAP_FAILED) {
        perror("mmap");
        return -1;
    }
    address[0] = 'm';
    printf("Successful mmap\n");
    sleep(15);
    return 0;
}
