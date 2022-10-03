# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class StockDetailReport(models.Model):
    _name = "stock.detail.report"
    _description = "Stock Detail Report"
    _auto = False
    picking_partner_id=fields.Many2one('res.partner','Partner')
    ship_mark=fields.Char('P. Ship Mark')
    s_ship_mark=fields.Char('S. Ship Mark')
    picking_id=fields.Many2one('stock.picking','Transfer')
    picking_type_id=fields.Many2one('stock.picking.type','Operation Type')
    picking_origin=fields.Char('Source Document')
    dest_location_id=fields.Many2one('stock.location','Warehouse')
    date=fields.Datetime('Date')
    product_id=fields.Many2one('product.product','Product')
    article=fields.Char('Article')
    qty_done=fields.Float('CTN Qty')
    qty_per_ctn=fields.Float('Qty/CTN')
    total_qty=fields.Float('Total QTY')
    weight=fields.Float('Weight')
    cbm=fields.Float('CBM')
    product_uom_id=fields.Many2one('uom.uom','Unit of Measure')
    lot_id=fields.Many2one('stock.production.lot','Lot/Serial Number')
    qty_on_hand=fields.Float('Qty on Hand')
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT 
                row_number() OVER (PARTITION BY true) AS id,
                sml.picking_partner_id,
                sml.ship_mark,
                sml.s_ship_mark,
                sml.picking_id,
                sml.picking_type_id,
                sml.picking_origin,
                sml.dest_location_id,
                sml.picking_date as date,
                sml.product_id,
                sml.article,
                sml.qty_done,
                sml.qty_per_ctn,
                sml.total_qty,
                sml.weight,
                sml.cbm,
                sml.product_uom_id,
                sml.lot_id,
                (select sum(quantity) from stock_quant group by lot_id,product_id having lot_id=sml.lot_id and product_id=sml.product_id) qty_on_hand
            FROM 
                stock_move_line sml
            )''' % (self._table,)
            )