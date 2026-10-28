/*
 * 28-damage-test.c — ⭐ [M] 28 Oct 2026: `damage_classify()` of `src/capture.c`
 *                    (extracted by `make test-damage`) on synthetic metadata.
 *
 * KWin sends the VideoDamage meta for unchanged frames too, holding only the
 * 0,0,0,0 terminator: that must read EMPTY, not ABSENT.
 *
 *   cd src && make test-damage
 */
#include <glib.h>
#include <stdio.h>
#include <string.h>
#include <spa/buffer/meta.h>
#include "capture.h"

#define MAX_REGIONS CAPTURE_DAMAGE_MAX
#include "damage-extract.c"

static int failures;
#define CHECK(c, what) do { if (!(c)) { printf("  FAIL: %s\n", what); failures++; } \
                            else printf("  ok:   %s\n", what); } while (0)

/* A meta with `n` regions followed by the 0,0,0,0 terminator (room for n+1). */
static struct spa_meta make(struct spa_meta_region *slots, int n, int rect[][4])
{
	struct spa_meta m;
	int i;

	memset(slots, 0, (n + 1) * sizeof *slots);
	for (i = 0; i < n; i++)
	{
		slots[i].region.position.x = rect[i][0];
		slots[i].region.position.y = rect[i][1];
		slots[i].region.size.width = rect[i][2];
		slots[i].region.size.height = rect[i][3];
	}
	m.type = SPA_META_VideoDamage;
	m.size = (n + 1) * sizeof *slots;
	m.data = slots;
	return m;
}

int main(void)
{
	CaptureRegion r[MAX_REGIONS];
	struct spa_meta_region slots[MAX_REGIONS + 3];
	struct spa_meta m;
	guint n = 99;
	gboolean all = TRUE;
	int k;

	printf("damage_classify:\n");
	k = damage_classify(NULL, 1920, 1080, r, &n, &all);
	CHECK(k == DAMAGE_ABSENT && n == 0 && !all, "meta absent => ABSENT");

	m = make(slots, 0, NULL);
	k = damage_classify(&m, 1920, 1080, r, &n, &all);
	CHECK(k == DAMAGE_EMPTY && n == 0 && !all, "terminator only => EMPTY");

	{ int rc[][4] = { { 10, 20, 100, 50 } };
	  m = make(slots, 1, rc);
	  k = damage_classify(&m, 1920, 1080, r, &n, &all);
	  CHECK(k == DAMAGE_PRESENT && n == 1 && !all && r[0].x == 10 && r[0].y == 20
	        && r[0].width == 100 && r[0].height == 50, "partial region => PRESENT, not all"); }

	{ int rc[][4] = { { 0, 0, 1920, 1080 } };
	  m = make(slots, 1, rc);
	  k = damage_classify(&m, 1920, 1080, r, &n, &all);
	  CHECK(k == DAMAGE_PRESENT && n == 1 && all, "full region => PRESENT, covers all"); }

	{ int rc[MAX_REGIONS + 1][4]; int i;
	  for (i = 0; i <= MAX_REGIONS; i++) { rc[i][0] = i; rc[i][1] = 0; rc[i][2] = 2; rc[i][3] = 2; }
	  m = make(slots, MAX_REGIONS + 1, rc);
	  k = damage_classify(&m, 1920, 1080, r, &n, &all);
	  CHECK(k == DAMAGE_PRESENT && n == 0 && all, "too many regions => PRESENT, covers all"); }

	printf(failures ? "FAILED (%d)\n" : "ALL OK\n", failures);
	return failures ? 1 : 0;
}
