#include <stdio.h>

int
main(void)
{
	char *foo;
	asprintf(&foo, "%d", 1);
	return 0;
}
