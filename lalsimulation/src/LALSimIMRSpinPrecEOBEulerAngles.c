#ifndef _LALSIMIMRSPINPRECEOBEULERANGLES_C
#define _LALSIMIMRSPINPRECEOBEULERANGLES_C

/**
 * Computes RHS of ODE for gamma. Eq. 10 of PRD 89, 084006 (2014)
 */
static double f_alphadotcosi( double x, void * inparams )
{
	PrecEulerAnglesIntegration* params = (PrecEulerAnglesIntegration*) inparams;

	REAL8 alphadot = gsl_spline_eval_deriv( params->alpha_spline, x, params->alpha_acc );
	REAL8 beta = gsl_spline_eval( params->beta_spline, x, params->beta_acc );

	return -1. * alphadot * cos(beta);

}
/**
 * Given the trajectory in an inertial frame, this computes Euler angles
 * of the roation from the inertial frame to the minimal-rotation frame
 * that co-precesses with LN(t) = rvec(t) x rdotvec(t)
 */
static int EulerAnglesI2P(REAL8Vector *Alpha, /**<< output: alpha Euler angle */
                 REAL8Vector *Beta, /**<< output: beta Euler angle */
                 REAL8Vector *Gamma, /**<< output: gamma Euler angle */
                 INT4 *phaseCounterA, /**<< output: counter for unwrapping of alpha */
                 INT4 *phaseCounterB, /**<< output: counter for unwrapping of beta */
                 const REAL8Vector tVec, /**<< time series */
                 const REAL8Vector posVecx, /**<< x time series */
                 const REAL8Vector posVecy, /**<< y time series */
                 const REAL8Vector posVecz, /**<< z time series */
                 const UINT4 retLenLow, /**<< Array length of the trajectory */
                 const REAL8 InitialAlpha, /**<< Initial alpha (used only if flag_highSR=1) */
                 const REAL8 InitialGamma, /**<< Initial gamma */
                 UINT4 flag_highSR /**<< Flag to indicate whether one is analyzing the high SR trajectory */) {
    UINT4 i = 0;
    REAL8Vector *LN_x = NULL, *LN_y = NULL, *LN_z = NULL;
    REAL8 tmpR[3], tmpRdot[3], magLN;
    REAL8 precEulerresult = 0, precEulererror = 0;
    gsl_integration_workspace * precEulerw = gsl_integration_workspace_alloc (1000);
    gsl_function precEulerF;
    PrecEulerAnglesIntegration precEulerparams;
    REAL8 inGamma = InitialGamma;

    LN_x = XLALCreateREAL8Vector( retLenLow );
    LN_y = XLALCreateREAL8Vector( retLenLow );
    LN_z = XLALCreateREAL8Vector( retLenLow );

    gsl_spline *x_spline = gsl_spline_alloc( gsl_interp_cspline, retLenLow );
    gsl_spline *y_spline = gsl_spline_alloc( gsl_interp_cspline, retLenLow );
    gsl_spline *z_spline = gsl_spline_alloc( gsl_interp_cspline, retLenLow );

    gsl_interp_accel *x_acc    = gsl_interp_accel_alloc();
    gsl_interp_accel *y_acc    = gsl_interp_accel_alloc();
    gsl_interp_accel *z_acc    = gsl_interp_accel_alloc();

    gsl_spline_init( x_spline, tVec.data, posVecx.data, retLenLow );
    gsl_spline_init( y_spline, tVec.data, posVecy.data, retLenLow );
    gsl_spline_init( z_spline, tVec.data, posVecz.data, retLenLow );

    for( i=0; i < retLenLow; i++ )
    {
        tmpR[0] = posVecx.data[i]; tmpR[1] = posVecy.data[i]; tmpR[2] = posVecz.data[i];
        tmpRdot[0] = gsl_spline_eval_deriv( x_spline, tVec.data[i], x_acc );
        tmpRdot[1] = gsl_spline_eval_deriv( y_spline, tVec.data[i], y_acc );
        tmpRdot[2] = gsl_spline_eval_deriv( z_spline, tVec.data[i], z_acc );

        LN_x->data[i] = tmpR[1] * tmpRdot[2] - tmpR[2] * tmpRdot[1];
        LN_y->data[i] = tmpR[2] * tmpRdot[0] - tmpR[0] * tmpRdot[2];
        LN_z->data[i] = tmpR[0] * tmpRdot[1] - tmpR[1] * tmpRdot[0];

        magLN = sqrt(LN_x->data[i] * LN_x->data[i] + LN_y->data[i] * LN_y->data[i]
                     + LN_z->data[i] * LN_z->data[i]);
        LN_x->data[i] /= magLN; LN_y->data[i] /= magLN; LN_z->data[i] /= magLN;

        /*  Eq. 19 of PRD 89, 084006 (2014) */
        /*  Also unwrap the two angles */
        if (fabs(LN_x->data[i]) <= 1.e-10 && fabs(LN_y->data[i]) <=1.e-10){
            Alpha->data[i] = 0.0;
            inGamma = 0.0;
        } else {
            Alpha->data[i] = atan2( LN_y->data[i], LN_x->data[i] )
                             +  *phaseCounterA * LAL_TWOPI;
            if (i==0 && flag_highSR != 1){
                inGamma = -Alpha->data[i];
            }
        }

        while( i>0 && Alpha->data[i] - Alpha->data[i-1] > 5. ) {
            *phaseCounterA = *phaseCounterA - 1;
            Alpha->data[i] -= LAL_TWOPI;
        }
        while( i && Alpha->data[i] - Alpha->data[i-1] < -5. ) {
            *phaseCounterA = *phaseCounterA + 1;
            Alpha->data[i] += LAL_TWOPI;
        }
        if (LN_z->data[i] >1.) {
            LN_z->data[i] = 1.;
        }
        if (LN_z->data[i] <-1.) {
            LN_z->data[i] = -1.;
        }
        if ( flag_highSR == 1) {
            Alpha->data[i] -= (Alpha->data[0] - InitialAlpha);
        }

        if (fabs(1.0 - LN_z->data[i]) < 1.e-12){
            REAL8 LN_xy;
            LN_xy = sqrt(LN_x->data[i]*LN_x->data[i] +
			 LN_y->data[i]*LN_y->data[i]);
            //LN_z->data[i] = sqrt(1.0 - LN_xy*LN_xy);
            Beta->data[i] = atan2(LN_xy, LN_z->data[i]);
            //printf("here   ");
        }else{
            Beta->data[i] = acos( LN_z->data[i] );
        }
        if( i>0 && Beta->data[i] > Beta->data[i-1] ) {
            *phaseCounterB = *phaseCounterB - 1;
        }
    }
    /* Integrate \dot{\alpha} \cos{\beta} to get the final Euler angle
     Eq. 20 of PRD 89, 084006 (2014) */
    gsl_spline_init( x_spline, tVec.data, Alpha->data, retLenLow );
    gsl_spline_init( y_spline, tVec.data, Beta->data, retLenLow );

    precEulerparams.alpha_spline = x_spline;
    precEulerparams.alpha_acc    = x_acc;
    precEulerparams.beta_spline  = y_spline;
    precEulerparams.beta_acc     = y_acc;

    precEulerF.function = &f_alphadotcosi;
    precEulerF.params   = &precEulerparams;

    for( i = 0; i < retLenLow; i++ )
    {
        //if( i==0 ) { Gamma->data[i] = InitialGamma; }
        if( i==0 ) { Gamma->data[i] = inGamma; }
        else
        {
            gsl_integration_qags (&precEulerF, tVec.data[i-1], tVec.data[i], 1e-9, 1e-9, 1000, precEulerw, &precEulerresult, &precEulererror);
            Gamma->data[i] = Gamma->data[i-1] + precEulerresult;
        }
    }
    gsl_integration_workspace_free( precEulerw );
    gsl_spline_free( x_spline );
    gsl_spline_free( y_spline );
    gsl_spline_free( z_spline );
    gsl_interp_accel_free( x_acc );
    gsl_interp_accel_free( y_acc );
    gsl_interp_accel_free( z_acc );
    XLALDestroyREAL8Vector( LN_x );
    XLALDestroyREAL8Vector( LN_y );
    XLALDestroyREAL8Vector( LN_z );
    return XLAL_SUCCESS;
}

/**
 * Given Euler angles to go from initial inertial frame to precessing frama
 * and the LNhat vector, this functions computes the Euler angles to
 * go from the precessing frame to the frame of the total angular
 * momentum
 */
static void EulerAnglesP2J(
                REAL8 *aP2J, /**<< alpha Euler angle from precessing to final-J frame */
                REAL8 *bP2J, /**<< beta Euler angle from precessing to final-J frame */
                REAL8 *gP2J, /**<< gamma Euler angle from precessing to final-J frame */
                const REAL8 aI2P, /**<< alpha Euler angle from inertial to precessing frame */
                const REAL8 bI2P, /**<< beta Euler angle from inertial to precessing frame */
                const REAL8 gI2P, /**<< gamma Euler angle from inertial to precessing frame */
                const REAL8 LNhx, /**<< x component of LNhat */
                const REAL8 LNhy, /**<< y component of LNhat */
                const REAL8 LNhz, /**<< z component of LNhat */
                const REAL8 JframeEx[], /**<< x-axis of the total-angular-momentum frame */
                const REAL8 JframeEy[], /**<< y-axis of the total-angular-momentum frame */
                const REAL8 JframeEz[] /**<< z-axis of the total-angular-momentum frame */
) {
    REAL8 LframeEx[3] = {0,0,0}, LframeEy[3] = {0,0,0}, LframeEz[3] = {0,0,0};
    LframeEx[0] =  cos(aI2P)*cos(bI2P)*cos(gI2P) - sin(aI2P)*sin(gI2P);
    LframeEx[1] =  sin(aI2P)*cos(bI2P)*cos(gI2P) + cos(aI2P)*sin(gI2P);
    LframeEx[2] = -sin(bI2P)*cos(gI2P);
    LframeEy[0] = -cos(aI2P)*cos(bI2P)*sin(gI2P) - sin(aI2P)*cos(gI2P);
    LframeEy[1] = -sin(aI2P)*cos(bI2P)*sin(gI2P) + cos(aI2P)*cos(gI2P);
    LframeEy[2] =  sin(bI2P)*sin(gI2P);
    LframeEz[0] =  LNhx;
    LframeEz[1] =  LNhy;
    LframeEz[2] =  LNhz;
    REAL8 normJ, normLz;
    normJ = JframeEz[0]*JframeEz[0]+JframeEz[1]*JframeEz[1]+JframeEz[2]*JframeEz[2];
    normLz = LframeEz[0]*LframeEz[0]+LframeEz[1]*LframeEz[1]+LframeEz[2]*LframeEz[2];
    *aP2J = atan2(JframeEz[0]*LframeEy[0]+JframeEz[1]*LframeEy[1]+JframeEz[2]*LframeEy[2],
                 JframeEz[0]*LframeEx[0]+JframeEz[1]*LframeEx[1]+JframeEz[2]*LframeEx[2]);
    REAL8 cosarg = JframeEz[0]*LframeEz[0]+JframeEz[1]*LframeEz[1]+JframeEz[2]*LframeEz[2];
    if ( cosarg >= 1.  && cosarg < 1. + 1.e-10 ) {
        cosarg = 1.;
    }
    if ( cosarg <= -1. && cosarg > -1. - 1.e-10 ) {
        cosarg = -1.;
    }
    *bP2J = acos( cosarg );
    if (*bP2J < 1.e-4){
        cosarg = (JframeEz[0]*LframeEz[0]+JframeEz[1]*LframeEz[1]+JframeEz[2]*LframeEz[2])/sqrt(normJ*normLz);
        if ( cosarg >= 1.  && cosarg < 1. + 1.e-10 ) {
            cosarg = 1.;
        }
        if ( cosarg <= -1. && cosarg > -1. - 1.e-10 ) {
            cosarg = -1.;
        }
        *bP2J = acos( cosarg );
    }
    *gP2J = atan2(  JframeEy[0]*LframeEz[0]+JframeEy[1]*LframeEz[1]+JframeEy[2]*LframeEz[2],
                 -(JframeEx[0]*LframeEz[0]+JframeEx[1]*LframeEz[1]+JframeEx[2]*LframeEz[2]));

    /* I2P Euler angles are stored only for debugging purposes */
    if ( fabs(*bP2J-LAL_PI) < 1.e-10){
        *gP2J = 0.0;
        *aP2J = atan2( JframeEx[1], JframeEx[0]);
    }

    if ( fabs(*bP2J) < 1.e-10){
        *gP2J = 0.0;
        *aP2J = atan2( JframeEx[1], JframeEx[0]);
    }
}

/// This function computes components of the spins in L-based frame close to the merger

static void ComputeSpinsInLframe(
        REAL8Vector* S1hatL,
        REAL8Vector* S2hatL,
        const REAL8 s1x,
        const REAL8 s1y,
        const REAL8 s1z,
        const REAL8 s2x,
        const REAL8 s2y,
        const REAL8 s2z,
        const REAL8 lhx,
        const REAL8 lhy,
        const REAL8 lhz)
{

    REAL8 Lmag = sqrt(lhx*lhx + lhy*lhy + lhz*lhz);
    REAL8 S1mag = sqrt(s1x*s1x + s1y*s1y + s1z*s1z);
    REAL8 S2mag = sqrt(s2x*s2x + s2y*s2y + s2z*s2z);

    REAL8 th = acos(lhz/Lmag);
    REAL8 ph = atan2(lhy, lhx);
    REAL8 th1 = 0.0;
    REAL8 ph1 = 0.0;
    if (S1mag>1e-8){
       th1=acos(s1z/S1mag);
       ph1= atan2(s1y, s1x);
    }
    REAL8 th2 = 0.0;
    REAL8 ph2 = 0.0;
    if (S2mag>1e-8){
       th2 = acos(s2z/S2mag);
       ph2 = atan2(s2y, s2x);
    }


    // I want to find components of S1, S2 in the frame where L is along z
    // (up to a overall rotation angle)

    //REAL8 ths1l = acos((lhx*s1x + lhy*s1y + lhz*s1z)/(S1mag*Lmag) );
    //REAL8 ths2l = acos((lhx*s1x + lhy*s1y + lhz*s1z)/(S1mag*Lmag) );

    // The easieast is to rotate to the frame
    // where L is along z: RY[-th].RZ[-ph]:

    S1hatL->data[0] = S1mag*(-cos(th1)*sin(th) + cos(th)*cos(ph - ph1)*sin(th1));
    S1hatL->data[1] = S1mag*(-sin(th1)*sin(ph - ph1));
    S1hatL->data[2] = S1mag*(cos(th)*cos(th1) + sin(th)*sin(th1)*cos(ph-ph1));
    // z -component should aagree with ths1l

    S2hatL->data[0] = S2mag*(-cos(th2)*sin(th) + cos(th)*cos(ph - ph2)*sin(th2));
    S2hatL->data[1] = S2mag*(-sin(th2)*sin(ph - ph2));
    S2hatL->data[2] = S2mag*(cos(th)*cos(th2) + sin(th)*sin(th2)*cos(ph-ph2));

}


static int EulerAnglesP2I(REAL8Vector* Alpha, /**<< output: alpha Euler angle */
                 REAL8Vector *Beta, /**<< output: beta Euler angle */
                 REAL8Vector *Gamma, /**<< output: gamma Euler angle */
				 REAL8TimeSeries* aI2P, /** low sample alpha I->P */
				 REAL8TimeSeries* bI2P, /** low sample beta I->P */
				 REAL8TimeSeries* gI2P, /** low sample gamma I->P */
				 REAL8Vector* timeLow,
				 REAL8TimeSeries* aI2Phi, /** high sample alpha I->P */
				 REAL8TimeSeries* bI2Phi, /** high sample beta I->P */
				 REAL8TimeSeries* gI2Phi, /** high sample gamma I->P */
				 REAL8Vector* timeHi,
				 REAL8Vector* timeFull)
 {
	unsigned int i;
	// First we need to resample the hisample data
	printf("length of aP2I is %d, length of time is %d \n", aI2P->data->length, timeLow->length);
	printf("length of aP2I is %d, length of time is %d \n", bI2P->data->length, timeLow->length);
	printf("length of aP2I is %d, length of time is %d \n", gI2P->data->length, timeLow->length);
	printf("length of aP2Ihi is %d, length of timeHi is %d \n", aI2Phi->data->length, timeHi->length);
	printf("length of aP2Ihi is %d, length of timeHi is %d \n", bI2Phi->data->length, timeHi->length);
	printf("length of aP2Ihi is %d, length of timeHi is %d \n", gI2Phi->data->length, timeHi->length);
	printf("length of timeFull is %d \n", timeFull->length);

	printf("End of timeLow is %f \n", timeLow->data[timeLow->length-1]);
	printf("Beginning  of timeHigh is %f \n", timeHi->data[0]);
	printf("End  of timeHigh is %f \n", timeHi->data[timeHi->length-1]);
	printf("End  of timeFull is %f \n", timeFull->data[timeFull->length-1]);



	//Alpha  = XLALCreateREAL8Vector( timeFull->length);
	//Beta  = XLALCreateREAL8Vector( timeFull->length);
	//Gamma  = XLALCreateREAL8Vector( timeFull->length);

	for (i=0; i<timeLow->length; i++){
		//Alpha->data[i] = -1.0*gI2P->data->data[i];
		//Beta->data[i] = -1.0*bI2P->data->data[i];
		//Gamma->data[i] = -1.0*aI2P->data->data[i];
		Alpha->data[i] = 1.0*gI2P->data->data[i];
		Beta->data[i] = -1.0*bI2P->data->data[i];
		Gamma->data[i] = 1.0*aI2P->data->data[i];
	}
    //for (i=0; i< timeLow->length; i++){
    //    printf("Check %d, %f, %f \n", i, Alpha->data[i], -gI2P->data->data[i]);
    //}


	 // Resample Hi sampling part of it
	int idX = i;
	printf("Check  timeFull is %f, %f \n", timeFull->data[idX-1], timeFull->data[idX]);

	for (i=idX; i<timeFull->length; i++){
		//Alpha->data[i] = -1.0*gI2P->data->data[idX-1];
		//Beta->data[i] = -1.0*bI2P->data->data[idX-1];
		//Gamma->data[i] = -1.0*aI2P->data->data[idX-1];
		Alpha->data[i] = 1.0*gI2P->data->data[idX-1];
		Beta->data[i] = -1.0*bI2P->data->data[idX-1];
		Gamma->data[i] = 1.0*aI2P->data->data[idX-1];
	}

	//int rlen = timeFull->length - timeLow->length;



	//gsl_spline    *spline = NULL;
	//gsl_interp_accel *acc = NULL;
	//spline = gsl_spline_alloc( gsl_interp_cspline, timeHi->length);
	//acc    = gsl_interp_accel_alloc();
	//gsl_spline_init( spline, timeHi->data, aP2Ihi->data->data, timeHi->length);

    //gsl_spline_free(spline);
    //gsl_interp_accel_free(acc);
	 // We need to extend it

	return XLAL_SUCCESS;
 }









#endif // _LALSIMIMRSPINPRECEOBEULERANGLES_C
