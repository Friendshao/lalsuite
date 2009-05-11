/*
*  Copyright (C) 2007 Jolien Creighton
*  Copyright (C) 2009 Oliver Bock
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

/**
 * \defgroup XML
 * \ingroup support
 * \author Oliver Bock, Reinhard Prix, Jolien Creighton
 * \brief Module for reading/writing/manipulating XML as well as data serialization.
 */

/**
 * \file
 * \ingroup XML
 * \brief Header file declaring the public XML API
 */

#include <libxml/tree.h>


int XLALXMLFilePrintElements(const char *fname);
xmlChar * XLALGetSingleNodeContentByXPath(const xmlDocPtr xmlDoc, const char *xpath);
