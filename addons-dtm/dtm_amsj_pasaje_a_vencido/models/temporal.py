
class dtm_amsj_pasaje_a_vendido(models.Model):
    _inherit = 'stock.picking'

    def cron_pasaje_a_vencido(self, cr, uid, context=None):
        quants=[]
        fecha_hoy = datetime.today()
        sql = """
        SELECT quant.id,quant.location_id, location.id, product.id, product_tmpl.uom_id, lot.id, quant.qty
        FROM stock_quant quant, stock_location location, 
        product_supplierinfo product_supplier, product_product product, 
        product_template product_tmpl, stock_production_lot lot 
        WHERE 
           quant.product_id = product.id and
           product_tmpl.id = product.product_tmpl_id and
           quant.lot_id = lot.id and quant.location_id = 476 and 
           product_supplier.name = location.laboratorio_id and
           product_tmpl.id = product_supplier.product_tmpl_id and
           lot.product_id = product.id and
           reservation_id IS NULL and
           location.laboratorio_id is not null and
           quant.lot_id is not null and quant.qty > 0 and 
           product_tmpl.categoria_id = 17 and (quant.sent = False or quant.sent isnull) and lot.alert_date <= %s
        """
        cr.execute(sql,(fecha_hoy,))
        resultado = cr.fetchall()
        for res in resultado:
            quant_id = res[0]
            quant_location_id = res[1]
            location_id = res[2]
            product_id = res[3]
            uom_id = res[4]
            lot_id = res[5]
            qty = res[6]
            quants.append(quant_id)
            location = self.pool.get('stock.location').browse(cr,uid,location_id)
            self.pool.get('stock.quant').write(cr,uid,[quant_id],{'sent':'True'})
            picking_out_id = self.pool.get('stock.picking').create(cr, uid, {
                        "location_id": quant_location_id,
                        'location_dest_id': location_id,
                        'picking_type_id': location.almacen_id.int_type_id.id,
                        'state': 'draft',
                        'sector_id': 17,
                        'origin': 'Creacion automatica de transferencia productos por vencer o vencidos'
                         })
            self.pool.get('stock.move').create(cr, SUPERUSER_ID, {
                         'name': 'Creacion automatica de transferencia productos por vencer o vencidos',
                        'product_id': product_id,
                        'product_uom_qty': qty,
                        'product_uom': uom_id,
                        'picking_id': picking_out_id,
                        'picking_type_id': location.almacen_id.int_type_id.id,
                         'lote': lot_id,
                        'location_dest_id': location.id,
                        'location_id': quant_location_id,
                        'state': "confirmed",
                        })
            picking_out = self.pool.get('stock.picking').browse(cr, SUPERUSER_ID, picking_out_id)
            if picking_out.state == 'draft':
                picking_out.sudo().action_confirm()
            if picking_out.state == 'confirmed':
                picking_out.sudo().action_assign()
                picking_out.do_enter_transfer_details()

        if quants:
            users_to_send = 'ccollado@datamatic.com.uy'
            odoobot = "odoo@amsj.com.uy"
            message_body = '<br/>'
            message_body += 'Listado de transferencia automatica de productos por vencer o vencidos:'
            message_body += '<br/>'
            for quant in self.pool.get('stock.quant').browse(cr,uid,quants):
                fecha_ven = str(quant.fecha_ven) or 'No ingresada'
                fecha_alerta = quant.lot_id.alert_date or 'No ingresada'
                message_body += '<br/>'
                message_body += '<b>Nombre producto: </b>' + quant.product_id.name +' <b>Cantidad: </b>' + str(quant.qty) + ' <b>Fecha vencimiento: </b>' + fecha_ven + ' <b>Fecha de alerta: </b>' + fecha_alerta + ' <b>Lote: </b>' + quant.lot_id.name
                message_body += '<br/>'
            mail = self.pool.get('mail.mail')
            today = datetime.now().strftime('%d/%m/%Y')
            mail_data = {'subject': 'Listado de transferencia automatica de productos por vencer o vencidos ' + str(today),
                            'email_from': odoobot,
                            'email_to': users_to_send,
                            'body_html': message_body}
            mail_out = mail.create(cr,SUPERUSER_ID,mail_data)
            if mail_out:
                mail.send(cr, SUPERUSER_ID, [mail_out])
        else:
            users_to_send = 'ccollado@datamatic.com.uy'
            odoobot = "odoo@amsj.com.uy"
            message_body = '<br/>'
            message_body += 'No se encontraron productos por vencer o vencidos:'
            message_body += '<br/>'
            mail = self.pool.get('mail.mail')
            today = datetime.now().strftime('%d/%m/%Y')
            mail_data = {
                'subject': 'Listado de transferencia automatica de productos por vencer o vencidos ' + str(today),
                'email_from': odoobot,
                'email_to': users_to_send,
                'body_html': message_body}
            mail_out = mail.create(cr, SUPERUSER_ID, mail_data)
            if mail_out:
                mail.send(cr, SUPERUSER_ID, [mail_out])
