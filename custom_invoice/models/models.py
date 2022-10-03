# -*- coding: utf-8 -*-

from odoo import models, fields, api


# class stockPickingButton(models.Model):
#     _inherit = 'stock.picking'
#
#     def QtyDoneCustom(self):
#         obj = self.env['stock.move']
#         obj.quantity_done = obj.done_qty_sm
#         print('end')

class StockTransferPicking(models.Model):
    _inherit = 'stock.move'

    # stock_move_id = fields.Many2one('stock.move.line')
    # done_qty_stock_move = fields.Float(related='stock_move_id.qty_done')
    # quantity_done = fields.Float('Quantity Done', compute='_quantity_done_compute', digits='Product Unit of Measure', inverse='_quantity_done_set')

    done_qty_sm = fields.Float(string='Done')
    lot_name_sm = fields.Char(string='Lot no')
    quantity_done = fields.Float(compute='qty_Done')

    def qty_Done(self):
      

        for rec in self:
            rec.product_uom_qty = rec.done_qty_sm
            rec.quantity_done = rec.done_qty_sm
            if rec.quantity_done:
                rec.env['stock.move.line'].create({
                'move_id': rec.id,
                'lot_name': rec.lot_name_sm,
                'qty_done': rec.done_qty_sm,
                'product_id': rec.product_id.id,
                'product_uom_id': rec.product_uom.id,
                'location_id': rec.location_id.id,
                'location_dest_id': rec.location_dest_id.id,
            })

    @api.onchange('lot_name_sm', 'done_qty_sm')
    def _onchange_done_qty(self):

        if self.done_qty_sm:
            self.env['stock.move.line'].create({
                'move_id': self.id,
                'lot_name': self.lot_name_sm,
                'qty_done': self.done_qty_sm,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })

    # def QtyDoneCustom(self):
    #     print("start")
    #     self.quantity_done = self.done_qty_sm
    #     print('end')

    # for move_line in self.move_line_nosuggest_ids:
    #
    #     move_line.qty_done
    #     move_line.lot_name

    # self.done_qty_sm = move_line.qty_done
    # self.lot_name_sm =  move_line.lot_name
