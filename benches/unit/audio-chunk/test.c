/* test.c — audiochunk.h (audit of the session, S-R8).  Build: cc -std=gnu11 -fsanitize=address,undefined -fno-sanitize-recover=undefined -I src benches/unit/audio-chunk/test.c -o t && ./t
 * and src/sound.c must call audio_chunk_ok() with the chunk and piano->maxsize in the condition of the loop (source reading, last check). */
#include "audiochunk.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static int bad;
#define CHECK(c, w) do { if (!(c)) { bad++; printf("FAIL: %s\n", w); } } while (0)

int main(void)
{
	CHECK(audio_chunk_ok(0, 1920, 1920) && audio_chunk_ok(0, 0, 0) && audio_chunk_ok(1000, 920, 1920), "1. chunks that fit (also exactly)");
	CHECK(!audio_chunk_ok(0, 1921, 1920), "2. one byte more than the buffer");
	CHECK(!audio_chunk_ok(2, 1920, 1920), "3. offset pushes the end out");
	CHECK(!audio_chunk_ok(0xFFFFFFFEu, 4, 1920), "4. offset + size wraps in 32 bits: still refused");
	CHECK(!audio_chunk_ok(0, 0xFFFFFFFFu, 1920), "5. huge size");
	CHECK(!audio_chunk_ok(1, 4, 1920), "6. odd offset: int16 samples would be misaligned");
	{
		FILE *f = fopen("src/sound.c", "r");
		static char src[2u << 20];
		size_t n;
		if (!f) { puts("(sound.c not found: run from the root of the tree)"); bad++; }
		else {
			n = fread(src, 1, sizeof src - 1, f); src[n] = 0; fclose(f);
			CHECK(strstr(src, "audio_chunk_ok(piano->chunk->offset, piano->chunk->size, piano->maxsize)") != NULL, "7. sound.c uses it with the chunk and maxsize");
		}
	}
	printf("%s\n", bad ? "FAILED" : "OK: all checks passed");
	return bad ? 1 : 0;
}
