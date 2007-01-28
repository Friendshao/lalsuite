/******** <lalVerbatim file="ComputeExcessPowerCV"> ********
Author: Flanagan, E. and Cannon, K.
$Id$
********* </lalVerbatim> ********/

#include <math.h>
#include <lal/LALRCSID.h>

NRCSID (COMPUTEEXCESSPOWERC, "$Id$");

#include <lal/ExcessPower.h>
#include <lal/Sequence.h>
#include <lal/Thresholds.h>
#include <lal/XLALError.h>


static REAL8 real8_sumwithfac (
	const REAL4 *data,
	const REAL8 *fac,
	size_t first,
	size_t count
)
{
	REAL8 sum = 0;

	for(data += first, fac += first; count-- > 0; data++, fac++) {
		sum += *data * *fac;
	}

	return(sum);
}


/******** <lalVerbatim file="ComputeExcessPowerCP"> ********/
int
XLALComputeExcessPower(
	TFTiling *tiling,
	const REAL4TimeFrequencyPlane *plane,
	const REAL8 *hrssfactor,
	const REAL4 *norm
)
/******** </lalVerbatim> ********/
{
	static const char func[] = "XLALComputeExcessPower";
	TFTile *tile = tiling->tile;
	REAL8 sum;
	REAL8 hrsssq;
	REAL8 dof;
	INT4 bin;
	INT4 binstep;
	INT4 nf = plane->freqBins;
	INT4 nt = plane->timeBins;
	size_t i;

	/* check on some parameter values */
	if((nf <= 0) || (nt <= 0))
		XLAL_ERROR(func, XLAL_EDOM);

	for(i = 0; i < tiling->numtiles; i++, tile++) {
		if((tile->tstart < 0) || (tile->tstart + tile->tbins > nt) ||
		   (tile->fstart < 0) || (tile->fstart + tile->fbins > nf))
			XLAL_ERROR(func, XLAL_EDATA);

		dof = XLALTFTileDegreesOfFreedom(tile);

		binstep = tile->tbins / dof;
		sum = 0.0;
		hrsssq = 0.0;
		for(bin = 0; bin < tile->tbins; bin += binstep) {
			sum += pow(XLALREAL4Sum(&plane->data[(tile->tstart + bin) * nf], tile->fstart, tile->fbins), 2.0);
			hrsssq += pow(real8_sumwithfac(&plane->data[(tile->tstart + bin) * nf], hrssfactor, tile->fstart, tile->fbins), 2.0);
		}
		sum /= XLALREAL4SumSquares(norm, tile->fstart, tile->fbins);
		tile->excessPower = sum - dof;
		tile->hrss = sqrt(hrsssq * binstep * plane->deltaT);
		tile->lnalpha = XLALlnOneMinusChisqCdf(sum, dof);
		if(XLALIsREAL8FailNaN(tile->lnalpha))
			XLAL_ERROR(func, XLAL_EFUNC);
	}

	/* success */
	return 0;
}


/******** <lalVerbatim file="ComputeLikelihoodCP"> ********/
REAL8
XLALComputeLikelihood(
	TFTiling *tiling
)
/******** </lalVerbatim> ********/
{
	REAL8 avglambda = 0.0;
	REAL8 rho4;
	TFTile *tile;
	size_t i;

	for(i = 0, tile = tiling->tile; i < tiling->numtiles; i++, tile++) {
		rho4 = tile->excessPower * tile->excessPower;
		avglambda += XLALTFTileDegreesOfFreedom(tile) / rho4 * exp(tile->lnweight - tile->lnalpha);
	}

	/* compute the likelihood averaged over TF tiles */
	avglambda /= tiling->numtiles;

	/* return value of statistic */
	return(avglambda);
}
