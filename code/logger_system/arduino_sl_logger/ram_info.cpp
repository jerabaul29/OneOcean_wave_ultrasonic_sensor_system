#include "ram_info.h"

extern char _end;
extern "C" char *sbrk(int i);
char *ramstart=(char *)0x20070000;
char *ramend=(char *)0x20088000;

void print_ram_info(void){
    char *heapend=sbrk(0);
    register char * stack_ptr asm ("sp");
    struct mallinfo mi=mallinfo();
    printf("S Dynamic ram used: %d\n",mi.uordblks);
    printf("S Program static ram used %d\n",&_end - ramstart);
    printf("S Stack ram used %d\n",ramend - stack_ptr);
    printf("S My guess at free mem: %d\n",stack_ptr - heapend + mi.fordblks);
}
