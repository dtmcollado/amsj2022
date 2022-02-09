# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import models, fields, api, exceptions, _


class StockProductioLot(models.Model):
    _inherit = 'stock.production.lot'
    _order = "life_date"
    # desc

    # @api.one
    # @api.constrains('removal_date', 'alert_date', 'life_date', 'use_date')
    # def _check_dates(self):
    #     dates = filter(lambda x: x, [self.alert_date, self.removal_date,
    #                                  self.use_date, self.life_date])
    #     sort_dates = list(dates)
    #     sort_dates.sort()
    #     if dates != sort_dates:
    #         raise exceptions.Warning(
    #             _('Dates must be: Alert Date < Removal Date < Best Before '
    #               'Date < Expiry Date'))


    @api.model
    def create(self, values):
        if 'life_date' in values:
            values['removal_date'] = values['life_date']

        return super(StockProductioLot, self).create(values)

    @api.one
    def write(self, values):
        if 'life_date' in values:
            values['removal_date'] = values['life_date']

        return super(StockProductioLot, self).write(values)

    @api.one
    @api.depends('removal_date', 'alert_date', 'life_date', 'use_date')
    def _get_product_state(self):
        now = fields.Datetime.now()
        self.expiry_state = 'normal'
        if self.life_date and self.life_date < now:
            self.expiry_state = 'expired'
        elif (self.alert_date and self.removal_date and
                self.removal_date >= now > self.alert_date):
            self.expiry_state = 'alert'
        elif (self.removal_date and self.use_date and
                self.use_date >= now > self.removal_date):
            self.expiry_state = 'to_remove'
        elif (self.use_date and self.life_date and
                self.life_date >= now > self.use_date):
            self.expiry_state = 'best_before'

    @api.one
    @api.depends('quant_ids')
    def get_stock_total(self):
        cantidad=0
        for quant in self.quant_ids:
            cantidad=cantidad+quant.qty
        self.stock_total=cantidad


    expiry_state = fields.Selection(
        compute=_get_product_state,
        selection=[('expired', 'Expirado'),
                   ('alert', 'En alerta'),
                   ('normal', 'Normal'),
                   ('to_remove', 'A remover'),
                   ('best_before', 'Para utilizar')],
        string=u'Estado de expiración',store=True)


    stock_total = fields.Float(string='Stock total',compute=get_stock_total)


class StockQuant(models.Model):

    _inherit = "stock.quant"

    expiry_state = fields.Selection(string=u'Estado de expiración',
                                    related="lot_id.expiry_state")

    fecha_ven = fields.Datetime(string=u'Vencimiento',
                                         related="lot_id.life_date")
