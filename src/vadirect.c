/*
 * vadirect.c — H.264 and HEVC on the card with libva directly.  The why is in
 * `vadirect.h`; here is the how, and next to every field the value that ffmpeg
 * 7.1 used to write for us (`[M]` 30 Sep 2026, traces of today's streams).
 *
 * The order of the file follows the order of a frame:
 *   1. the device and the configuration (once);
 *   2. the level, computed like `ff_h264_guess_level`/`ff_h265_guess_level`;
 *   3. the headers written bit by bit — H.264, then HEVC;
 *   4. the encoding round of one frame;
 *   5. the route from memory (the pixels that go up to the card).
 */
#include "vadirect.h"
#include "log.h"
#include "bit_writer.h"

#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <va/va_drm.h>
#include <va/va_enc_h264.h>
#include <va/va_enc_hevc.h>

#define LOG_ENCODING "video"

/* ⛔ How many RECONSTRUCTED surfaces the driver keeps for us: the current one and
 *    the reference (a single reference, no B — `encoder.h`, «latency
 *    weighs more than frames»).  Three and not two, for headroom on the
 *    drivers that keep one extra round in the pipe. */
#define REBUILT 3

/* How large the buffer of encoded bytes is: the same rule as ffmpeg
 * (`vaapi_encode_alloc_output_buffer`): 3 x width x height + 64 KiB —
 * an uncompressed frame is a ceiling for a compressed one. */
#define CODED_MARGIN (1u << 16)

static void di(char *dove, size_t how_much, const char *fmt, ...)
{
	va_list ap;

	if (!dove || !how_much)
		return;
	va_start(ap, fmt);
	vsnprintf(dove, how_much, fmt, ap);
	va_end(ap);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 1. THE DEVICE
 * ═══════════════════════════════════════════════════════════════════════════ */

bool vadirect_open_device(const char *node, VaDevice *d, char *error,
                                size_t error_byte)
{
	VAStatus st;
	const char *vendor;

	memset(d, 0, sizeof *d);
	d->fd = -1;
	if (!node || !node[0]) {
		di(error, error_byte, "no render node declared");
		return false;
	}
	d->fd = open(node, O_RDWR | O_CLOEXEC);
	if (d->fd < 0) {
		di(error, error_byte, "«%s» does not open: %s", node, strerror(errno));
		return false;
	}
	d->display = vaGetDisplayDRM(d->fd);
	if (!d->display) {
		di(error, error_byte, "vaGetDisplayDRM on «%s» returned no display", node);
		close(d->fd);
		d->fd = -1;
		return false;
	}
	st = vaInitialize(d->display, &d->greater, &d->less);
	if (st != VA_STATUS_SUCCESS) {
		di(error, error_byte, "VA-API did not open on «%s»: %s", node, vaErrorStr(st));
		close(d->fd);
		d->fd = -1;
		d->display = NULL;
		return false;
	}
	vendor = vaQueryVendorString(d->display);
	snprintf(d->vendor, sizeof d->vendor, "%s",
	         vendor ? vendor : "(the driver does not say its name)");
	return true;
}

void vadirect_close_device(VaDevice *d)
{
	if (!d)
		return;
	if (d->display)
		vaTerminate(d->display);
	if (d->fd >= 0)
		close(d->fd);
	d->display = NULL;
	d->fd = -1;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 2. THE LEVEL — how ffmpeg guessed it when nobody imposed one
 *
 * ⛔ Needed because `ffprobe -show_streams` must report the SAME level as
 *    yesterday even when the client declares none (the benches, and `RCP.md`
 *    §4.3 does not oblige the client).  The tables are A-1 of H.264 and A.4 of
 *    H.265, taken from ffmpeg's `h264_levels.c` and `h265_profile_level.c`;
 *    for HEVC Main and Main 10 are enough, the only profiles we open.
 * ═══════════════════════════════════════════════════════════════════════════ */

typedef struct {
	int level_idc, cs3f;
	int max_mbps, max_fs, max_dpb_mbs, max_br;
} H264Level;

static const H264Level H264_LEVELS[] = {
	{ 10, 0, 1485, 99, 396, 64 },          { 11, 1, 1485, 99, 396, 128 },
	{ 9, 0, 1485, 99, 396, 128 },          { 11, 0, 3000, 396, 900, 192 },
	{ 12, 0, 6000, 396, 2376, 384 },       { 13, 0, 11880, 396, 2376, 768 },
	{ 20, 0, 11880, 396, 2376, 2000 },     { 21, 0, 19800, 792, 4752, 4000 },
	{ 22, 0, 20250, 1620, 8100, 4000 },    { 30, 0, 40500, 1620, 8100, 10000 },
	{ 31, 0, 108000, 3600, 18000, 14000 }, { 32, 0, 216000, 5120, 20480, 20000 },
	{ 40, 0, 245760, 8192, 32768, 20000 }, { 41, 0, 245760, 8192, 32768, 50000 },
	{ 42, 0, 522240, 8704, 34816, 50000 }, { 50, 0, 589824, 22080, 110400, 135000 },
	{ 51, 0, 983040, 36864, 184320, 240000 }, { 52, 0, 2073600, 36864, 184320, 240000 },
	{ 60, 0, 4177920, 139264, 696320, 240000 }, { 61, 0, 8355840, 139264, 696320, 480000 },
	{ 62, 0, 16711680, 139264, 696320, 800000 },
};

/* `ff_h264_guess_level(100, bitrate, fps, mbw*16, mbh*16, dpb=1)`.
 * ⚠ 1500 is the NAL factor of High (table A-2); the Baseline/Main profiles
 *   would have 1200, but High is the only one we open. */
static int h264_level(int64_t bitrate, int fps, uint32_t mb_l, uint32_t mb_a, int dpb)
{
	for (size_t i = 0; i < sizeof H264_LEVELS / sizeof H264_LEVELS[0]; i++) {
		const H264Level *L = &H264_LEVELS[i];
		uint64_t mb = (uint64_t) mb_l * mb_a;

		if (L->cs3f)
			continue; /* High does not carry constraint_set3 */
		if (bitrate > (int64_t) L->max_br * 1500)
			continue;
		if (mb > (uint64_t) L->max_fs)
			continue;
		if ((uint64_t) mb_l * mb_l > 8u * (uint64_t) L->max_fs)
			continue;
		if ((uint64_t) mb_a * mb_a > 8u * (uint64_t) L->max_fs)
			continue;
		if (mb) {
			int dpb_max = (int) ((uint64_t) L->max_dpb_mbs / mb);
			if (dpb_max > 16)
				dpb_max = 16;
			if (dpb > dpb_max)
				continue;
			if (fps > (int) ((uint64_t) L->max_mbps / mb))
				continue;
		}
		return L->level_idc;
	}
	return 62; /* «Stream will not conform to any level: using level 6.2» */
}

typedef struct {
	int level_idc;
	uint32_t max_luma_ps;
	int max_br_main; /* kbit/s, Main tier */
} HEVCLevel;

static const HEVCLevel HEVC_LEVELS[] = {
	{ 30, 36864, 128 },       { 60, 122880, 1500 },     { 63, 245760, 3000 },
	{ 90, 552960, 6000 },     { 93, 983040, 10000 },    { 120, 2228224, 12000 },
	{ 123, 2228224, 20000 },  { 150, 8912896, 25000 },  { 153, 8912896, 40000 },
	{ 156, 8912896, 60000 },  { 180, 35651584, 60000 }, { 183, 35651584, 120000 },
	{ 186, 35651584, 240000 },
};

/* `ff_h265_guess_level` for Main/Main10, Main tier, 1 slice, no tiles,
 * `max_dec_pic_buffering` = 1: CpbNalFactor 1100, hbr_factor 1,
 * maxDpbPicBuf 6.  ⚠ The bitrate here is the working POINT (`avctx->bit_rate`),
 *   not the wire: that is how `hw_base_encode_h265.c` does it, and H.264 does the
 *   opposite (`ctx->va_bit_rate`, i.e. the wire).  Two asymmetries to be copied,
 *   not corrected. */
static int hevc_level(int64_t bitrate, uint32_t l, uint32_t a, int dpb)
{
	uint64_t pic = (uint64_t) l * a;

	for (size_t i = 0; i < sizeof HEVC_LEVELS / sizeof HEVC_LEVELS[0]; i++) {
		const HEVCLevel *L = &HEVC_LEVELS[i];
		int dpb_max;

		if (pic > L->max_luma_ps)
			continue;
		if ((uint64_t) l * l > 8u * (uint64_t) L->max_luma_ps)
			continue;
		if ((uint64_t) a * a > 8u * (uint64_t) L->max_luma_ps)
			continue;
		if (bitrate > (int64_t) 1100 * L->max_br_main)
			continue;
		if (pic <= (L->max_luma_ps >> 2))
			dpb_max = 16;
		else if (pic <= (L->max_luma_ps >> 1))
			dpb_max = 12;
		else if (pic <= (3u * L->max_luma_ps >> 2))
			dpb_max = 8;
		else
			dpb_max = 6;
		if (dpb > dpb_max)
			continue;
		return L->level_idc;
	}
	return 255; /* «using level 8.5» — and ffmpeg raises the tier: see `hevc_ptl()` */
}

/* ═══════════════════════════════════════════════════════════════════════════
 * THE STATE
 * ═══════════════════════════════════════════════════════════════════════════ */

struct VaDirect {
	VADisplay display;
	char vendor[128];           /* for the SEI: who encoded */
	VaDirectRequest r;
	VaDirectDeclaration d;

	VAConfigID config;
	VAContextID context;
	VASurfaceID *ingress;         /* the input pool */
	unsigned how_many_ingress, next_ingress;
	VASurfaceID rebuilt[REBUILT];
	VABufferID coded;
	size_t coded_byte;

	/* the bytes of the last frame, in Annex-B, ours */
	uint8_t *output;
	size_t output_capabilities, output_byte;

	/* the sequence state — what ffmpeg kept in `FFHWBaseEncodePicture` */
	uint64_t order;               /* how many frames encoded since this open */
	uint64_t last_idr;           /* the order of the last IDR */
	uint32_t in_gop;              /* frames since the last IDR, inclusive */
	bool reference_valid;       /* there is a previous frame to predict from */
	unsigned rebuilt_current; /* which of the REBUILT receives this frame */
	unsigned rebuilt_reference;
	/* H.264 */
	uint32_t frame_num, frame_num_reference;
	uint32_t idr_pic_id;
	int32_t poc, poc_reference;  /* HEVC: display − last IDR · H.264: twice that (poc type 2) */
	bool sei_identifier_written;

	/* the fixed sequence/picture parameters, filled at open */
	union {
		VAEncSequenceParameterBufferH264 h264;
		VAEncSequenceParameterBufferHEVC hevc;
	} seq;
	int fixed_qp;                  /* CQP: the requested QP · QVBR: 26 (H.264) / 30 (HEVC), like ffmpeg */
	uint32_t mb_l, mb_a;           /* H.264: the macroblocks */
	uint32_t ctb_l, ctb_a;         /* HEVC: the CTBs */
	/* HEVC: what ends up in the SPS/PPS, decided by the driver's attributes */
	struct {
		unsigned log2_min_cb_m3, log2_diff_cb, log2_min_tb_m2, log2_diff_tb;
		unsigned depth_inter, depth_intra;
		bool amp, sao, tmvp, pcm, transform_skip, cu_qp_delta;
		unsigned min_cb, ctu;
	} hevc;

};

/* ═══════════════════════════════════════════════════════════════════════════
 * 3. THE HEADERS — H.264
 *
 * Each function writes the RBSP with `BitWriter` and then the NAL in Annex-B with
 * `nal_annexb()`.  ⚠ The capacities are generous on purpose: an SPS is ~30 bytes,
 *   a slice header ~10, the SEI ~120.
 * ═══════════════════════════════════════════════════════════════════════════ */

#define MAX_HEADER 512

/* The three colour numbers, declared and not inherited (as
 * `convert_on_gpu()` in `encoder.c` imposes the matrix): BT.709 on all three entries, limited
 * range.  They are the values of `AVCOL_PRI_BT709`/`AVCOL_TRC_BT709`/
 * `AVCOL_SPC_BT709` = 1, and the full-range flag at 0. */
#define COLOR_PRIMARIES 1
#define COLOR_TRANSFER 1
#define COLOR_MATRIX 1

static bool h264_cqp(const VaDirect *v)
{
	return v->d.va_mode == VA_RC_CQP;
}

/* av_log2: the highest bit set. */
static int log2_int(uint64_t x)
{
	int n = -1;
	while (x) {
		x >>= 1;
		n++;
	}
	return n < 0 ? 0 : n;
}

static unsigned trim_4bit(int x)
{
	if (x < 0)
		return 0;
	if (x > 15)
		return 15;
	return (unsigned) x;
}

static void h264_hrd_parameters(BitWriter *s, const VaDirect *v)
{
	uint64_t bitrate = (uint64_t) v->r.bandwidth_wire;
	uint64_t cpb = (uint64_t) v->r.reservoir_bit;
	unsigned bit_rate_scale = trim_4bit(log2_int(bitrate) - 15 - 6);
	unsigned cpb_size_scale = trim_4bit(log2_int(cpb) - 15 - 4);

	bw_ue(s, 0);                                        /* cpb_cnt_minus1 */
	bw_u(s, 4, bit_rate_scale);
	bw_u(s, 4, cpb_size_scale);
	bw_ue(s, (uint32_t) ((bitrate >> (bit_rate_scale + 6)) - 1)); /* bit_rate_value_minus1[0] */
	bw_ue(s, (uint32_t) ((cpb >> (cpb_size_scale + 4)) - 1));     /* cpb_size_value_minus1[0] */
	bw_flag(s, false);                                  /* cbr_flag[0]: never, even in CBR */
	bw_u(s, 5, 23);                                     /* initial_cpb_removal_delay_length_minus1 */
	bw_u(s, 5, 23);                                     /* cpb_removal_delay_length_minus1 */
	bw_u(s, 5, 7);                                      /* dpb_output_delay_length_minus1 */
	bw_u(s, 5, 0);                                      /* time_offset_length */
}

static size_t h264_sps(const VaDirect *v, uint8_t *report, size_t capabilities)
{
	uint8_t rbsp[MAX_HEADER];
	const uint8_t head = 0x67; /* nal_ref_idc 3, nal_unit_type 7 */
	BitWriter s;
	uint32_t crop_right = (16 * v->mb_l - v->r.width) / 2;
	uint32_t crop_bottom = (16 * v->mb_a - v->r.height) / 2;

	bw_open(&s, rbsp, sizeof rbsp);
	bw_u(&s, 8, 100);                 /* profile_idc: High, which is what `avc1.64..` says */
	bw_flag(&s, false);               /* constraint_set0_flag */
	bw_flag(&s, false);               /* constraint_set1_flag */
	bw_flag(&s, false);               /* constraint_set2_flag */
	bw_flag(&s, false);               /* constraint_set3_flag: only with gop_size == 1 */
	bw_flag(&s, true);                /* constraint_set4_flag: High ⇒ 1 */
	bw_flag(&s, true);                /* constraint_set5_flag: no B ⇒ 1 */
	bw_u(&s, 2, 0);                   /* reserved_zero_2bits */
	bw_u(&s, 8, (uint32_t) v->d.level_idc);
	bw_ue(&s, 0);                     /* seq_parameter_set_id */
	bw_ue(&s, 1);                     /* chroma_format_idc: 4:2:0 */
	bw_ue(&s, (uint32_t) (v->r.depth - 8)); /* bit_depth_luma_minus8 */
	bw_ue(&s, (uint32_t) (v->r.depth - 8)); /* bit_depth_chroma_minus8 */
	bw_flag(&s, false);               /* qpprime_y_zero_transform_bypass_flag */
	bw_flag(&s, false);               /* seq_scaling_matrix_present_flag */
	bw_ue(&s, 4);                     /* log2_max_frame_num_minus4: frame_num on 8 bits */
	bw_ue(&s, 2);                     /* pic_order_cnt_type: 2, because no B */
	bw_ue(&s, 1);                     /* max_num_ref_frames: one, the previous */
	bw_flag(&s, false);               /* gaps_in_frame_num_value_allowed_flag */
	bw_ue(&s, v->mb_l - 1);           /* pic_width_in_mbs_minus1 */
	bw_ue(&s, v->mb_a - 1);           /* pic_height_in_map_units_minus1 */
	bw_flag(&s, true);                /* frame_mbs_only_flag */
	bw_flag(&s, true);                /* direct_8x8_inference_flag */
	if (crop_right || crop_bottom) {    /* frame_cropping_flag: the canvas is not a multiple of 16 */
		bw_flag(&s, true);
		bw_ue(&s, 0);
		bw_ue(&s, crop_right);
		bw_ue(&s, 0);
		bw_ue(&s, crop_bottom);
	} else {
		bw_flag(&s, false);
	}
	bw_flag(&s, true);                /* vui_parameters_present_flag */
	/* VUI (E.1.1) */
	bw_flag(&s, false);               /* aspect_ratio_info_present_flag: the capture has no SAR */
	bw_flag(&s, false);               /* overscan_info_present_flag */
	bw_flag(&s, true);                /* video_signal_type_present_flag */
	bw_u(&s, 3, 5);                   /* video_format: unspecified (table E-2) */
	bw_flag(&s, false);               /* video_full_range_flag: limited — Firefox ignores full [M] */
	bw_flag(&s, true);                /* colour_description_present_flag */
	bw_u(&s, 8, COLOR_PRIMARIES);
	bw_u(&s, 8, COLOR_TRANSFER);
	bw_u(&s, 8, COLOR_MATRIX);
	bw_flag(&s, false);               /* chroma_loc_info_present_flag */
	bw_flag(&s, true);                /* timing_info_present_flag */
	bw_u(&s, 32, 1);                  /* num_units_in_tick = framerate.den */
	bw_u(&s, 32, 2u * v->r.fotogrammi_al_secondo); /* time_scale = 2·num */
	bw_flag(&s, true);                /* fixed_frame_rate_flag */
	if (h264_cqp(v)) {
		bw_flag(&s, false);           /* nal_hrd_parameters_present_flag */
		bw_flag(&s, false);           /* vcl_hrd_parameters_present_flag */
		/* low_delay_hrd_flag: absent without HRD (inferred 1 − fixed_frame_rate) */
	} else {
		bw_flag(&s, true);            /* nal_hrd_parameters_present_flag: with the cap on, ffmpeg writes them */
		h264_hrd_parameters(&s, v);
		bw_flag(&s, false);           /* vcl_hrd_parameters_present_flag */
		bw_flag(&s, false);           /* low_delay_hrd_flag */
	}
	bw_flag(&s, false);               /* pic_struct_present_flag */
	bw_flag(&s, true);                /* bitstream_restriction_flag */
	bw_flag(&s, true);                /* motion_vectors_over_pic_boundaries_flag */
	bw_ue(&s, 0);                     /* max_bytes_per_pic_denom */
	bw_ue(&s, 0);                     /* max_bits_per_mb_denom */
	bw_ue(&s, 15);                    /* log2_max_mv_length_horizontal */
	bw_ue(&s, 15);                    /* log2_max_mv_length_vertical */
	bw_ue(&s, 0);                     /* max_num_reorder_frames: no B */
	bw_ue(&s, 1);                     /* max_dec_frame_buffering: the single reference */
	bw_close_rbsp(&s);
	if (s.overflowed)
		return 0;
	return nal_annexb(report, capabilities, &head, 1, rbsp, bw_byte(&s));
}

static size_t h264_pps(const VaDirect *v, uint8_t *report, size_t capabilities)
{
	uint8_t rbsp[MAX_HEADER];
	const uint8_t head = 0x68; /* nal_ref_idc 3, nal_unit_type 8 */
	BitWriter s;

	bw_open(&s, rbsp, sizeof rbsp);
	bw_ue(&s, 0);                     /* pic_parameter_set_id */
	bw_ue(&s, 0);                     /* seq_parameter_set_id */
	bw_flag(&s, true);                /* entropy_coding_mode_flag: CABAC (High) */
	bw_flag(&s, false);               /* bottom_field_pic_order_in_frame_present_flag */
	bw_ue(&s, 0);                     /* num_slice_groups_minus1 */
	bw_ue(&s, 0);                     /* num_ref_idx_l0_default_active_minus1 */
	bw_ue(&s, 0);                     /* num_ref_idx_l1_default_active_minus1 */
	bw_flag(&s, false);               /* weighted_pred_flag */
	bw_u(&s, 2, 0);                   /* weighted_bipred_idc */
	bw_se(&s, v->fixed_qp - 26);      /* pic_init_qp_minus26 */
	bw_se(&s, 0);                     /* pic_init_qs_minus26 */
	bw_se(&s, 0);                     /* chroma_qp_index_offset */
	bw_flag(&s, false);               /* deblocking_filter_control_present_flag */
	bw_flag(&s, false);               /* constrained_intra_pred_flag */
	bw_flag(&s, false);               /* redundant_pic_cnt_present_flag */
	/* more_rbsp_data(): on High ffmpeg also writes these three */
	bw_flag(&s, true);                /* transform_8x8_mode_flag */
	bw_flag(&s, false);               /* pic_scaling_matrix_present_flag */
	bw_se(&s, 0);                     /* second_chroma_qp_index_offset */
	bw_close_rbsp(&s);
	if (s.overflowed)
		return 0;
	return nal_annexb(report, capabilities, &head, 1, rbsp, bw_byte(&s));
}

/*
 * The slice header (7.3.3) for our single slice: IDR or P.
 * ⚠ `mmco 1` with `difference_of_pic_nums_minus1 = 0` on EVERY P: it is ffmpeg
 *   discarding the previous reference as soon as it has a new one («Discard
 *   everything which is in the DPB of the previous frame but not in the DPB
 *   of this one»), and with a single reference the difference is always 0 —
 *   `[M]` it is in every P of today's trace.
 */
static size_t h264_slice(const VaDirect *v, bool idr, uint8_t *report, size_t capabilities)
{
	uint8_t rbsp[MAX_HEADER];
	const uint8_t head = idr ? 0x65 : 0x41; /* IDR: ref_idc 3, type 5 · P: ref_idc 1, type 1 */
	BitWriter s;

	bw_open(&s, rbsp, sizeof rbsp);
	bw_ue(&s, 0);                     /* first_mb_in_slice */
	bw_ue(&s, idr ? 7 : 5);           /* slice_type: I (7) / P (5), «all slices like this» */
	bw_ue(&s, 0);                     /* pic_parameter_set_id */
	bw_u(&s, 8, v->frame_num & 0xFFu); /* frame_num, on log2_max_frame_num = 8 bits */
	if (idr)
		bw_ue(&s, v->idr_pic_id);     /* idr_pic_id */
	/* pic_order_cnt_type 2: no pic_order_cnt_lsb */
	if (!idr) {
		bw_flag(&s, false);           /* num_ref_idx_active_override_flag */
		bw_flag(&s, false);           /* ref_pic_list_modification_flag_l0 */
	}
	/* dec_ref_pic_marking(): nal_ref_idc != 0 in both cases */
	if (idr) {
		bw_flag(&s, false);           /* no_output_of_prior_pics_flag */
		bw_flag(&s, false);           /* long_term_reference_flag */
	} else {
		bw_flag(&s, true);            /* adaptive_ref_pic_marking_mode_flag */
		bw_ue(&s, 1);                 /* memory_management_control_operation 1 */
		bw_ue(&s, v->frame_num - v->frame_num_reference - 1); /* difference_of_pic_nums_minus1 */
		bw_ue(&s, 0);                 /* memory_management_control_operation 0: end */
		bw_ue(&s, 0);                 /* cabac_init_idc (CABAC, non-I slice) */
	}
	bw_se(&s, 0);                     /* slice_qp_delta: the QP is already in pic_init_qp */
	bw_align_with_uni(&s);           /* cabac_alignment_one_bit */
	if (s.overflowed)
		return 0;
	return nal_annexb(report, capabilities, &head, 1, rbsp, bw_byte(&s));
}

/* ⭐ REMOTIX's UUID for the user_data_unregistered SEI (D.1.7): 16 bytes
 *    drawn once and fixed.  Different from ffmpeg's on purpose: a
 *    reader looking for «who encoded» finds the truth. */
static const uint8_t UUID_REMOTIX[16] = { 0x52, 0x45, 0x4d, 0x4f, 0x54, 0x49, 0x58, 0x2d,
	                                      0x76, 0x61, 0x64, 0x69, 0x72, 0x65, 0x74, 0x74 };

/* The SEI of the first frame: who we are, and with the cap on also the
 * buffering_period (D.1.1) — the same two that ffmpeg puts in a single NAL. */
static size_t h264_sei(const VaDirect *v, bool idr, uint8_t *report, size_t capabilities)
{
	uint8_t rbsp[MAX_HEADER];
	const uint8_t head = 0x06; /* nal_ref_idc 0, nal_unit_type 6 */
	BitWriter s;
	char text[224];
	size_t length;
	bool identifier = !v->sei_identifier_written;
	bool times = !h264_cqp(v);

	if (!identifier && !times)
		return 0;
	bw_open(&s, rbsp, sizeof rbsp);
	if (identifier) {
		snprintf(text, sizeof text, "REMOTIX vadiretta / VAAPI %d.%d / %s",
		         VA_MAJOR_VERSION, VA_MINOR_VERSION, v->vendor);
		length = strlen(text) + 1; /* with the NUL, like ffmpeg */
		bw_u(&s, 8, 5);                                 /* last_payload_type_byte: user_data_unregistered */
		bw_u(&s, 8, (uint32_t) (16 + length));       /* last_payload_size_byte */
		for (int i = 0; i < 16; i++)
			bw_u(&s, 8, UUID_REMOTIX[i]);
		for (size_t i = 0; i < length; i++)
			bw_u(&s, 8, (uint8_t) text[i]);
	}
	if (times) {
		/* buffering_period on the IDR (7 bytes: ue sps_id + 2 x u(24)) and
		 * pic_timing on every frame (u(24) + u(8) = 4 bytes), with the arithmetic of
		 * `vaapi_encode_h264_init_picture_params`. */
		uint64_t reservoir = (uint64_t) v->r.reservoir_bit;
		uint64_t full = reservoir * 3 / 4; /* initial_buffer_fullness */
		uint32_t initial_removal = (uint32_t) (90000u * full / (reservoir ? reservoir : 1));
		uint32_t cpb_delay = (uint32_t) (v->order - v->last_idr);

		if (idr) {
			bw_u(&s, 8, 0);                             /* payloadType 0: buffering_period */
			bw_u(&s, 8, 7);                             /* payloadSize: ue(0)=1 bit + 48 bits + tail = 7 bytes */
			bw_ue(&s, 0);                               /* seq_parameter_set_id */
			bw_u(&s, 24, initial_removal);           /* initial_cpb_removal_delay[0] */
			bw_u(&s, 24, 0);                            /* initial_cpb_removal_delay_offset[0] */
			bw_flag(&s, true);                          /* bit_equal_to_one */
			while (!bw_aligned(&s))
				bw_flag(&s, false);
		}
		bw_u(&s, 8, 1);                                 /* payloadType 1: pic_timing */
		bw_u(&s, 8, 4);                                 /* payloadSize: 24 + 8 bit */
		bw_u(&s, 24, 2u * cpb_delay);                   /* cpb_removal_delay */
		bw_u(&s, 8, 0);                                 /* dpb_output_delay: 2·dpb_delay, with max_b_depth 0 */
	}
	bw_close_rbsp(&s);
	if (s.overflowed)
		return 0;
	return nal_annexb(report, capabilities, &head, 1, rbsp, bw_byte(&s));
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 3-bis. THE HEADERS — HEVC
 * ═══════════════════════════════════════════════════════════════════════════ */

/* profile_tier_level(1, 0) of 7.3.3: 96 bits.  Main: compat[1] and [2]; Main 10:
 * compat[2].  ⚠ With compat[2] set the constraint branch is the «profile
 *   2» one: 7 reserved bits, one_picture_only, 35 reserved — the order that
 *   `cbs_h265` follows and that today's trace shows. */
static void hevc_ptl(BitWriter *s, const VaDirect *v)
{
	unsigned profile = v->r.depth == 10 ? 2 : 1;
	bool tier_alto = v->d.level_idc == 255; /* «The tier flag must be set in level 8.5» */

	bw_u(s, 2, 0);                    /* general_profile_space */
	bw_flag(s, tier_alto);            /* general_tier_flag */
	bw_u(s, 5, profile);              /* general_profile_idc */
	for (unsigned j = 0; j < 32; j++) /* general_profile_compatibility_flag[j] */
		bw_flag(s, j == profile || (profile == 1 && j == 2));
	bw_flag(s, true);                 /* general_progressive_source_flag */
	bw_flag(s, false);                /* general_interlaced_source_flag */
	bw_flag(s, true);                 /* general_non_packed_constraint_flag */
	bw_flag(s, true);                 /* general_frame_only_constraint_flag */
	bw_u(s, 7, 0);                    /* general_reserved_zero_7bits */
	bw_flag(s, false);                /* general_one_picture_only_constraint_flag */
	bw_u(s, 24, 0);                   /* general_reserved_zero_35bits */
	bw_u(s, 11, 0);
	bw_flag(s, false);                /* general_inbld_flag */
	bw_u(s, 8, (uint32_t) v->d.level_idc); /* general_level_idc */
}

static size_t hevc_vps(const VaDirect *v, uint8_t *report, size_t capabilities)
{
	uint8_t rbsp[MAX_HEADER];
	const uint8_t head[2] = { 0x40, 0x01 }; /* type 32, layer 0, temporal_id_plus1 1 */
	BitWriter s;

	bw_open(&s, rbsp, sizeof rbsp);
	bw_u(&s, 4, 0);                   /* vps_video_parameter_set_id */
	bw_flag(&s, true);                /* vps_base_layer_internal_flag */
	bw_flag(&s, true);                /* vps_base_layer_available_flag */
	bw_u(&s, 6, 0);                   /* vps_max_layers_minus1 */
	bw_u(&s, 3, 0);                   /* vps_max_sub_layers_minus1 */
	bw_flag(&s, true);                /* vps_temporal_id_nesting_flag */
	bw_u(&s, 16, 0xFFFF);             /* vps_reserved_0xffff_16bits */
	hevc_ptl(&s, v);
	bw_flag(&s, false);               /* vps_sub_layer_ordering_info_present_flag */
	bw_ue(&s, 1);                     /* vps_max_dec_pic_buffering_minus1[0]: max_b_depth + 1 */
	bw_ue(&s, 0);                     /* vps_max_num_reorder_pics[0] */
	bw_ue(&s, 0);                     /* vps_max_latency_increase_plus1[0] */
	bw_u(&s, 6, 0);                   /* vps_max_layer_id */
	bw_ue(&s, 0);                     /* vps_num_layer_sets_minus1 */
	bw_flag(&s, true);                /* vps_timing_info_present_flag */
	bw_u(&s, 32, 1);                  /* vps_num_units_in_tick */
	bw_u(&s, 32, v->r.fotogrammi_al_secondo); /* vps_time_scale: NOT doubled here */
	bw_flag(&s, true);                /* vps_poc_proportional_to_timing_flag */
	bw_ue(&s, 0);                     /* vps_num_ticks_poc_diff_one_minus1 */
	bw_ue(&s, 0);                     /* vps_num_hrd_parameters */
	bw_flag(&s, false);               /* vps_extension_flag */
	bw_close_rbsp(&s);
	if (s.overflowed)
		return 0;
	return nal_annexb(report, capabilities, head, 2, rbsp, bw_byte(&s));
}

static size_t hevc_sps(const VaDirect *v, uint8_t *report, size_t capabilities)
{
	uint8_t rbsp[MAX_HEADER];
	const uint8_t head[2] = { 0x42, 0x01 }; /* type 33 */
	BitWriter s;
	uint32_t crop_right = (v->d.surface_width - v->r.width) >> 1;
	uint32_t crop_bottom = (v->d.surface_height - v->r.height) >> 1;

	bw_open(&s, rbsp, sizeof rbsp);
	bw_u(&s, 4, 0);                   /* sps_video_parameter_set_id */
	bw_u(&s, 3, 0);                   /* sps_max_sub_layers_minus1 */
	bw_flag(&s, true);                /* sps_temporal_id_nesting_flag */
	hevc_ptl(&s, v);
	bw_ue(&s, 0);                     /* sps_seq_parameter_set_id */
	bw_ue(&s, 1);                     /* chroma_format_idc: 4:2:0 */
	bw_ue(&s, v->d.surface_width); /* pic_width_in_luma_samples: the surface, aligned */
	bw_ue(&s, v->d.surface_height);
	if (crop_right || crop_bottom) {    /* conformance_window_flag: the canvas cropped from the surface */
		bw_flag(&s, true);
		bw_ue(&s, 0);
		bw_ue(&s, crop_right);         /* in chroma units: >> log2_chroma_w */
		bw_ue(&s, 0);
		bw_ue(&s, crop_bottom);
	} else {
		bw_flag(&s, false);
	}
	bw_ue(&s, (uint32_t) (v->r.depth - 8)); /* bit_depth_luma_minus8 */
	bw_ue(&s, (uint32_t) (v->r.depth - 8)); /* bit_depth_chroma_minus8 */
	bw_ue(&s, 8);                     /* log2_max_pic_order_cnt_lsb_minus4: POC lsb on 12 bits */
	bw_flag(&s, false);               /* sps_sub_layer_ordering_info_present_flag */
	bw_ue(&s, 1);                     /* sps_max_dec_pic_buffering_minus1[0] */
	bw_ue(&s, 0);                     /* sps_max_num_reorder_pics[0] */
	bw_ue(&s, 0);                     /* sps_max_latency_increase_plus1[0] */
	bw_ue(&s, v->hevc.log2_min_cb_m3);   /* log2_min_luma_coding_block_size_minus3 */
	bw_ue(&s, v->hevc.log2_diff_cb);     /* log2_diff_max_min_luma_coding_block_size */
	bw_ue(&s, v->hevc.log2_min_tb_m2);   /* log2_min_luma_transform_block_size_minus2 */
	bw_ue(&s, v->hevc.log2_diff_tb);     /* log2_diff_max_min_luma_transform_block_size */
	bw_ue(&s, v->hevc.depth_inter);      /* max_transform_hierarchy_depth_inter */
	bw_ue(&s, v->hevc.depth_intra);      /* max_transform_hierarchy_depth_intra */
	bw_flag(&s, false);               /* scaling_list_enabled_flag */
	bw_flag(&s, v->hevc.amp);         /* amp_enabled_flag */
	bw_flag(&s, v->hevc.sao);         /* sample_adaptive_offset_enabled_flag */
	bw_flag(&s, false);               /* pcm_enabled_flag: ffmpeg keeps it off even if the driver supports it */
	bw_ue(&s, 0);                     /* num_short_term_ref_pic_sets: the sets live in the slices */
	bw_flag(&s, false);               /* long_term_ref_pics_present_flag */
	bw_flag(&s, v->hevc.tmvp);        /* sps_temporal_mvp_enabled_flag */
	bw_flag(&s, false);               /* strong_intra_smoothing_enabled_flag */
	bw_flag(&s, true);                /* vui_parameters_present_flag */
	/* VUI (E.2.1) */
	bw_flag(&s, false);               /* aspect_ratio_info_present_flag */
	bw_flag(&s, false);               /* overscan_info_present_flag */
	bw_flag(&s, true);                /* video_signal_type_present_flag */
	bw_u(&s, 3, 5);                   /* video_format */
	bw_flag(&s, false);               /* video_full_range_flag */
	bw_flag(&s, true);                /* colour_description_present_flag */
	bw_u(&s, 8, COLOR_PRIMARIES);
	bw_u(&s, 8, COLOR_TRANSFER);
	bw_u(&s, 8, COLOR_MATRIX);
	bw_flag(&s, false);               /* chroma_loc_info_present_flag */
	bw_flag(&s, false);               /* neutral_chroma_indication_flag */
	bw_flag(&s, false);               /* field_seq_flag */
	bw_flag(&s, false);               /* frame_field_info_present_flag */
	bw_flag(&s, false);               /* default_display_window_flag */
	bw_flag(&s, true);                /* vui_timing_info_present_flag */
	bw_u(&s, 32, 1);                  /* vui_num_units_in_tick */
	bw_u(&s, 32, v->r.fotogrammi_al_secondo); /* vui_time_scale */
	bw_flag(&s, true);                /* vui_poc_proportional_to_timing_flag */
	bw_ue(&s, 0);                     /* vui_num_ticks_poc_diff_one_minus1 */
	bw_flag(&s, false);               /* vui_hrd_parameters_present_flag: never, not even with the cap */
	bw_flag(&s, true);                /* bitstream_restriction_flag */
	bw_flag(&s, false);               /* tiles_fixed_structure_flag */
	bw_flag(&s, true);                /* motion_vectors_over_pic_boundaries_flag */
	bw_flag(&s, true);                /* restricted_ref_pic_lists_flag */
	bw_ue(&s, 0);                     /* min_spatial_segmentation_idc */
	bw_ue(&s, 0);                     /* max_bytes_per_pic_denom */
	bw_ue(&s, 0);                     /* max_bits_per_min_cu_denom */
	bw_ue(&s, 15);                    /* log2_max_mv_length_horizontal */
	bw_ue(&s, 15);                    /* log2_max_mv_length_vertical */
	bw_flag(&s, false);               /* sps_extension_present_flag */
	bw_close_rbsp(&s);
	if (s.overflowed)
		return 0;
	return nal_annexb(report, capabilities, head, 2, rbsp, bw_byte(&s));
}

static size_t hevc_pps(const VaDirect *v, uint8_t *report, size_t capabilities)
{
	uint8_t rbsp[MAX_HEADER];
	const uint8_t head[2] = { 0x44, 0x01 }; /* type 34 */
	BitWriter s;

	bw_open(&s, rbsp, sizeof rbsp);
	bw_ue(&s, 0);                     /* pps_pic_parameter_set_id */
	bw_ue(&s, 0);                     /* pps_seq_parameter_set_id */
	bw_flag(&s, false);               /* dependent_slice_segments_enabled_flag */
	bw_flag(&s, false);               /* output_flag_present_flag */
	bw_u(&s, 3, 0);                   /* num_extra_slice_header_bits */
	bw_flag(&s, false);               /* sign_data_hiding_enabled_flag */
	bw_flag(&s, false);               /* cabac_init_present_flag */
	bw_ue(&s, 0);                     /* num_ref_idx_l0_default_active_minus1 */
	bw_ue(&s, 0);                     /* num_ref_idx_l1_default_active_minus1 */
	bw_se(&s, v->fixed_qp - 26);      /* init_qp_minus26 */
	bw_flag(&s, false);               /* constrained_intra_pred_flag */
	bw_flag(&s, v->hevc.transform_skip); /* transform_skip_enabled_flag */
	bw_flag(&s, v->hevc.cu_qp_delta); /* cu_qp_delta_enabled_flag: only with the cap (not CQP) */
	if (v->hevc.cu_qp_delta)
		bw_ue(&s, v->hevc.log2_diff_cb); /* diff_cu_qp_delta_depth: «its max value» */
	bw_se(&s, 0);                     /* pps_cb_qp_offset */
	bw_se(&s, 0);                     /* pps_cr_qp_offset */
	bw_flag(&s, false);               /* pps_slice_chroma_qp_offsets_present_flag */
	bw_flag(&s, false);               /* weighted_pred_flag */
	bw_flag(&s, false);               /* weighted_bipred_flag */
	bw_flag(&s, false);               /* transquant_bypass_enabled_flag */
	bw_flag(&s, false);               /* tiles_enabled_flag */
	bw_flag(&s, false);               /* entropy_coding_sync_enabled_flag */
	bw_flag(&s, true);                /* pps_loop_filter_across_slices_enabled_flag */
	bw_flag(&s, false);               /* deblocking_filter_control_present_flag */
	bw_flag(&s, false);               /* pps_scaling_list_data_present_flag */
	bw_flag(&s, false);               /* lists_modification_present_flag */
	bw_ue(&s, 0);                     /* log2_parallel_merge_level_minus2 */
	bw_flag(&s, false);               /* slice_segment_header_extension_present_flag */
	bw_flag(&s, false);               /* pps_extension_present_flag */
	bw_close_rbsp(&s);
	if (s.overflowed)
		return 0;
	return nal_annexb(report, capabilities, head, 2, rbsp, bw_byte(&s));
}

/*
 * slice_segment_header() (7.3.6.1): IDR_W_RADL with an I slice, or TRAIL_R
 * with a P slice — or a «GPB» B when the driver cannot do P (`p_come_b`, Intel iHD:
 * `[M]` today's trace has `slice_type 0` with `mvd_l1_zero_flag` and
 * `collocated_from_l0_flag`, and L1 = L0).
 */
static size_t hevc_slice(const VaDirect *v, bool idr, uint8_t *report, size_t capabilities)
{
	uint8_t rbsp[MAX_HEADER];
	const uint8_t head[2] = { idr ? 0x26 : 0x02, 0x01 }; /* 19 (IDR_W_RADL) or 1 (TRAIL_R) */
	BitWriter s;
	unsigned kind = idr ? 2 : (v->d.p_come_b ? 0 : 1); /* I / B / P */

	bw_open(&s, rbsp, sizeof rbsp);
	bw_flag(&s, true);                /* first_slice_segment_in_pic_flag */
	if (idr)
		bw_flag(&s, false);           /* no_output_of_prior_pics_flag (IRAP only) */
	bw_ue(&s, 0);                     /* slice_pic_parameter_set_id */
	bw_ue(&s, kind);                  /* slice_type */
	if (!idr) {
		bw_u(&s, 12, (uint32_t) v->poc & 0xFFFu); /* slice_pic_order_cnt_lsb */
		bw_flag(&s, false);           /* short_term_ref_pic_set_sps_flag: the set is here */
		/* st_ref_pic_set(0): a single negative, the previous one, used */
		bw_ue(&s, 1);                 /* num_negative_pics */
		bw_ue(&s, 0);                 /* num_positive_pics */
		bw_ue(&s, (uint32_t) (v->poc - v->poc_reference - 1)); /* delta_poc_s0_minus1[0] */
		bw_flag(&s, true);            /* used_by_curr_pic_s0_flag[0] */
		if (v->hevc.tmvp)
			bw_flag(&s, true);        /* slice_temporal_mvp_enabled_flag */
	}
	if (v->hevc.sao) {
		bw_flag(&s, true);            /* slice_sao_luma_flag */
		bw_flag(&s, true);            /* slice_sao_chroma_flag */
	}
	if (!idr) {
		bw_flag(&s, false);           /* num_ref_idx_active_override_flag */
		if (kind == 0)
			bw_flag(&s, false);       /* mvd_l1_zero_flag */
		/* cabac_init_present_flag is 0: no cabac_init_flag */
		if (v->hevc.tmvp) {
			if (kind == 0)
				bw_flag(&s, true);    /* collocated_from_l0_flag */
			/* collocated_ref_idx: absent, num_ref_idx_l0_active_minus1 = 0 */
		}
		bw_ue(&s, 0);                 /* five_minus_max_num_merge_cand */
	}
	bw_se(&s, 0);                     /* slice_qp_delta */
	/* pps_loop_filter_across_slices_enabled_flag && (sao || deblocking on) ⇒ present */
	bw_flag(&s, false);               /* slice_loop_filter_across_slices_enabled_flag */
	bw_close_rbsp(&s);               /* byte_alignment() */
	if (s.overflowed)
		return 0;
	return nal_annexb(report, capabilities, head, 2, rbsp, bw_byte(&s));
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 1-bis. THE OPENING: configuration, context, surfaces, buffers
 * ═══════════════════════════════════════════════════════════════════════════ */

static bool attribute(VADisplay d, VAProfile p, VAEntrypoint e, VAConfigAttribType kind,
                      uint32_t *value)
{
	VAConfigAttrib a = { .type = kind };

	if (vaGetConfigAttributes(d, p, e, &a, 1) != VA_STATUS_SUCCESS)
		return false;
	if (a.value == VA_ATTRIB_NOT_SUPPORTED)
		return false;
	*value = a.value;
	return true;
}

static uint32_t align(uint32_t x, uint32_t a)
{
	return (x + a - 1) / a * a;
}

/* What the driver can do in HEVC, and the sizes that follow from it: it is
 * ffmpeg's `vaapi_encode_h265_get_encoder_caps` + the «update sps setting
 * according to queried result» block. */
static void hevc_capabilities(VaDirect *v)
{
	uint32_t features = 0, blocks = 0;
	bool f_ok = attribute(v->display, v->r.profile, v->r.entrypoint,
	                      VAConfigAttribEncHEVCFeatures, &features);
	bool b_ok = attribute(v->display, v->r.profile, v->r.entrypoint,
	                      VAConfigAttribEncHEVCBlockSizes, &blocks);

	/* ffmpeg's defaults («These values come from the capabilities of the
	 * first encoder implementation in the i965 driver on Intel Skylake»). */
	v->hevc.log2_min_cb_m3 = 0;
	v->hevc.log2_diff_cb = 2;
	v->hevc.log2_min_tb_m2 = 0;
	v->hevc.log2_diff_tb = 3;
	v->hevc.depth_inter = 3;
	v->hevc.depth_intra = 3;
	v->hevc.amp = true;
	v->hevc.sao = false;
	v->hevc.tmvp = false;
	v->hevc.pcm = false;
	v->hevc.transform_skip = false;
	v->hevc.cu_qp_delta = v->d.va_mode != VA_RC_CQP;
	v->hevc.ctu = 32;
	v->hevc.min_cb = 16;

	if (f_ok) {
		VAConfigAttribValEncHEVCFeatures f = { .value = features };
		v->hevc.amp = f.bits.amp != 0;
		v->hevc.sao = f.bits.sao != 0;
		v->hevc.tmvp = f.bits.temporal_mvp != 0;
		v->hevc.pcm = f.bits.pcm != 0;
		v->hevc.transform_skip = f.bits.transform_skip != 0;
		if (v->d.va_mode != VA_RC_CQP)
			v->hevc.cu_qp_delta = f.bits.cu_qp_delta != 0;
	}
	if (b_ok) {
		VAConfigAttribValEncHEVCBlockSizes b = { .value = blocks };
		v->hevc.ctu = 1u << (b.bits.log2_max_coding_tree_block_size_minus3 + 3);
		v->hevc.min_cb = 1u << (b.bits.log2_min_luma_coding_block_size_minus3 + 3);
		v->hevc.log2_min_cb_m3 = b.bits.log2_min_luma_coding_block_size_minus3;
		v->hevc.log2_diff_cb = b.bits.log2_max_coding_tree_block_size_minus3
		                       - b.bits.log2_min_luma_coding_block_size_minus3;
		v->hevc.log2_min_tb_m2 = b.bits.log2_min_luma_transform_block_size_minus2;
		v->hevc.log2_diff_tb = b.bits.log2_max_luma_transform_block_size_minus2
		                       - b.bits.log2_min_luma_transform_block_size_minus2;
		v->hevc.depth_inter = b.bits.max_max_transform_hierarchy_depth_inter;
		v->hevc.depth_intra = b.bits.max_max_transform_hierarchy_depth_intra;
	}
	v->d.hevc_attributes_read = f_ok && b_ok;
	v->d.hevc_features = features;
	v->d.hevc_blocks = blocks;
	registro_dice(LOG_ENCODING,
	              "vadiretta HEVC: the driver %s the attributes — CTB %u, minimum CB %u, "
	              "amp %d, sao %d, tmvp %d, transform_skip %d, cu_qp_delta %d "
	              "(features 0x%x, blocks 0x%x)",
	              v->d.hevc_attributes_read ? "DECLARES" : "does NOT declare (ffmpeg defaults)",
	              v->hevc.ctu, v->hevc.min_cb, v->hevc.amp, v->hevc.sao, v->hevc.tmvp,
	              v->hevc.transform_skip, v->hevc.cu_qp_delta, features, blocks);
}

static void fill_h264_sequence(VaDirect *v)
{
	VAEncSequenceParameterBufferH264 *q = &v->seq.h264;
	uint32_t crop_right = (16 * v->mb_l - v->r.width) / 2;
	uint32_t crop_bottom = (16 * v->mb_a - v->r.height) / 2;
	uint32_t gop = v->r.chiavi_ogni ? v->r.chiavi_ogni : (uint32_t) INT_MAX;

	memset(q, 0, sizeof *q);
	q->seq_parameter_set_id = 0;
	q->level_idc = (uint8_t) v->d.level_idc;
	q->intra_period = gop;
	q->intra_idr_period = gop;
	q->ip_period = 1;
	q->bits_per_second = (uint32_t) (v->d.va_mode == VA_RC_CQP ? 0 : v->r.bandwidth_wire);
	q->max_num_ref_frames = 1;
	q->picture_width_in_mbs = (uint16_t) v->mb_l;
	q->picture_height_in_mbs = (uint16_t) v->mb_a;
	q->seq_fields.bits.chroma_format_idc = 1;
	q->seq_fields.bits.frame_mbs_only_flag = 1;
	q->seq_fields.bits.direct_8x8_inference_flag = 1;
	q->seq_fields.bits.log2_max_frame_num_minus4 = 4;
	q->seq_fields.bits.pic_order_cnt_type = 2;
	q->seq_fields.bits.log2_max_pic_order_cnt_lsb_minus4 = 0;
	q->bit_depth_luma_minus8 = (uint8_t) (v->r.depth - 8);
	q->bit_depth_chroma_minus8 = (uint8_t) (v->r.depth - 8);
	q->frame_cropping_flag = (crop_right || crop_bottom) ? 1 : 0;
	q->frame_crop_right_offset = crop_right;
	q->frame_crop_bottom_offset = crop_bottom;
	q->vui_parameters_present_flag = 1;
	q->vui_fields.bits.timing_info_present_flag = 1;
	q->vui_fields.bits.bitstream_restriction_flag = 1;
	q->vui_fields.bits.log2_max_mv_length_horizontal = 15;
	q->vui_fields.bits.log2_max_mv_length_vertical = 15;
	q->num_units_in_tick = 1;
	q->time_scale = 2u * v->r.fotogrammi_al_secondo;
}

static void fill_hevc_sequence(VaDirect *v)
{
	VAEncSequenceParameterBufferHEVC *q = &v->seq.hevc;
	uint32_t gop = v->r.chiavi_ogni ? v->r.chiavi_ogni : (uint32_t) INT_MAX;

	memset(q, 0, sizeof *q);
	q->general_profile_idc = v->r.depth == 10 ? 2 : 1;
	q->general_level_idc = (uint8_t) v->d.level_idc;
	q->general_tier_flag = v->d.level_idc == 255 ? 1 : 0;
	q->intra_period = gop;
	q->intra_idr_period = gop;
	q->ip_period = 1;
	q->bits_per_second = (uint32_t) (v->d.va_mode == VA_RC_CQP ? 0 : v->r.bandwidth_wire);
	q->pic_width_in_luma_samples = (uint16_t) v->d.surface_width;
	q->pic_height_in_luma_samples = (uint16_t) v->d.surface_height;
	q->seq_fields.bits.chroma_format_idc = 1;
	q->seq_fields.bits.bit_depth_luma_minus8 = (unsigned) (v->r.depth - 8);
	q->seq_fields.bits.bit_depth_chroma_minus8 = (unsigned) (v->r.depth - 8);
	q->seq_fields.bits.amp_enabled_flag = v->hevc.amp;
	q->seq_fields.bits.sample_adaptive_offset_enabled_flag = v->hevc.sao;
	q->seq_fields.bits.sps_temporal_mvp_enabled_flag = v->hevc.tmvp;
	q->log2_min_luma_coding_block_size_minus3 = (uint8_t) v->hevc.log2_min_cb_m3;
	q->log2_diff_max_min_luma_coding_block_size = (uint8_t) v->hevc.log2_diff_cb;
	q->log2_min_transform_block_size_minus2 = (uint8_t) v->hevc.log2_min_tb_m2;
	q->log2_diff_max_min_transform_block_size = (uint8_t) v->hevc.log2_diff_tb;
	q->max_transform_hierarchy_depth_inter = (uint8_t) v->hevc.depth_inter;
	q->max_transform_hierarchy_depth_intra = (uint8_t) v->hevc.depth_intra;
	q->vui_parameters_present_flag = 0;
}

VaDirect *vadirect_open(const VaDevice *d, const VaDirectRequest *r,
                          char *error, size_t error_byte)
{
	VaDirect *v;
	VAConfigAttrib attributes[4];
	int amount = 0;
	uint32_t value;
	VAStatus st;
	bool hevc = r->codec == VADIRECT_HEVC;
	bool p10 = r->depth == 10;

	if (!d || !d->display || !r || !r->width || !r->height) {
		di(error, error_byte, "vadiretta: incomplete request");
		return NULL;
	}
	if (!hevc && p10) {
		di(error, error_byte, "vadiretta: 10-bit H.264 does not open (only 8-bit High)");
		return NULL;
	}
	if (r->qp < 1 || r->qp > 51) {
		di(error, error_byte, "vadiretta: QP %d outside 1..51", r->qp);
		return NULL;
	}
	v = calloc(1, sizeof *v);
	if (!v) {
		di(error, error_byte, "out of memory");
		return NULL;
	}
	v->display = d->display;
	snprintf(v->vendor, sizeof v->vendor, "%s", d->vendor);
	v->r = *r;
	v->config = VA_INVALID_ID;
	v->context = VA_INVALID_ID;
	v->coded = VA_INVALID_ID;
	for (unsigned i = 0; i < REBUILT; i++)
		v->rebuilt[i] = VA_INVALID_ID;
	if (!v->r.fotogrammi_al_secondo)
		v->r.fotogrammi_al_secondo = 30;
	if (!v->r.input_surfaces)
		v->r.input_surfaces = 4;

	/* ── bitrate control: CQP, or QVBR with the cap ──────────────────────── */
	if (r->bandwidth_wire > 0) {
		v->d.va_mode = VA_RC_QVBR;
		/* ffmpeg: under a regulated mode pic_init_qp and slice_qp_delta are
		 * 26 (H.264) and 30 (HEVC), and the requested QP is the quality_factor. */
		v->fixed_qp = hevc ? 30 : 26;
	} else {
		v->d.va_mode = VA_RC_CQP;
		v->fixed_qp = r->qp;
	}

	/* ── the surface format, and the driver's declaration of it ──────────── */
	v->d.rt_format = p10 ? VA_RT_FORMAT_YUV420_10BPP : VA_RT_FORMAT_YUV420;
	v->d.input_fourcc = p10 ? VA_FOURCC_P010 : VA_FOURCC_NV12;
	if (attribute(d->display, r->profile, r->entrypoint, VAConfigAttribRTFormat, &value)) {
		if (!(value & v->d.rt_format)) {
			di(error, error_byte,
			   "the driver does not declare format %s for this profile/entrypoint (0x%x)",
			   p10 ? "YUV420_10" : "YUV420", value);
			free(v);
			return NULL;
		}
		attributes[amount++] = (VAConfigAttrib){ .type = VAConfigAttribRTFormat,
			                                    .value = v->d.rt_format };
	}
	if (attribute(d->display, r->profile, r->entrypoint, VAConfigAttribRateControl, &value)) {
		if (!(value & v->d.va_mode)) {
			di(error, error_byte, "the driver does not declare bitrate mode 0x%x (it has 0x%x)",
			   v->d.va_mode, value);
			free(v);
			return NULL;
		}
		attributes[amount++] = (VAConfigAttrib){ .type = VAConfigAttribRateControl,
			                                    .value = v->d.va_mode };
	}
	/* The packed headers we ask to write ourselves: the
	 * same three as ffmpeg (SEQUENCE = SPS/PPS/VPS, SLICE, MISC = SEI). */
	if (attribute(d->display, r->profile, r->entrypoint, VAConfigAttribEncPackedHeaders,
	              &value)) {
		v->d.packed_headers_driver = value;
		v->d.packed_headers = value & (VA_ENC_PACKED_HEADER_SEQUENCE
		                                | VA_ENC_PACKED_HEADER_SLICE
		                                | VA_ENC_PACKED_HEADER_MISC);
		if (v->d.packed_headers)
			attributes[amount++] = (VAConfigAttrib){ .type = VAConfigAttribEncPackedHeaders,
				                                    .value = v->d.packed_headers };
	}

	/* ── P as B?  Ask the driver, like ffmpeg (VAConfigAttribPredictionDirection) */
	v->d.p_come_b = false;
	{
		uint32_t references = 0, direction = 0;
		uint32_t l0 = 0, l1 = 0;
		if (attribute(d->display, r->profile, r->entrypoint, VAConfigAttribEncMaxRefFrames,
		              &references)) {
			l0 = references & 0xFFFF;
			l1 = (references >> 16) & 0xFFFF;
		}
		if (l0 < 1) {
			di(error, error_byte, "the driver declares no reference frame");
			free(v);
			return NULL;
		}
		if (attribute(d->display, r->profile, r->entrypoint,
		              VAConfigAttribPredictionDirection, &direction)) {
			if ((direction & VA_PREDICTION_DIRECTION_BI_NOT_EMPTY) && l0 > 0 && l1 > 0)
				v->d.p_come_b = true;
		}
		registro_dice(LOG_ENCODING,
		              "vadiretta: declared references l0=%u l1=%u, directions 0x%x ⇒ the Ps "
		              "are %s", l0, l1, direction,
		              v->d.p_come_b ? "B slices «GPB» (the driver cannot do P)" : "slice P");
	}

	/* ── the aligned sizes and the level ─────────────────────────────────── */
	if (hevc) {
		hevc_capabilities(v);
		v->d.block = v->hevc.ctu;
		v->d.surface_width = align(r->width, v->hevc.min_cb);
		v->d.surface_height = align(r->height, v->hevc.min_cb);
		v->ctb_l = (v->d.surface_width + v->hevc.ctu - 1) / v->hevc.ctu;
		v->ctb_a = (v->d.surface_height + v->hevc.ctu - 1) / v->hevc.ctu;
		v->d.level_idc = r->level_idc > 0
		                       ? r->level_idc
		                       : hevc_level(v->d.va_mode == VA_RC_CQP ? 0 : r->bandwidth_point,
		                                      v->d.surface_width,
		                                      v->d.surface_height, 1);
	} else {
		v->mb_l = (r->width + 15) / 16;
		v->mb_a = (r->height + 15) / 16;
		v->d.block = 16;
		v->d.surface_width = v->mb_l * 16;
		v->d.surface_height = v->mb_a * 16;
		v->d.level_idc = r->level_idc > 0
		                       ? r->level_idc
		                       : h264_level(v->d.va_mode == VA_RC_CQP ? 0 : r->bandwidth_wire,
		                                      (int) v->r.fotogrammi_al_secondo,
		                                      v->mb_l, v->mb_a, 1);
	}

	/* ── configuration and context ───────────────────────────────────────── */
	st = vaCreateConfig(d->display, r->profile, r->entrypoint, attributes, amount, &v->config);
	if (st != VA_STATUS_SUCCESS) {
		di(error, error_byte, "vaCreateConfig: %s", vaErrorStr(st));
		vadirect_close(v);
		return NULL;
	}
	/* the RECONSTRUCTED surfaces, at the aligned size */
	st = vaCreateSurfaces(d->display, v->d.rt_format, v->d.surface_width,
	                      v->d.surface_height, v->rebuilt, REBUILT, NULL, 0);
	if (st != VA_STATUS_SUCCESS) {
		di(error, error_byte, "the %ux%u reconstructed surfaces were not created: %s",
		   v->d.surface_width, v->d.surface_height, vaErrorStr(st));
		for (unsigned i = 0; i < REBUILT; i++)
			v->rebuilt[i] = VA_INVALID_ID;
		vadirect_close(v);
		return NULL;
	}
	st = vaCreateContext(d->display, v->config, (int) v->d.surface_width,
	                     (int) v->d.surface_height, VA_PROGRESSIVE, v->rebuilt,
	                     REBUILT, &v->context);
	if (st != VA_STATUS_SUCCESS) {
		di(error, error_byte, "vaCreateContext %ux%u: %s", v->d.surface_width,
		   v->d.surface_height, vaErrorStr(st));
		v->context = VA_INVALID_ID;
		vadirect_close(v);
		return NULL;
	}
	/* the input pool, at the size of the CANVAS: the driver pads by itself */
	v->ingress = calloc(v->r.input_surfaces, sizeof *v->ingress);
	if (!v->ingress) {
		di(error, error_byte, "out of memory for the pool");
		vadirect_close(v);
		return NULL;
	}
	{
		VASurfaceAttrib fmt = {
			.type = VASurfaceAttribPixelFormat,
			.flags = VA_SURFACE_ATTRIB_SETTABLE,
			.value.type = VAGenericValueTypeInteger,
			.value.value.i = (int) v->d.input_fourcc,
		};
		st = vaCreateSurfaces(d->display, v->d.rt_format, r->width, r->height,
		                      v->ingress, v->r.input_surfaces, &fmt, 1);
	}
	if (st != VA_STATUS_SUCCESS) {
		di(error, error_byte, "the input pool (%u x %s %ux%u) was not created: %s",
		   v->r.input_surfaces, p10 ? "P010" : "NV12", r->width, r->height,
		   vaErrorStr(st));
		free(v->ingress);
		v->ingress = NULL;
		vadirect_close(v);
		return NULL;
	}
	v->how_many_ingress = v->r.input_surfaces;
	/* the buffer of encoded bytes */
	v->coded_byte = (size_t) 3 * v->d.surface_width * v->d.surface_height + CODED_MARGIN;
	st = vaCreateBuffer(d->display, v->context, VAEncCodedBufferType, (unsigned) v->coded_byte,
	                    1, NULL, &v->coded);
	if (st != VA_STATUS_SUCCESS) {
		di(error, error_byte, "the %zu-byte coded buffer was not created: %s",
		   v->coded_byte, vaErrorStr(st));
		v->coded = VA_INVALID_ID;
		vadirect_close(v);
		return NULL;
	}
	v->output_capabilities = v->coded_byte;
	v->output = malloc(v->output_capabilities);
	if (!v->output) {
		di(error, error_byte, "out of memory for the output");
		vadirect_close(v);
		return NULL;
	}
	/* Is `vaSyncBuffer` there?  Ask with the null buffer, like ffmpeg. */
	v->d.sync_buffer = vaSyncBuffer(d->display, VA_INVALID_ID, 0) != VA_STATUS_ERROR_UNIMPLEMENTED;

	if (hevc)
		fill_hevc_sequence(v);
	else
		fill_h264_sequence(v);

	registro_dice(LOG_ENCODING,
	              "vadiretta open: %s %d bit %ux%u (surface %ux%u, block %u) · "
	              "profile %d entrypoint %d · %s (qp %d) · level %d%s · packed header "
	              "0x%x (driver 0x%x) · %s · %u input surfaces",
	              hevc ? "HEVC" : "H.264", r->depth, r->width, r->height,
	              v->d.surface_width, v->d.surface_height, v->d.block,
	              (int) r->profile, (int) r->entrypoint,
	              v->d.va_mode == VA_RC_CQP ? "CQP" : "QVBR", r->qp, v->d.level_idc,
	              r->level_idc > 0 ? " (imposed)" : " (computed like ffmpeg)",
	              v->d.packed_headers, v->d.packed_headers_driver,
	              v->d.sync_buffer ? "vaSyncBuffer" : "vaSyncSurface", v->how_many_ingress);
	return v;
}

void vadirect_close(VaDirect *v)
{
	if (!v)
		return;
	if (v->coded != VA_INVALID_ID)
		vaDestroyBuffer(v->display, v->coded);
	if (v->context != VA_INVALID_ID)
		vaDestroyContext(v->display, v->context);
	if (v->ingress) {
		vaDestroySurfaces(v->display, v->ingress, (int) v->how_many_ingress);
		free(v->ingress);
	}
	if (v->rebuilt[0] != VA_INVALID_ID)
		vaDestroySurfaces(v->display, v->rebuilt, REBUILT);
	if (v->config != VA_INVALID_ID)
		vaDestroyConfig(v->display, v->config);
	free(v->output);
	free(v);
}

const VaDirectDeclaration *vadirect_declaration(const VaDirect *v)
{
	return v ? &v->d : NULL;
}

VASurfaceID vadirect_input_surface(VaDirect *v)
{
	VASurfaceID s;

	if (!v || !v->how_many_ingress)
		return VA_INVALID_ID;
	s = v->ingress[v->next_ingress];
	v->next_ingress = (v->next_ingress + 1) % v->how_many_ingress;
	return s;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 4. THE ROUND OF ONE FRAME — `vaapi_encode_issue()` + `vaapi_encode_output()`
 *
 * The order of the buffers is ffmpeg's: sequence (on the IDR), the «global»
 * parameters (on the IDR: bitrate, HRD, frame rate), picture, the packed
 * sequence headers (on the IDR), the SEI, then the packed slice
 * header and the slice parameters.
 * ═══════════════════════════════════════════════════════════════════════════ */

typedef struct {
	VABufferID id[24];
	int amount;
	bool fault;
	char error[256];
} Buffer;

static void buffer_param(VaDirect *v, Buffer *b, VABufferType kind, const void *data,
                         size_t byte)
{
	VAStatus st;

	if (b->fault || b->amount >= (int) (sizeof b->id / sizeof b->id[0])) {
		b->fault = true;
		return;
	}
	st = vaCreateBuffer(v->display, v->context, kind, (unsigned) byte, 1, (void *) data,
	                    &b->id[b->amount]);
	if (st != VA_STATUS_SUCCESS) {
		b->fault = true;
		snprintf(b->error, sizeof b->error, "vaCreateBuffer(type %d, %zu bytes): %s",
		         (int) kind, byte, vaErrorStr(st));
		return;
	}
	b->amount++;
}

static void buffer_misc(VaDirect *v, Buffer *b, VAEncMiscParameterType kind, const void *data,
                        size_t byte)
{
	uint8_t box[256];
	VAEncMiscParameterBuffer *head = (VAEncMiscParameterBuffer *) box;

	if (sizeof(VAEncMiscParameterBuffer) + byte > sizeof box) {
		b->fault = true;
		return;
	}
	memset(box, 0, sizeof box);
	head->type = kind;
	memcpy(head->data, data, byte);
	buffer_param(v, b, VAEncMiscParameterBufferType, box,
	             sizeof(VAEncMiscParameterBuffer) + byte);
}

/* A packed header: the parameter (type, length in bits, «already has the
 * emulation bytes») and the data.  ⚠ `has_emulation_bytes = 1`: we put the
 *   `03`s in ourselves in `nal_annexb()`, the driver must not add them again. */
static void buffer_packed(VaDirect *v, Buffer *b, unsigned kind, const uint8_t *data,
                          size_t byte)
{
	VAEncPackedHeaderParameterBuffer p = {
		.type = kind,
		.bit_length = (unsigned) (byte * 8),
		.has_emulation_bytes = 1,
	};

	if (!byte) {
		b->fault = true;
		snprintf(b->error, sizeof b->error, "a packed header is empty (type %u)",
		         kind);
		return;
	}
	buffer_param(v, b, VAEncPackedHeaderParameterBufferType, &p, sizeof p);
	buffer_param(v, b, VAEncPackedHeaderDataBufferType, data, byte);
}

static void global_parameters(VaDirect *v, Buffer *b)
{
	if (v->d.va_mode != VA_RC_CQP) {
		/* `vaapi_encode_init_rate_control`: wire, share of the point, buffer
		 * window in ms, and the QP as the QVBR quality factor. */
		VAEncMiscParameterRateControl rc = {
			.bits_per_second = (uint32_t) v->r.bandwidth_wire,
			.target_percentage = (uint32_t) (v->r.bandwidth_point * 100 / v->r.bandwidth_wire),
			.window_size = (uint32_t) ((int64_t) v->r.reservoir_bit * 1000 / v->r.bandwidth_wire),
			.initial_qp = 0,
			.min_qp = 0,
			.basic_unit_size = 0,
			.ICQ_quality_factor = (uint32_t) v->r.qp,
			.max_qp = 0,
			.quality_factor = (uint32_t) v->r.qp,
		};
		VAEncMiscParameterHRD hrd = {
			.initial_buffer_fullness = (uint32_t) ((int64_t) v->r.reservoir_bit * 3 / 4),
			.buffer_size = (uint32_t) v->r.reservoir_bit,
		};
		rc.rc_flags.bits.mb_rate_control = 2; /* «blbrc ? 1 : 2», and blbrc is off */
		buffer_misc(v, b, VAEncMiscParameterTypeRateControl, &rc, sizeof rc);
		buffer_misc(v, b, VAEncMiscParameterTypeHRD, &hrd, sizeof hrd);
	}
	{
		VAEncMiscParameterFrameRate fr = {
			.framerate = (1u << 16) | v->r.fotogrammi_al_secondo, /* den << 16 | num */
		};
		buffer_misc(v, b, VAEncMiscParameterTypeFrameRate, &fr, sizeof fr);
	}
}

static bool read_output(VaDirect *v, char *error, size_t error_byte)
{
	VACodedBufferSegment *segment = NULL, *s;
	VAStatus st;
	size_t total = 0;

	st = vaMapBuffer(v->display, v->coded, (void **) &segment);
	if (st != VA_STATUS_SUCCESS) {
		di(error, error_byte, "vaMapBuffer on the encoded bytes: %s", vaErrorStr(st));
		return false;
	}
	for (s = segment; s; s = s->next)
		total += s->size;
	if (total > v->output_capabilities) {
		uint8_t *fresh = realloc(v->output, total);
		if (!fresh) {
			vaUnmapBuffer(v->display, v->coded);
			di(error, error_byte, "out of memory for %zu output bytes", total);
			return false;
		}
		v->output = fresh;
		v->output_capabilities = total;
	}
	total = 0;
	for (s = segment; s; s = s->next) {
		memcpy(v->output + total, s->buf, s->size);
		total += s->size;
	}
	v->output_byte = total;
	vaUnmapBuffer(v->display, v->coded);
	if (!total) {
		di(error, error_byte, "the driver returned zero bytes");
		return false;
	}
	return true;
}

bool vadirect_encode(VaDirect *v, VASurfaceID ingress, bool key,
                        const uint8_t **data, size_t *byte, char *error, size_t error_byte)
{
	Buffer b;
	uint8_t header[4 * MAX_HEADER];
	size_t n, tot;
	VAStatus st, fine;
	bool hevc = v->r.codec == VADIRECT_HEVC;
	bool idr;
	unsigned ref;

	if (!v || ingress == VA_INVALID_ID) {
		di(error, error_byte, "vadiretta: nothing to encode");
		return false;
	}
	memset(&b, 0, sizeof b);

	/* ── who this frame is ─────────────────────────────────────────────── */
	idr = key || !v->reference_valid || v->order == 0
	      || (v->r.chiavi_ogni && v->in_gop >= v->r.chiavi_ogni);
	if (idr) {
		v->last_idr = v->order;
		v->in_gop = 0;
		v->frame_num = 0;
		v->poc = 0;
		if (v->order)
			v->idr_pic_id = (v->idr_pic_id + 1) & 0xFFFFu;
	} else {
		/* `hpic->frame_num = hprev->frame_num + prev->is_reference`: +1, always */
		v->frame_num = v->frame_num_reference + 1;
		v->poc = (int32_t) (v->order - v->last_idr);
	}
	v->in_gop++;
	ref = v->rebuilt_reference;
	v->rebuilt_current = (ref + 1) % REBUILT;

	/* ── 1. sequence and global parameters, on the IDR ────────────────── */
	if (idr) {
		if (hevc)
			buffer_param(v, &b, VAEncSequenceParameterBufferType, &v->seq.hevc, sizeof v->seq.hevc);
		else
			buffer_param(v, &b, VAEncSequenceParameterBufferType, &v->seq.h264, sizeof v->seq.h264);
		global_parameters(v, &b);
	}

	/* ── 2. the picture ───────────────────────────────────────────────── */
	if (hevc) {
		VAEncPictureParameterBufferHEVC p;
		memset(&p, 0, sizeof p);
		p.decoded_curr_pic.picture_id = v->rebuilt[v->rebuilt_current];
		p.decoded_curr_pic.pic_order_cnt = v->poc;
		p.decoded_curr_pic.flags = 0;
		for (unsigned i = 0; i < 15; i++) {
			p.reference_frames[i].picture_id = VA_INVALID_ID;
			p.reference_frames[i].flags = VA_PICTURE_HEVC_INVALID;
		}
		if (!idr) {
			p.reference_frames[0].picture_id = v->rebuilt[ref];
			p.reference_frames[0].pic_order_cnt = v->poc_reference;
			p.reference_frames[0].flags = VA_PICTURE_HEVC_RPS_ST_CURR_BEFORE;
		}
		p.coded_buf = v->coded;
		p.collocated_ref_pic_index = v->hevc.tmvp ? 0 : 0xff;
		p.last_picture = 0;
		p.pic_init_qp = (uint8_t) v->fixed_qp;
		p.diff_cu_qp_delta_depth = (uint8_t) (v->hevc.cu_qp_delta ? v->hevc.log2_diff_cb : 0);
		p.log2_parallel_merge_level_minus2 = 0;
		p.ctu_max_bitsize_allowed = 0;
		p.num_ref_idx_l0_default_active_minus1 = 0;
		p.num_ref_idx_l1_default_active_minus1 = 0;
		p.slice_pic_parameter_set_id = 0;
		p.nal_unit_type = idr ? 19 : 1;
		p.pic_fields.bits.idr_pic_flag = idr;
		p.pic_fields.bits.coding_type = idr ? 1 : 2; /* I / P: the GPB is also «P» here */
		p.pic_fields.bits.reference_pic_flag = 1;
		p.pic_fields.bits.transform_skip_enabled_flag = v->hevc.transform_skip;
		p.pic_fields.bits.cu_qp_delta_enabled_flag = v->hevc.cu_qp_delta;
		p.pic_fields.bits.pps_loop_filter_across_slices_enabled_flag = 1;
		buffer_param(v, &b, VAEncPictureParameterBufferType, &p, sizeof p);
	} else {
		VAEncPictureParameterBufferH264 p;
		memset(&p, 0, sizeof p);
		p.CurrPic.picture_id = v->rebuilt[v->rebuilt_current];
		p.CurrPic.frame_idx = v->frame_num;
		p.CurrPic.flags = 0;
		p.CurrPic.TopFieldOrderCnt = 2 * v->poc; /* poc type 2: twice */
		p.CurrPic.BottomFieldOrderCnt = 2 * v->poc;
		for (unsigned i = 0; i < 16; i++) {
			p.ReferenceFrames[i].picture_id = VA_INVALID_ID;
			p.ReferenceFrames[i].flags = VA_PICTURE_H264_INVALID;
		}
		if (!idr) {
			p.ReferenceFrames[0].picture_id = v->rebuilt[ref];
			p.ReferenceFrames[0].frame_idx = v->frame_num_reference;
			p.ReferenceFrames[0].flags = VA_PICTURE_H264_SHORT_TERM_REFERENCE;
			p.ReferenceFrames[0].TopFieldOrderCnt = 2 * v->poc_reference;
			p.ReferenceFrames[0].BottomFieldOrderCnt = 2 * v->poc_reference;
		}
		p.coded_buf = v->coded;
		p.pic_parameter_set_id = 0;
		p.seq_parameter_set_id = 0;
		p.last_picture = 0;
		p.frame_num = (uint16_t) v->frame_num;
		p.pic_init_qp = (uint8_t) v->fixed_qp;
		p.num_ref_idx_l0_active_minus1 = 0;
		p.num_ref_idx_l1_active_minus1 = 0;
		p.chroma_qp_index_offset = 0;
		p.second_chroma_qp_index_offset = 0;
		p.pic_fields.bits.idr_pic_flag = idr;
		p.pic_fields.bits.reference_pic_flag = 1;
		p.pic_fields.bits.entropy_coding_mode_flag = 1;
		p.pic_fields.bits.transform_8x8_mode_flag = 1;
		buffer_param(v, &b, VAEncPictureParameterBufferType, &p, sizeof p);
	}

	/* ── 3. the packed headers ────────────────────────────────────────── */
	if (idr && (v->d.packed_headers & VA_ENC_PACKED_HEADER_SEQUENCE)) {
		tot = 0;
		if (hevc) {
			n = hevc_vps(v, header + tot, sizeof header - tot);
			tot += n;
			n = n ? hevc_sps(v, header + tot, sizeof header - tot) : 0;
			tot += n;
			n = n ? hevc_pps(v, header + tot, sizeof header - tot) : 0;
			tot += n;
		} else {
			n = h264_sps(v, header + tot, sizeof header - tot);
			tot += n;
			n = n ? h264_pps(v, header + tot, sizeof header - tot) : 0;
			tot += n;
		}
		buffer_packed(v, &b, VAEncPackedHeaderSequence, header, n ? tot : 0);
	}
	if (!hevc && (v->d.packed_headers & VA_ENC_PACKED_HEADER_MISC)) {
		n = h264_sei(v, idr, header, sizeof header);
		if (n)
			buffer_packed(v, &b, VAEncPackedHeaderRawData, header, n);
	}

	/* ── 4. the slice: packed header and parameters ───────────────────── */
	if (v->d.packed_headers & VA_ENC_PACKED_HEADER_SLICE) {
		n = hevc ? hevc_slice(v, idr, header, sizeof header)
		         : h264_slice(v, idr, header, sizeof header);
		buffer_packed(v, &b, VAEncPackedHeaderSlice, header, n);
	}
	if (hevc) {
		VAEncSliceParameterBufferHEVC s;
		memset(&s, 0, sizeof s);
		s.slice_segment_address = 0;
		s.num_ctu_in_slice = v->ctb_l * v->ctb_a;
		s.slice_type = idr ? 2 : (v->d.p_come_b ? 0 : 1);
		s.slice_pic_parameter_set_id = 0;
		for (unsigned i = 0; i < 15; i++) {
			s.ref_pic_list0[i].picture_id = VA_INVALID_ID;
			s.ref_pic_list0[i].flags = VA_PICTURE_HEVC_INVALID;
			s.ref_pic_list1[i].picture_id = VA_INVALID_ID;
			s.ref_pic_list1[i].flags = VA_PICTURE_HEVC_INVALID;
		}
		if (!idr) {
			s.ref_pic_list0[0].picture_id = v->rebuilt[ref];
			s.ref_pic_list0[0].pic_order_cnt = v->poc_reference;
			s.ref_pic_list0[0].flags = VA_PICTURE_HEVC_RPS_ST_CURR_BEFORE;
			if (v->d.p_come_b) {
				/* GPB: L1 = L0, it is ffmpeg's «Reference for GPB B-frame» */
				for (unsigned i = 0; i < 15; i++) {
					s.ref_pic_list1[i].picture_id = s.ref_pic_list0[i].picture_id;
					s.ref_pic_list1[i].pic_order_cnt = s.ref_pic_list0[i].pic_order_cnt;
					s.ref_pic_list1[i].flags = s.ref_pic_list0[i].flags;
				}
			}
		}
		s.max_num_merge_cand = 5;
		s.slice_qp_delta = 0;
		s.slice_fields.bits.last_slice_of_pic_flag = 1;
		s.slice_fields.bits.slice_temporal_mvp_enabled_flag = idr ? 0 : v->hevc.tmvp;
		s.slice_fields.bits.slice_sao_luma_flag = v->hevc.sao;
		s.slice_fields.bits.slice_sao_chroma_flag = v->hevc.sao;
		s.slice_fields.bits.collocated_from_l0_flag = idr ? 0 : 1;
		buffer_param(v, &b, VAEncSliceParameterBufferType, &s, sizeof s);
	} else {
		VAEncSliceParameterBufferH264 s;
		memset(&s, 0, sizeof s);
		s.macroblock_address = 0;
		s.num_macroblocks = v->mb_l * v->mb_a;
		s.macroblock_info = VA_INVALID_ID;
		s.slice_type = idr ? 2 : 0; /* 7 % 5 = 2 (I) · 5 % 5 = 0 (P) */
		s.pic_parameter_set_id = 0;
		s.idr_pic_id = (uint16_t) v->idr_pic_id;
		s.pic_order_cnt_lsb = (uint16_t) ((2 * v->poc) & 0xF); /* log2_max_poc_lsb_minus4 = 0 */
		s.direct_spatial_mv_pred_flag = 1;
		for (unsigned i = 0; i < 32; i++) {
			s.RefPicList0[i].picture_id = VA_INVALID_ID;
			s.RefPicList0[i].flags = VA_PICTURE_H264_INVALID;
			s.RefPicList1[i].picture_id = VA_INVALID_ID;
			s.RefPicList1[i].flags = VA_PICTURE_H264_INVALID;
		}
		if (!idr) {
			s.RefPicList0[0].picture_id = v->rebuilt[ref];
			s.RefPicList0[0].frame_idx = v->frame_num_reference;
			s.RefPicList0[0].flags = VA_PICTURE_H264_SHORT_TERM_REFERENCE;
			s.RefPicList0[0].TopFieldOrderCnt = 2 * v->poc_reference;
			s.RefPicList0[0].BottomFieldOrderCnt = 2 * v->poc_reference;
		}
		s.slice_qp_delta = 0;
		buffer_param(v, &b, VAEncSliceParameterBufferType, &s, sizeof s);
	}

	if (b.fault) {
		for (int i = 0; i < b.amount; i++)
			vaDestroyBuffer(v->display, b.id[i]);
		di(error, error_byte, "the frame buffers were not created: %s",
		   b.error[0] ? b.error : "too many, or an empty header");
		return false;
	}

	/* ── 5. begin / render / end ──────────────────────────────────────── */
	st = vaBeginPicture(v->display, v->context, ingress);
	if (st != VA_STATUS_SUCCESS) {
		for (int i = 0; i < b.amount; i++)
			vaDestroyBuffer(v->display, b.id[i]);
		di(error, error_byte, "vaBeginPicture: %s", vaErrorStr(st));
		return false;
	}
	st = vaRenderPicture(v->display, v->context, b.id, b.amount);
	fine = vaEndPicture(v->display, v->context);
	for (int i = 0; i < b.amount; i++)
		vaDestroyBuffer(v->display, b.id[i]);
	if (st != VA_STATUS_SUCCESS || fine != VA_STATUS_SUCCESS) {
		di(error, error_byte, "%s: %s", st != VA_STATUS_SUCCESS ? "vaRenderPicture" : "vaEndPicture",
		   vaErrorStr(st != VA_STATUS_SUCCESS ? st : fine));
		return false;
	}

	/* ── 6. WAIT, and read the bytes ──────────────────────────────────── */
	if (v->d.sync_buffer)
		st = vaSyncBuffer(v->display, v->coded, VA_TIMEOUT_INFINITE);
	else
		st = vaSyncSurface(v->display, ingress);
	if (st != VA_STATUS_SUCCESS) {
		di(error, error_byte, "waiting for the encode failed: %s", vaErrorStr(st));
		return false;
	}
	if (!read_output(v, error, error_byte))
		return false;

	/* ── 7. this frame is the reference for the next ──────────────────── */
	v->reference_valid = true;
	v->rebuilt_reference = v->rebuilt_current;
	v->frame_num_reference = v->frame_num;
	v->poc_reference = v->poc;
	v->sei_identifier_written = true;
	v->order++;
	*data = v->output;
	*byte = v->output_byte;
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 5. THE ROUTE FROM MEMORY
 * ═══════════════════════════════════════════════════════════════════════════ */

/* Writes `lines` rows of `byte_per_line` into an image derived from or created
 * on the surface: first `vaDeriveImage` (no extra copy), and if the
 * driver does not give it, `vaCreateImage` + `vaPutImage`. */
typedef struct {
	const uint8_t *piano[3];
	uint32_t step[3];
	uint32_t lines[3];         /* rows per plane */
	uint32_t byte_per_line[3];
	unsigned plans;
} Plans;

static bool write_image(VaDirect *v, VASurfaceID dest, unsigned fourcc, uint32_t l,
                            uint32_t a, const Plans *p, char *error, size_t error_byte)
{
	VAImage img;
	VAStatus st;
	uint8_t *map = NULL;
	bool derivative = true;

	st = vaDeriveImage(v->display, dest, &img);
	if (st != VA_STATUS_SUCCESS || img.format.fourcc != fourcc) {
		VAImageFormat f;
		if (st == VA_STATUS_SUCCESS)
			vaDestroyImage(v->display, img.image_id);
		derivative = false;
		memset(&f, 0, sizeof f);
		f.fourcc = fourcc;
		f.byte_order = VA_LSB_FIRST;
		f.bits_per_pixel = (fourcc == VA_FOURCC_NV12) ? 12 : (fourcc == VA_FOURCC_P010 ? 24 : 32);
		st = vaCreateImage(v->display, &f, (int) l, (int) a, &img);
		if (st != VA_STATUS_SUCCESS) {
			di(error, error_byte, "neither vaDeriveImage nor vaCreateImage (%c%c%c%c): %s",
			   fourcc & 0xff, (fourcc >> 8) & 0xff, (fourcc >> 16) & 0xff, (fourcc >> 24) & 0xff,
			   vaErrorStr(st));
			return false;
		}
	}
	st = vaMapBuffer(v->display, img.buf, (void **) &map);
	if (st != VA_STATUS_SUCCESS) {
		vaDestroyImage(v->display, img.image_id);
		di(error, error_byte, "vaMapBuffer on the image: %s", vaErrorStr(st));
		return false;
	}
	for (unsigned k = 0; k < p->plans && k < img.num_planes; k++) {
		uint8_t *dove = map + img.offsets[k];
		uint32_t img_stride = img.pitches[k];
		uint32_t n = p->byte_per_line[k] < img_stride ? p->byte_per_line[k] : img_stride;
		for (uint32_t r = 0; r < p->lines[k]; r++)
			memcpy(dove + (size_t) r * img_stride, p->piano[k] + (size_t) r * p->step[k], n);
	}
	vaUnmapBuffer(v->display, img.buf);
	if (!derivative) {
		st = vaPutImage(v->display, dest, img.image_id, 0, 0, l, a, 0, 0, l, a);
		if (st != VA_STATUS_SUCCESS) {
			vaDestroyImage(v->display, img.image_id);
			di(error, error_byte, "vaPutImage: %s", vaErrorStr(st));
			return false;
		}
	}
	vaDestroyImage(v->display, img.image_id);
	return true;
}

/*
 * ⭐ NV12 / P010 already converted on the CPU (`colors709.c`), straight into the input
 *    surface: it is the route that existed before phase 18 (conversion in
 *    system memory, then the upload), redone without libswscale.
 * ⛔ RGB is NOT uploaded for the VPP to convert: `[M]` 30 Sep 2026,
 *    `benches/18-card/18-confronto.sh`, the VPP from memory loses quality
 *    and bytes compared with the CPU conversion (Intel 1080p H.264 −1 dB and +82 %
 *    bytes, HEVC −4 dB and +255 %; Radeon −1…−6 dB).  The VPP stays ONLY on
 *    zero copy, where the frame is already on the card.
 */
bool vadirect_load_nv12(VaDirect *v, VASurfaceID dest, const uint8_t *y, uint32_t stride_y,
                           const uint8_t *uv, uint32_t stride_uv, char *error, size_t error_byte)
{
	uint32_t l = v->r.width, a = v->r.height;
	Plans p = {
		.piano = { y, uv },
		.step = { stride_y, stride_uv },
		.lines = { a, a / 2 },
		.byte_per_line = { l, l },
		.plans = 2,
	};

	return write_image(v, dest, VA_FOURCC_NV12, l, a, &p, error, error_byte);
}

bool vadirect_load_p010(VaDirect *v, VASurfaceID dest, const uint16_t *y, uint32_t stride_y,
                           const uint16_t *uv, uint32_t stride_uv, char *error, size_t error_byte)
{
	uint32_t l = v->r.width, a = v->r.height;
	Plans p = {
		.piano = { (const uint8_t *) y, (const uint8_t *) uv },
		.step = { stride_y, stride_uv },
		.lines = { a, a / 2 },
		.byte_per_line = { l * 2, l * 2 },
		.plans = 2,
	};

	return write_image(v, dest, VA_FOURCC_P010, l, a, &p, error, error_byte);
}

bool vadirect_load_yuv420p10(VaDirect *v, VASurfaceID dest, const uint8_t *pixel,
                                uint32_t stride_y, char *error, size_t error_byte)
{
	/* yuv420p10le (three planes, 10 bits in the LOW bits of 16) → P010 (Y, then
	 * interleaved UV, 10 bits in the HIGH bits of 16).  ⛔ They are two different
	 *    formats with the same number of bits: copying them as they are would give
	 *    a dark image (`encoder.c`, the note on P010). */
	uint32_t l = v->r.width, a = v->r.height;
	uint32_t py = stride_y ? stride_y : l * 2;
	const uint8_t *y = pixel;
	const uint8_t *u = y + (size_t) py * a;
	const uint8_t *w = u + (size_t) (py / 2) * (a / 2);
	uint16_t *tmp = malloc((size_t) l * a * 2 + (size_t) l * (a / 2) * 2);
	uint16_t *uv;
	Plans p;
	bool outcome;

	if (!tmp) {
		di(error, error_byte, "out of memory for the staging P010");
		return false;
	}
	uv = tmp + (size_t) l * a;
	for (uint32_t r = 0; r < a; r++) {
		const uint16_t *source_dir = (const uint16_t *) (y + (size_t) r * py);
		uint16_t *dst = tmp + (size_t) r * l;
		for (uint32_t x = 0; x < l; x++)
			dst[x] = (uint16_t) (source_dir[x] << 6);
	}
	for (uint32_t r = 0; r < a / 2; r++) {
		const uint16_t *su = (const uint16_t *) (u + (size_t) r * (py / 2));
		const uint16_t *sv = (const uint16_t *) (w + (size_t) r * (py / 2));
		uint16_t *dst = uv + (size_t) r * l;
		for (uint32_t x = 0; x < l / 2; x++) {
			dst[2 * x] = (uint16_t) (su[x] << 6);
			dst[2 * x + 1] = (uint16_t) (sv[x] << 6);
		}
	}
	p = (Plans){
		.piano = { (const uint8_t *) tmp, (const uint8_t *) uv },
		.step = { l * 2, l * 2 },
		.lines = { a, a / 2 },
		.byte_per_line = { l * 2, l * 2 },
		.plans = 2,
	};
	outcome = write_image(v, dest, VA_FOURCC_P010, l, a, &p, error, error_byte);
	free(tmp);
	return outcome;
}
