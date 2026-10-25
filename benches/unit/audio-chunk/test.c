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
		uint32_t o, z;

		o = 0; z = 1920;
		CHECK(audio_chunk_fit(&o, &z, 1920) && o == 0 && z == 1920, "8. fit: a chunk that fits is unchanged");
		o = 1000; z = 5000;
		CHECK(audio_chunk_fit(&o, &z, 1920) && o == 1000 && z == 920, "8b. fit: too long is cut to the buffer");
		o = 4000; z = 100;
		CHECK(audio_chunk_fit(&o, &z, 1920) && o == 160 && z == 100, "8c. fit: offset is taken modulo maxsize");
		o = 1; z = 100;
		CHECK(audio_chunk_fit(&o, &z, 1920) && o == 0 && z == 100, "8d. fit: odd offset is brought down to even");
		o = 0xFFFFFFFFu; z = 0xFFFFFFFFu;
		CHECK(audio_chunk_fit(&o, &z, 1920) && o + z <= 1920 && (o & 1u) == 0, "8e. fit: huge values end inside the buffer");
		o = 0; z = 10;
		CHECK(!audio_chunk_fit(&o, &z, 0), "8f. fit: maxsize 0 leaves nothing");
	}
	{
		FILE *f = fopen("src/sound.c", "r");
		static char src[2u << 20];
		size_t n;
		if (!f) { puts("(sound.c not found: run from the root of the tree)"); bad++; }
		else {
			n = fread(src, 1, sizeof src - 1, f); src[n] = 0; fclose(f);
			CHECK(strstr(src, "audio_chunk_fit(&chunk_offset, &chunk_size, piano->maxsize)") != NULL && strstr(src, "(const uint8_t *) piano->data + chunk_offset") != NULL, "7. sound.c reads only the reduced chunk");
		}
	}
	printf("%s\n", bad ? "FAILED" : "OK: all checks passed");
	return bad ? 1 : 0;
}
