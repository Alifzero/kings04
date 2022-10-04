# -*- coding: utf-8 -*-

from odoo import models, fields, api


# class stockPickingButton(models.Model):
#     _inherit = 'stock.picking'
#
#     def changeStage(self):
#         self.state = 'draft'




class StockTransferPicking(models.Model):
    _inherit = 'stock.move'

    done_qty_sm = fields.Float(string='Done', required=True)
    lot_name_sm = fields.Char(string='Lot no', required=True)

    def qty_Done(self):
        for rec in self:
            if rec.done_qty_sm:
                record = rec.env['stock.move.line'].browse([])

                if rec.quantity_done == 0:
                    rec.env['stock.move.line'].create({
                        'move_id': rec.id,
                        'lot_name': rec.lot_name_sm,
                        'qty_done': rec.done_qty_sm,
                        'product_id': rec.product_id.id,
                        'product_uom_id': rec.product_uom.id,
                        'location_id': rec.location_id.id,
                        'location_dest_id': rec.location_dest_id.id,
                    })
                    rec.product_uom_qty = rec.done_qty_sm
                    rec.quantity_done = rec.done_qty_sm

                else:

                    rec.env['stock.move.line'].write({
                    'move_id': rec.id,
                    'lot_name': rec.lot_name_sm,
                    'qty_done': rec.done_qty_sm,
                    'product_id': rec.product_id.id,
                    'product_uom_id': rec.product_uom.id,
                    'location_id': rec.location_id.id,
                    'location_dest_id': rec.location_dest_id.id,
                })
                    rec.product_uom_qty = rec.done_qty_sm
                    rec.quantity_done = rec.done_qty_sm
