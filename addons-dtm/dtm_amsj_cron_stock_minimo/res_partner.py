# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) BrowseInfo (http://browseinfo.in)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv
from openerp.osv import fields
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from openerp import http


class res_partner(osv.osv):
    _inherit = "res.partner"

    def _cron_reminder(self, cr, uid, context=None):
        su_id = self.pool.get('res.partner').browse(cr, uid, SUPERUSER_ID)
        partner_ids = self.search(cr, uid, (), context=None)
        for partner in self.browse(cr, uid, partner_ids, context=None):
            bdate = datetime.strptime(partner.birthdate, '%Y-%m-%d').date()
            today = datetime.now().date()
            if bdate != today:
                if bdate.month == today.month:
                    if bdate.day == today.day:
                        if partner:
                            template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid,
                                                                                              'birthday_reminder',
                                                                                              'email_template_reminder')[
                                1]
                            email_template_obj = self.pool.get('email.template')
                            if template_id:
                                values = email_template_obj.generate_email(cr, uid, template_id, partner.id,
                                                                           context=context)
                                values['email_from'] = su_id.email
                                values['email_to'] = partner.email
                                values['res_id'] = False
                                mail_mail_obj = self.pool.get('mail.mail')
                                msg_id = mail_mail_obj.create(cr, SUPERUSER_ID, values)
                                if msg_id:
                                    mail_mail_obj.send(cr, SUPERUSER_ID, [msg_id])

        return True
