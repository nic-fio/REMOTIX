/* test.c — audiochunk.h (audit of the session, S-R8): audio_chunk_ok() refuses a chunk that does not fit in its buffer; audio_chunk_fit() reduces it to the buffer (offset modulo maxsize,
 * size cut to what is left, offset even).  The last check reads src/sound.c to see that the capture callback uses audio_chunk_fit() and reads only the reduced chunk: that is why it
 * runs from the root of the tree.
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /albero && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
 *        -Isrc benches/unit/audio-chunk/test.c -o /tmp/test && /tmp/test'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
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
