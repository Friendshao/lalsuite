/* constants */
#define EAH_GENERIC 0
#define EAH_SINCOS_ROUND_FLOOR       EAH_GENERIC
#define EAH_SINCOS_ROUND_INT4        4
#define EAH_SINCOS_ROUND_INT8        8
#define EAH_SINCOS_ROUND_MODF        2
#define EAH_SINCOS_VARIANT_LAL       EAH_GENERIC
#define EAH_SINCOS_VARIANT_LINEAR    9
#define EAH_HOTLOOP_VARIANT_LAL      EAH_GENERIC
#define EAH_HOTLOOP_VARIANT_SSE      3
#define EAH_HOTLOOP_VARIANT_ALTIVEC  2
#define EAH_HOTLOOP_VARIANT_AUTOVECT EAH_GENERIC
#define EAH_HOTLOOP_VARIANT_x87      EAH_GENERIC
#define EAH_HOUGH_PREFETCH_NONE      EAH_GENERIC
#define EAH_HOUGH_PREFETCH_DIRECT    1
#define EAH_HOUGH_PREFETCH_C         2
#define EAH_HOUGH_ASS_NONE           EAH_GENERIC
#define EAH_HOUGH_ASS_X87            7

#ifndef EAH_OPTIIZATION
#define EAH_OPTIMIZATION EAH_GENERIC
#else

#if   EAH_OPTIIZATION == 1 /* fastest portable code */
#define EAH_SINCOS_VARIANT  EAH_SINCOS_VARIANT_LINEAR
#define EAH_SINCOS_ROUND    EAH_SINCOS_ROUND_INT8
#define EAH_HOTLOOP_VARIANT EAH_HOTLOOP_VARIANT_LAL
#define EAH_HOUGH_PREFETCH  EAH_HOUGH_PREFETCH_NONE
#define EAH_HOUGH_ASS       EAH_HOUGH_ASS_NONE

#elif EAH_OPTIIZATION == 2 /* AltiVec Code (currently not working) */
#define EAH_SINCOS_VARIANT  EAH_SINCOS_VARIANT_LINEAR
#define EAH_SINCOS_ROUND    EAH_SINCOS_ROUND_FLOOR
#define EAH_HOTLOOP_VARIANT EAH_HOTLOOP_VARIANT_LAL /* should be ALTIVEC, but doesn't work yet */
#define EAH_HOUGH_PREFETCH  EAH_HOUGH_PREFETCH_NONE /* should be somethig similar to ASS, but isn't there yet */
#define EAH_HOUGH_ASS       EAH_HOUGH_ASS_NONE

#elif EAH_OPTIIZATION == 3 /* SSE code, contains assembler */
#define EAH_SINCOS_VARIANT  EAH_SINCOS_VARIANT_LINEAR
#define EAH_SINCOS_ROUND    EAH_SINCOS_ROUND_INT8
#define EAH_HOTLOOP_VARIANT EAH_HOTLOOP_VARIANT_SSE
#define EAH_HOUGH_PREFETCH  EAH_HOUGH_PREFETCH_DIRECT
#define EAH_HOUGH_ASS       EAH_HOUGH_ASS_X87

#endif /* EAH_OPTIIZATION == */
#endif /* ifdef EAH_OPTIIZATION */

/* defaults - if they haven't been set special, set them to GENERIC */
#ifndef EAH_SINCOS_VARIANT
#define EAH_SINCOS_VARIANT  EAH_GENERIC
#endif
#ifndef EAH_SINCOS_ROUND
#define EAH_SINCOS_ROUND    EAH_GENERIC
#endif
#ifndef EAH_HOTLOOP_VARIANT
#define EAH_HOTLOOP_VARIANT EAH_GENERIC
#endif
#ifndef EAH_HOGH_PREFETCH
#define EAH_HOUGH_PREFETCH  EAH_GENERIC
#endif
#ifndef EAH_HOUGH_ASS
#define EAH_HOUGH_ASS       EAH_GENERIC
#endif
