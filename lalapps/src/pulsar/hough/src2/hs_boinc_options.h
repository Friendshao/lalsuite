/*
*  Copyright (C) 2007 Bernd Machenschalk
*
*  This program is free software; you can redistribute it and/or modify
*  it under the terms of the GNU General Public License as published by
*  the Free Software Foundation; either version 2 of the License, or
*  (at your option) any later version.
*
*  This program is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*  GNU General Public License for more details.
*
*  You should have received a copy of the GNU General Public License
*  along with with program; see the file COPYING. If not, write to the
*  Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
*  MA  02111-1307  USA
*/

/* C++ -> C interface for BOINC_OPTION handling etc.
*/

#include "boinc_api.h"
#if (BOINC_GRAPHICS > 0)
#include "graphics_api.h"
#endif

#define HS_BOINC_OPTIONS_H_RCSID "$Id$"

struct HS_SHMEM {
  char user_name[64];
  char team_name[64];
  char  app_name[64];
  char   wu_name[64];
  char boincdir[128];
  double skypos_rac;
  double skypos_dec;
  double user_credit;
  double ravg_credit;
  double host_credit;
  double update_time;
  double fraction_done;
  double cpu_time;
  BOINC_STATUS status;
};

#ifdef __cplusplus
extern "C" {
#endif
  
extern double boincv6_skypos_rac;
extern double boincv6_skypos_dec;
extern double boincv6_fraction_done;

#if (BOINC_GRAPHICS > 0)
extern int boinc_init_graphics_options(WORKER_FUNC_PTR);
#endif

#ifdef BOINC_APIV6
extern int setup_shmem(void);
#endif

extern void set_boinc_options(void);

#ifdef __cplusplus
}
#endif
