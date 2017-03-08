# Copyright (C) 2007-2014  Kipp Cannon
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


#
# =============================================================================
#
#                                   Preamble
#
# =============================================================================
#


import copy
import itertools
import math
import numpy
from scipy.stats import stats
import sys


import lal


from glue.ligolw import ligolw
from glue.ligolw import lsctables
from glue.ligolw import utils as ligolw_utils
from glue.ligolw.utils import process as ligolw_process
from glue.ligolw.utils import search_summary as ligolw_search_summary
from . import git_version
from pylal import rate
from pylal import snglcoinc


__author__ = "Kipp Cannon <kipp.cannon@ligo.org>"
__version__ = "git id %s" % git_version.id
__date__ = git_version.date


#
# =============================================================================
#
#                Excess Power Specific Parameter Distributions
#
# =============================================================================
#


def dt_binning(instrument1, instrument2):
	# FIXME:  hard-coded for directional search
	#dt = 0.02 + snglcoinc.light_travel_time(instrument1, instrument2)
	dt = 0.02
	return rate.NDBins((rate.ATanBins(-dt, +dt, 12001), rate.LinearBins(0.0, 2 * math.pi, 61)))


class BurcaCoincParamsDistributions(snglcoinc.CoincParamsDistributions):
	binnings = {
		"H1_H2_dband": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_L1_dband": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H2_L1_dband": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_V1_dband": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"L1_V1_dband": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_H2_ddur": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_L1_ddur": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H2_L1_ddur": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_V1_ddur": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"L1_V1_ddur": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_H2_df": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_L1_df": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H2_L1_df": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_V1_df": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"L1_V1_df": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_H2_dh": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_L1_dh": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H2_L1_dh": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_V1_dh": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"L1_V1_dh": rate.NDBins((rate.LinearBins(-2.0, +2.0, 12001), rate.LinearBins(0.0, 2 * math.pi, 61))),
		"H1_H2_dt": dt_binning("H1", "H2"),
		"H1_L1_dt": dt_binning("H1", "L1"),
		"H2_L1_dt": dt_binning("H2", "L1"),
		"H1_V1_dt": dt_binning("H1", "V1"),
		"L1_V1_dt": dt_binning("L1", "V1")
	}

	filters = {
		"H1_H2_dband": rate.gaussian_window(11, 5),
		"H1_L1_dband": rate.gaussian_window(11, 5),
		"H2_L1_dband": rate.gaussian_window(11, 5),
		"H1_V1_dband": rate.gaussian_window(11, 5),
		"L1_V1_dband": rate.gaussian_window(11, 5),
		"H1_H2_ddur": rate.gaussian_window(11, 5),
		"H1_L1_ddur": rate.gaussian_window(11, 5),
		"H2_L1_ddur": rate.gaussian_window(11, 5),
		"H1_V1_ddur": rate.gaussian_window(11, 5),
		"L1_V1_ddur": rate.gaussian_window(11, 5),
		"H1_H2_df": rate.gaussian_window(11, 5),
		"H1_L1_df": rate.gaussian_window(11, 5),
		"H2_L1_df": rate.gaussian_window(11, 5),
		"H1_V1_df": rate.gaussian_window(11, 5),
		"L1_V1_df": rate.gaussian_window(11, 5),
		"H1_H2_dh": rate.gaussian_window(11, 5),
		"H1_V1_df": rate.gaussian_window(11, 5),
		"L1_V1_df": rate.gaussian_window(11, 5),
		"H1_L1_dh": rate.gaussian_window(11, 5),
		"H2_L1_dh": rate.gaussian_window(11, 5),
		"H1_H2_dt": rate.gaussian_window(11, 5),
		"H1_L1_dt": rate.gaussian_window(11, 5),
		"H2_L1_dt": rate.gaussian_window(11, 5),
		"H1_V1_dh": rate.gaussian_window(11, 5),
		"L2_V1_dh": rate.gaussian_window(11, 5)
	}

	@classmethod
	def from_filenames(cls, filenames, name, verbose = False):
		"""
		Convenience function to deserialize
		CoincParamsDistributions objects from a collection of XML
		files and return their sum.  The return value is a
		two-element tuple.  The first element is the deserialized
		and summed CoincParamsDistributions object, the second is a
		segmentlistdict indicating the interval of time spanned by
		the out segments in the search_summary rows matching the
		process IDs that were attached to the
		CoincParamsDistributions objects in the XML.
		"""
		self = None
		for n, filename in enumerate(filenames, 1):
			if verbose:
				print >>sys.stderr, "%d/%d:" % (n, len(filenames)),
			xmldoc = ligolw_utils.load_filename(filename, verbose = verbose, contenthandler = cls.contenthandler)
			if self is None:
				self = cls.from_xml(xmldoc, name)
				seglists = lsctables.SearchSummaryTable.get_table(xmldoc).get_out_segmentlistdict(set([self.process_id])).coalesce()
			else:
				other = cls.from_xml(xmldoc, name)
				self += other
				seglists |= lsctables.SearchSummaryTable.get_table(xmldoc).get_out_segmentlistdict(set([other.process_id])).coalesce()
				del other
			xmldoc.unlink()
		return self, seglists


#
# All sky version
#


class EPAllSkyCoincParamsDistributions(BurcaCoincParamsDistributions):
	@staticmethod
	def coinc_params(events, offsetvector):
		#
		# check for coincs that have been vetoed entirely
		#

		if len(events) < 2:
			return None

		params = {}

		# the "time" is the ms_snr squared weighted average of the
		# peak times neglecting light-travel times.  because
		# LIGOTimeGPS objects have overflow problems in this sort
		# of a calculation, the first event's peak time is used as
		# an epoch and the calculations are done w.r.t. that time.

		# FIXME: this time is available as the peak_time in the
		# multi_burst table, and it should be retrieved from that
		# table instead of being recomputed
		events = tuple(events)
		t = events[0].peak
		t += sum(float(event.peak - t) * event.ms_snr**2.0 for event in events) / sum(event.ms_snr**2.0 for event in events)
		gmst = lal.GreenwichMeanSiderealTime(t) % (2 * math.pi)

		for event1, event2 in itertools.combinations(sorted(events, key = lambda x: x.ifo), 2):
			if event1.ifo == event2.ifo:
				# a coincidence is parameterized only by
				# inter-instrument deltas
				continue

			prefix = "%s_%s_" % (event1.ifo, event2.ifo)

			# in each of the following, if the list of events contains
			# more than one event from a given instrument, the smallest
			# deltas are recorded

			dt = float(event1.peak + offsetvector[event1.ifo] - event2.peak - offsetvector[event2.ifo])
			name = "%sdt" % prefix
			if name not in params or abs(params[name][0]) > abs(dt):
				#params[name] = (dt,)
				params[name] = (dt, gmst)

			df = (event1.peak_frequency - event2.peak_frequency) / ((event1.peak_frequency + event2.peak_frequency) / 2)
			name = "%sdf" % prefix
			if name not in params or abs(params[name][0]) > abs(df):
				#params[name] = (df,)
				params[name] = (df, gmst)

			dh = (event1.ms_hrss - event2.ms_hrss) / ((event1.ms_hrss + event2.ms_hrss) / 2)
			name = "%sdh" % prefix
			if name not in params or abs(params[name][0]) > abs(dh):
				#params[name] = (dh,)
				params[name] = (dh, gmst)

			dband = (event1.ms_bandwidth - event2.ms_bandwidth) / ((event1.ms_bandwidth + event2.ms_bandwidth) / 2)
			name = "%sdband" % prefix
			if name not in params or abs(params[name][0]) > abs(dband):
				#params[name] = (dband,)
				params[name] = (dband, gmst)

			ddur = (event1.ms_duration - event2.ms_duration) / ((event1.ms_duration + event2.ms_duration) / 2)
			name = "%sddur" % prefix
			if name not in params or abs(params[name][0]) > abs(ddur):
				#params[name] = (ddur,)
				params[name] = (ddur, gmst)

		return params


#
# Galactic core coinc params
#


def delay_and_amplitude_correct(event, ra, dec):
	# retrieve station metadata

	detector = lal.cached_detector_by_prefix[event.ifo]

	# delay-correct the event to the geocentre

	delay = lal.TimeDelayFromEarthCenter(detector.location, ra, dec, event.peak)
	event.peak -= delay
	event.period = event.period.shift(-delay)
	try:
		event.ms_peak -= delay
	except AttributeError:
		pass
	try:
		event.ms_period = event.ms_period.shift(-delay)
	except AttributeError:
		pass

	# amplitude-correct the event using the polarization-averaged
	# antenna response

	fp, fc = lal.ComputeDetAMResponse(detector.response, ra, dec, 0, lal.GreenwichMeanSiderealTime(event.peak))
	mean_response = math.sqrt(fp**2 + fc**2)
	event.amplitude /= mean_response
	event.ms_hrss /= mean_response

	# done

	return event


class EPGalacticCoreCoincParamsDistributions(BurcaCoincParamsDistributions):
	@staticmethod
	def coinc_params(events, offsetvector, ra, dec):
		return EPAllSkyCoincParamsDistributions.coinc_params([delay_and_amplitude_correct(copy.copy(event), ra, dec) for event in events], offsetvector)


#
# =============================================================================
#
#                                     I/O
#
# =============================================================================
#


process_program_name = "lalapps_burca_tailor"


def gen_likelihood_control(coinc_params_distributions, seglists, name = u"lalapps_burca_tailor", comment = u""):
	xmldoc = ligolw.Document()
	node = xmldoc.appendChild(ligolw.LIGO_LW())

	process = ligolw_process.register_to_xmldoc(xmldoc, program = process_program_name, paramdict = {}, version = __version__, cvs_repository = "lscsoft", cvs_entry_time = __date__, comment = comment)
	coinc_params_distributions.process_id = process.process_id
	ligolw_search_summary.append_search_summary(xmldoc, process, ifos = seglists.keys(), inseg = seglists.extent_all(), outseg = seglists.extent_all())

	node.appendChild(coinc_params_distributions.to_xml(name))

	ligolw_process.set_process_end_time(process)

	return xmldoc
