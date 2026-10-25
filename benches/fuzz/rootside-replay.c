/* rootside-replay.c — a main() for the rootside-* fuzz harnesses WITHOUT libFuzzer: every file named on the command line is fed to LLVMFuzzerTestOneInput(), once.
 * What a replay with `-runs=0` does, with gcc and the sanitizers alone (the tablet has no libFuzzer).  Exit 0 = no oracle fired (a failing oracle abort()s). */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

int main(int argc, char **argv)
{
	int n = 0;

	for (int i = 1; i < argc; i++) {
		FILE *f = fopen(argv[i], "rb");
		uint8_t *buf = NULL;
		size_t len = 0, cap = 0, r;

		if (!f) { fprintf(stderr, "cannot open %s\n", argv[i]); return 2; }
		do {
			if (len == cap) { cap = cap ? cap * 2 : 4096; buf = realloc(buf, cap); if (!buf) return 2; }
			r = fread(buf + len, 1, cap - len, f);
			len += r;
		} while (r > 0);
		fclose(f);
		(void)LLVMFuzzerTestOneInput(buf, len);
		free(buf);
		n++;
	}
	printf("replayed %d input(s), no oracle fired\n", n);
	return 0;
}
