/*
 * test.c — 64-bit arithmetic on the sizes of a frame (src/dimcheck.h), audit of 25 Oct 2026, part E, E-R6 and E-R3.
 * What is checked, on the REAL header (nothing copied):
 *   1. dim_stride_ok: a width of 2^30 (width * 4u would wrap to 0) is refused with a small stride; the exact stride passes; zero width refused;
 *   2. dim_object_size: offset + stride * height over 2^32 is refused (it used to wrap to a small size); the largest fitting value passes; zeros refused;
 *   3. dim_frame_ok: consistent frame passes; stride too short, bytes too few, zero sizes fail; over the maximum canvas fails (E-R3), at the maximum passes, max 0 = no maximum;
 *      stride * height over 2^32 with enough 64-bit bytes passes (no wrap in the product);
 *   4. by reading the sources (argv[1] = src/encoder.c, argv[2] = src/capture.c, argv[3] = src/child.c, optional): the places the audit named use the header
 *      and no longer the 32-bit expressions.
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *        -I/albero/src /albero/benches/unit/dim-check/test.c -o test && ./test /albero/src/encoder.c /albero/src/capture.c /albero/src/child.c'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "dimcheck.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures, passed;

static void check(int cond, const char *what)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", what);
	if (cond)
		passed++;
	else
		failures++;
}

static char *slurp(const char *path)
{
	FILE *f = fopen(path, "rb");
	long n;
	char *b;

	if (!f)
		return NULL;
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	fseek(f, 0, SEEK_SET);
	b = calloc(1, (size_t)n + 1);
	if (b && fread(b, 1, (size_t)n, f) != (size_t)n) {
		free(b);
		b = NULL;
	}
	fclose(f);
	return b;
}

int main(int argc, char **argv)
{
	uint32_t sz = 7;

	check(!dim_stride_ok(64, 1u << 30), "stride 64 with width 2^30: refused (width * 4u wraps to 0 in 32 bits)");
	check(!dim_stride_ok(0xffffffffu, 0x40000000u) , "width 2^30 needs 2^32 bytes of stride: 2^32-1 is refused");
	check(dim_stride_ok(7680, 1920), "exact stride passes");
	check(dim_stride_ok(8192, 1920), "padded stride passes");
	check(!dim_stride_ok(7676, 1920), "4 bytes short fails");
	check(!dim_stride_ok(7680, 0), "zero width refused");

	check(!dim_object_size(0, 0x10000, 0x10000, &sz) && sz == 7, "stride * height = 2^32: refused, size untouched");
	check(!dim_object_size(70000, 0x10000, 0xffff, &sz) && sz == 7, "offset pushes it over 2^32: refused");
	check(dim_object_size(4096, 7680, 2160, &sz) && sz == 4096u + 7680u * 2160u, "a 1920x2160 object: 16 MiB + offset");
	check(dim_object_size(0, 0xffffffffu, 1, &sz) && sz == 0xffffffffu, "the largest value that fits passes");
	check(!dim_object_size(1, 0xffffffffu, 1, &sz), "one more fails");
	check(!dim_object_size(0, 0, 100, &sz) && !dim_object_size(0, 100, 0, &sz), "zero stride or height refused");

	check(dim_frame_ok(3840, 2160, 15360, (uint64_t)15360 * 2160, 4096, 2304), "4K frame within the canvas maximum passes");
	check(!dim_frame_ok(3840, 2160, 15356, (uint64_t)15360 * 2160, 4096, 2304), "stride too short fails");
	check(!dim_frame_ok(3840, 2160, 15360, (uint64_t)15360 * 2160 - 1, 4096, 2304), "one byte too few fails");
	check(!dim_frame_ok(0, 2160, 15360, 1u << 30, 4096, 2304) && !dim_frame_ok(3840, 0, 15360, 1u << 30, 4096, 2304), "zero width or height fails");
	check(!dim_frame_ok(16000, 4000, 64000, (uint64_t)64000 * 4000, 4096, 2304), "16000x4000 (a wlroots mode beyond the canvas) fails");
	check(dim_frame_ok(4096, 2304, 16384, (uint64_t)16384 * 2304, 4096, 2304), "exactly the maximum passes");
	check(!dim_frame_ok(4098, 2304, 16392, (uint64_t)16392 * 2304, 4096, 2304) && !dim_frame_ok(4096, 2306, 16384, (uint64_t)16384 * 2306, 4096, 2304),
	      "two pixels beyond in either direction fails");
	check(dim_frame_ok(16000, 4000, 64000, (uint64_t)64000 * 4000, 0, 0), "max 0 = no maximum");
	check(dim_frame_ok(2, 0x20000000u, 8, (uint64_t)8 * 0x20000000u, 0, 0), "stride * height over 2^32 with the 64-bit bytes present: no wrap in the product");

	for (int i = 1; i < argc && i <= 3; i++) {
		char *t = slurp(argv[i]);

		if (!t) {
			printf("    --  (cannot read %s: source check skipped)\n", argv[i]);
			continue;
		}
		if (i == 1) {
			check(strstr(t, "dim_object_size(") != NULL, "encoder.c imports the DMA-BUF through dim_object_size()");
			check(strstr(t, "s->offset + s->stride * s->height") == NULL, "encoder.c no longer computes the object size in 32 bits");
			check(strstr(t, "beyond the %ux%u the driver declared") != NULL, "encoder.c: codificatore_ridimensiona() checks zero and the driver maximum (E-R3)");
		} else if (i == 2) {
			check(strstr(t, "dim_stride_ok(step, capture->fmt.size.width)") != NULL, "capture.c: the memory-route guard uses dim_stride_ok()");
			check(strstr(t, "step < capture->fmt.size.width * 4u") == NULL, "capture.c: the 32-bit comparison is gone");
			check(strstr(t, "st < w * 4u") == NULL, "capture.c: the 32-bit comparison in the damage code is gone");
		} else {
			check(strstr(t, "dim_frame_ok(fo.width, fo.height, fo.stride, fo.byte, RCP_CANVAS_MAX_W") != NULL,
			      "child.c: the frame guard uses dim_frame_ok() with the canvas maximum (E-R3)");
		}
		free(t);
	}
	printf("\n  %d passed, %d failed\n", passed, failures);
	return failures ? 1 : 0;
}
