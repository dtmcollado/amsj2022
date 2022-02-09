# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2012  Carlos Lamas Bruzzone
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def _upper_vat(self, cr, uid, ids, context=None):
        for partner in self.browse(cr, uid, ids, context=context):
            if partner.vat:
                vat_country = partner.vat[:2]
                if not vat_country.isupper():
                    return False
        return True


    def valid_ci_uy(self, ci):
        '''
        Valid Uruguayan CI number.
        '''
        # Only digits
        try:
            int(ci)
        except:
            return False

        ci = str(ci)
        ci = ci.rjust(8,"0")

        if ( len(ci) > 8 ):
            return False

        check_digit = 0
        base = "2987634"
        for i in range(0,7):
            check_digit += int(ci[i]) * int(base[i])

        check_digit %= 10
        check_digit  = 10 - check_digit
        if ( check_digit == 10 ):
            check_digit = 0

        if ( check_digit == int(ci[7]) ):
            return True
        else:
            return False


    def valid_vat_uy(self, vat):
        '''
        Valid Uruguayan VAT number (RUT).
        '''
        # Only digits
        try:
            int(vat)
        except:
            return False

        # Long enough
        if ( len(vat) != 12 ):
            return False

        # VAT[] * Base[]
        check_digit = 0
        base = "43298765432"
        for i in range(0,11):
            check_digit += int(vat[i]) * int(base[i])

        # Module 11
        check_digit %= 11
        check_digit  = 11 - check_digit

        # Mistakes ?
        if ( check_digit == 10 ):
            return False
        else:
            if ( check_digit == 11 ): check_digit = 0
            if ( check_digit != int(vat[11]) ):
                return False

        # We are here, so ...
        return True


    def check_vat_uy(self, vat):
        '''
        Check Uruguayan VAT number (RUT).
        '''
        # One or another ...
        return self.valid_vat_uy(vat) or self.valid_ci_uy(vat)


    _constraints = [(_upper_vat, "VAT country must be uppercase", ["vat"])]

res_partner()
