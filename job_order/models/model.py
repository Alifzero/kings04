# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import except_orm, ValidationError
import logging
from datetime import datetime
import math
import _sqlite3
from gevent.libev.corecext import NONE
_logger = logging.getLogger(__name__)

class JobOrder(models.Model):
    _name='job.order'
    _rec_name='container_no'
    cmb=fields.Float(string='Total CBM')
    total_cmb=fields.Float(string='Total CBM',compute='_cal_cbm')
    state=fields.Selection([('Draft','Draft'),('Confirmed','Confirmed'),('Invoiced','Invoiced'),('Receipt','Receipt')],default='Draft')
    line_ids=fields.One2many('job.order.line','order_id')
    container_no=fields.Char(string='Container Number')
    total_no_ctn=fields.Float('Total CTN Quantity',compute='_cal_total_no_ctn')
    total_ctn=fields.Float('Total CTN Quantity')
    total_weight=fields.Float('Total Weight',compute='_cal_total_weight')
    shipment_no=fields.Char('Shipment No.')
    type=fields.Selection([('Job Order','Job Order'),('Packing List','Packing List')],'Type')
    
    
#     @api.constrains('cmb', 'total_cmb')
#     def check_total_cbm(self):
#         for each in self:
#             if each.total_cmb and each.cmb:
#                 if each.total_cmb > each.cmb:
#                     raise ValidationError('You are exceeding total limit of container. Kindly remove extra products.')
    
#     @api.constrains('total_no_ctn', 'total_ctn')
#     def check_total_ctn(self):
#         for each in self:
#             if each.total_no_ctn and each.total_ctn:
#                 if each.total_no_ctn > each.total_ctn:
#                     raise ValidationError('You are exceeding total limit of container. Kindly remove extra products.')

    def SetToDraft(self):
        for line in self.env['account.move'].search([('order_id','=',self.id)]):
            line.unlink()
        self.state='Draft'
    @api.depends('line_ids')
    def _cal_cbm(self):
        for rec in self:
            total=0
            for line in rec.line_ids:
                total+=line.cbm
            rec.total_cmb=total

    @api.depends('line_ids')
    def _cal_total_weight(self):
        for rec in self:
            total=0
            rec.total_weight=0
            for line in rec.line_ids:
                for each in line.detail_ids:
                    total+=each.weight
            rec.total_weight=total
    @api.depends('line_ids')
    def _cal_total_no_ctn(self):
        for rec in self:
            total=0
            rec.total_no_ctn=0
            for line in rec.line_ids:
                total+=line.no_of_ctn
            rec.total_no_ctn=total

    def Confirmed(self):
        total=0
        if not self.line_ids:
            raise ValidationError('At least one order line required')

        for line in self.line_ids:
            total+=line.cbm
#         if total>self.cmb:
#             raise ValidationError('CBM limit Exceeds')
        self.state='Confirmed'

    def CreateInv(self):
        self.state='Invoiced'
        
        for line in self.line_ids:
            
            move_lines = [(5,0,0)]
            for detail_line in line.detail_ids:
                product_obj=self.env['product.product'].search([('product_tmpl_id','=',detail_line.product_id.id)],limit=1)
                line_vals_debit={'product_id': product_obj.id,
                                  'name': product_obj.name,
                                  'account_id': product_obj.property_account_income_id.id,
                                  'debit': detail_line.sub_total,
                                  'exclude_from_invoice_tab': True,
                                  'article': detail_line.article,
                                  'quantity': detail_line.no_of_ctn,
                                  'qty_per_ctn': detail_line.qty_per_ctn,
                                  'cbm': detail_line.cbm,
                                  'weight': detail_line.weight,
                                  'price_based': detail_line.price_based,
                                  'detail_id':detail_line.id,
                                  'product_uom_id': detail_line.uom_id.id,
#                                   'price_unit': detail_line.price,
                                  'price_subtotal':detail_line.sub_total
                                  }
                move_lines.append((0,0,line_vals_debit))
                line_vals_credit={'product_id': product_obj.id,
                                  'name': product_obj.name,
                                  'account_id': product_obj.property_account_expense_id.id,
                                  'credit': detail_line.sub_total,
                                  'exclude_from_invoice_tab': False,
                                  'article': detail_line.article,
                                  'quantity': detail_line.no_of_ctn,
                                  'qty_per_ctn': detail_line.qty_per_ctn,
                                  'cbm': detail_line.cbm,
                                  'weight': detail_line.weight,
                                  'price_based': detail_line.price_based,
                                  'detail_id':detail_line.id,
                                  'product_uom_id': detail_line.uom_id.id,
#                                   'price_unit': detail_line.price,
                                  'price_subtotal':detail_line.sub_total
                                  }
                move_lines.append((0,0,line_vals_credit))
            invoice_new = self.env['account.move'].create({'partner_id': line.partner_id.id,
                                                           'invoice_date': datetime.now(),
                                                           'move_type': 'out_invoice',
                                                           'invoice_origin': 'Job Order of '+str(self.container_no),
                                                           'order_id': self.id,
                                                           'container_no':self.container_no,
                                                           'line_ids':move_lines
                                                           })
#                 inv_line = self.env['account.move.line'].create([{'move_id': invoice_new.id, 'product_id': product_obj.id,
#                                                                   'name': product_obj.name,
#                                                                   'account_id': product_obj.property_account_income_id.id,
#                                                                   'debit': detail_line.sub_total,
#                                                                   'exclude_from_invoice_tab': True,
#                                                                   'article': detail_line.article,
#                                                                   'quantity': detail_line.no_of_ctn,
#                                                                   'qty_per_ctn': detail_line.qty_per_ctn,
#                                                                   'cbm': detail_line.cbm,
#                                                                   'weight': detail_line.weight,
#                                                                   'price_based': detail_line.price_based,
#                                                                   'detail_id':detail_line.id,
#                                                                   'product_uom_id': detail_line.uom_id.id,
#                                                                   'price_unit': detail_line.price,
#                                                                   'price_subtotal':detail_line.sub_total
#                                                                   },
#                                                                  {'move_id': invoice_new.id, 'product_id': product_obj.id,
#                                                                   'name': product_obj.name,
#                                                                   'account_id': product_obj.property_account_expense_id.id,
#                                                                   'credit': detail_line.sub_total,
#                                                                   'exclude_from_invoice_tab': False,
#                                                                   'article': detail_line.article,
#                                                                   'quantity': detail_line.no_of_ctn,
#                                                                   'qty_per_ctn': detail_line.qty_per_ctn,
#                                                                   'cbm': detail_line.cbm,
#                                                                   'weight': detail_line.weight,
#                                                                   'price_based': detail_line.price_based,
#                                                                   'detail_id':detail_line.id,
#                                                                   'product_uom_id': detail_line.uom_id.id,
#                                                                   'price_unit': detail_line.price,
#                                                                   'price_subtotal':detail_line.sub_total
#                                                                   }]
#                                                                 )
#                 move_lines.append((0,0,line_vals_credit))


class JobOrderLines(models.Model):
    _name = 'job.order.line'

    order_id=fields.Many2one('job.order')
    partner_id=fields.Many2one('res.partner')
    mark=fields.Char(related='partner_id.ref',string='P. Ship Mark')
    s_ship_mark=fields.Char(related='partner_id.s_ship_mark',string='S. Ship Mark',store=True)
    no_of_ctn=fields.Float(string='Total CTN',compute='cal_total_no_of_qty')
    total_qty=fields.Float(string='Total QTY/CTN',compute='_cal_qty')
    total_weight=fields.Float(string='Total Weight',compute='_cal_weight')
    cbm=fields.Float(string='Total CBM',compute='_cal_total_cbm')
    detail_ids=fields.One2many('job.order.line.detail','line_id')
    description=fields.Char(string='Description')
    type=fields.Selection([('Job Order','Job Order'),('Packing List','Packing List')],'Type',related='order_id.type')
    @api.depends('detail_ids')
    def cal_total_no_of_qty(self):
        for each in self:
            total=0
            for line in each.detail_ids:
                total+=line.no_of_ctn
            each.no_of_ctn=total

    @api.depends('detail_ids')
    def _cal_total_cbm(self):
        for each in self:
            total=0
            for line in each.detail_ids:
                total+=line.cbm
            each.cbm=total

    @api.depends('detail_ids')
    def _cal_qty(self):
        for each in self:
            total=0
            for line in each.detail_ids:
                total+=line.qty_per_ctn
            each.total_qty=total
    
    @api.depends('detail_ids')
    def _cal_weight(self):
        for each in self:
            total=0
            for line in each.detail_ids:
                total+=line.weight
            each.total_weight=total

class JobOrderLinesDetails(models.Model):
    _name = 'job.order.line.detail'
    
    partner_id=fields.Many2one('res.partner','Partner',related='line_id.partner_id',store=True)
    ship_mark=fields.Char('P. Ship Mark',related='line_id.partner_id.ref',store=True)
    s_ship_mark=fields.Char(related='partner_id.s_ship_mark',string='S. Ship Mark',store=True)
    product_ids=fields.Many2many('product.template','Products',compute='_cal_valid_products')
    product_id=fields.Many2one('product.template',required=1,domain="[('id','in',product_ids)]")
    lot_id=fields.Many2one('stock.production.lot','Lot No.')
    on_hand_qty=fields.Float('On Hand QTY',compute='_cal_on_hand_qty')
    article=fields.Char('Article')
    no_of_ctn=fields.Float(string='CTN Qty',required=1)
    qty_per_ctn=fields.Float('Qty/CTN',required=1)
    uom_id=fields.Many2one('uom.uom',required=1)
    cbm=fields.Float(string='CBM')
    weight=fields.Float(string='Weight')
    price_based=fields.Selection([('CTN Qty','CTN Qty'),('Qty/CTN','Qty/CTN'),('CBM','CBM'),('Weight','Weight')],'Price Based On')
    price=fields.Float(string='Price')
    sub_total=fields.Float(string='Sub Total')
    line_id=fields.Many2one('job.order.line')
    job_order_id=fields.Many2one('job.order','Container No.',related='line_id.order_id',store=True)
    stock_receipt_date=fields.Datetime('Stock in Date')
    type=fields.Selection([('Job Order','Job Order'),('Packing List','Packing List')],'Type',related='job_order_id.type')
    
    @api.onchange('product_id','lot_id')
    def get_product_details(self):
        if self.product_id and self.lot_id:
            stock_move_obj=self.env['stock.move.line'].search([('product_id.product_tmpl_id','=',self.product_id.id),('lot_id','=',self.lot_id.id),('picking_partner_id','=',self.partner_id.id),('reference','like','/IN/')])
            if stock_move_obj:
                self.article=stock_move_obj.article
                self.qty_per_ctn=stock_move_obj.qty_per_ctn
                self.uom_id=stock_move_obj.product_uom_id.id
                self.cbm=stock_move_obj.cbm
                self.weight=stock_move_obj.weight
                self.price=self.product_id.price
                self.no_of_ctn=stock_move_obj.qty_done
                self.stock_receipt_date=stock_move_obj.date
#             for move in stock_move_obj:
#                 total_ctn=total_ctn+move.quantity_done
#             self.no_of_ctn=total_ctn
        
    @api.onchange('product_id')
    def get_lot(self):
        res={}
        if self.product_id:
            stock_line_obj=self.env['stock.move.line'].search([('product_id.product_tmpl_id','=',self.product_id.id),('picking_partner_id','=',self.partner_id.id),('reference','like','/IN/')])
            lot_list=[]
            for each in stock_line_obj:
                lot_list.append(each.lot_id.id)
            if lot_list:
                res['domain']={'lot_id':[('id','in',lot_list)]}
                return res
            else:
                res['domain']={'lot_id':[('id','=',-1)]}
                return res
        else:
            res['domain']={'lot_id':[('id','=',-1)]}
            return res
        
    @api.depends('partner_id')
    def _cal_valid_products(self):
        for each in self:
            if each.partner_id:
                stock_move_obj=self.env['stock.move.line'].search([('picking_partner_id','=',each.partner_id.id)])
                product_list=[]
                for stock in stock_move_obj:
                    product_list.append(stock.product_id.product_tmpl_id.id)
                if product_list:
                    each.product_ids=product_list
            else:
                each.product_ids=None
    @api.depends('lot_id','product_id')
    def _cal_on_hand_qty(self):
        for each in self:
            if each.lot_id and each.product_id:
                each.on_hand_qty=each.lot_id.product_qty
            else:
                each.on_hand_qty=0
    @api.onchange('price_based','no_of_ctn','qty_per_ctn','cbm','weight','price')
    def _cal_sub_price(self):
        if self.price_based=='CTN Qty' and self.price:
            self.sub_total= (self.no_of_ctn*self.price)
        elif self.price_based=='Qty/CTN' and self.price and self.qty_per_ctn:
            self.sub_total= self.qty_per_ctn*self.no_of_ctn*self.price
        elif self.price_based=='CBM' and self.price:
            self.sub_total= (self.cbm*self.price)
        elif self.price_based=='Weight' and self.price:
            self.sub_total= (self.weight*self.price)
            

class InheritAccountMOve(models.Model):
    _inherit = 'account.move'

    order_id=fields.Many2one('job.order')
    container_no=fields.Char(string='Container Number')
    
class InheritAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    detail_id=fields.Many2one('job.order.line.detail')
    cbm=fields.Float(string='CBM')

    article=fields.Char('Article',store=True)
    no_of_ctn=fields.Float(string='CTN Qty',store=True)
    qty_per_ctn=fields.Float('Qty/CTN',store=True)
    weight=fields.Float(string='Weight',store=True)
    price_based=fields.Selection([('CTN Qty','CTN Qty'),('Qty/CTN','Qty/CTN'),('CBM','CBM'),('Weight','Weight')],'Price Based On',store=True)
    price_unit = fields.Float(string='Unit Price',store=True)
    
    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids','cbm','no_of_ctn','qty_per_ctn','weight','price_based')
    def _onchange_price_subtotal(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue

            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())
    @api.model_create_multi
    def create(self, vals_list):
        obj=super(InheritAccountMoveLine,self).create(vals_list)
        
#         if obj.price_based=='CTN Qty' and obj.price_unit:
#             subtotal= (obj.quantity*obj.price_unit)
#         elif obj.price_based=='Qty/CTN' and obj.price_unit and obj.qty_per_ctn:
#             subtotal= obj.qty_per_ctn*obj.quantity*obj.price_unit
#         elif obj.price_based=='CBM' and obj.price_unit:
#             subtotal= (obj.cbm*obj.price_unit)
#         elif obj.price_based=='Weight' and obj.price_unit:
#             subtotal= (obj.weight*obj.price_unit)
#         obj.price_subtotal=subtotal
        for each in obj:
            subtotal=0
#             if not each.detail_id:
            if each.price_based=='CTN Qty' and each.price_unit:
                subtotal= (each.quantity*each.price_unit)
            elif each.price_based=='Qty/CTN' and each.price_unit and each.qty_per_ctn:
                subtotal= each.qty_per_ctn*each.quantity*each.price_unit
            elif each.price_based=='CBM' and each.price_unit:
                subtotal= (each.cbm*each.price_unit)
            elif each.price_based=='Weight' and each.price_unit:
                subtotal= (each.weight*each.price_unit)
            each.price_subtotal=subtotal
        return obj
             
#     def write(self, vals):
#         print (vals)
#         obj=super(InheritAccountMoveLine,self).write(vals)
#         print (self.price_based)
#         return obj
    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type,**optional):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}
        obj=super(InheritAccountMoveLine,self)._get_price_total_and_subtotal_model(price_unit=self.price_unit,
            quantity=self.quantity,
            discount=self.discount,
            currency=self.currency_id,
            product=self.product_id,
            partner=self.partner_id,
            taxes=self.tax_ids,
            move_type=self.move_id.move_type,**optional)
        # Compute 'price_subtotal'.
        subtotal=0
        if self.price_based=='CTN Qty' and self.price_unit:
            subtotal= (self.quantity*self.price_unit)
#             self.write({'price_subtotal':price_subtotal})
        elif self.price_based=='Qty/CTN' and self.price_unit and self.qty_per_ctn:
            subtotal= self.qty_per_ctn*self.quantity*self.price_unit
#             self.write({'price_subtotal':price_subtotal})
        elif self.price_based=='CBM' and self.price_unit:
            subtotal= (self.cbm*self.price_unit)
#             self.write({'price_subtotal':price_subtotal})
        elif self.price_based=='Weight' and self.price_unit:
            subtotal= (self.weight*self.price_unit)
#             self.write({'price_subtotal':price_subtotal})
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))
#         subtotal = quantity * line_discount_price_unit

        # Compute 'price_total'.
        if taxes:
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(line_discount_price_unit,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res
    
#     @api.onchange('price_based','price_unit','quantity','qty_per_ctn','weight','cbm')
#     def cal_sub_price(self):
# #         for each in self:
# #         each.price_subtotal=0
#         if self.price_based=='CTN Qty' and self.price_unit:
#             price_subtotal= (self.quantity*self.price_unit)
#             self.write({'price_subtotal':price_subtotal})
#         elif self.price_based=='Qty/CTN' and self.price_unit and self.qty_per_ctn:
#             price_subtotal= self.qty_per_ctn*self.quantity*self.price_unit
#             self.write({'price_subtotal':price_subtotal})
#         elif self.price_based=='CBM' and self.price_unit:
#             price_subtotal= (self.cbm*self.price_unit)
#             self.write({'price_subtotal':price_subtotal})
#         elif self.price_based=='Weight' and self.price_unit:
#             price_subtotal= (self.weight*self.price_unit)
#             self.write({'price_subtotal':price_subtotal})
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    product_owner_id=fields.Many2one('res.partner','Prodcut Owner')
    article=fields.Char('Article')
    qty_per_ctn=fields.Float('Qty/CTN')
    weight=fields.Float(string='Weight')
    cbm=fields.Float(string='CBM')
    picking_id=fields.Many2one('stock.picking','Stock Picking')
    stock_move_ids=fields.One2many('stock.move.line','product_tmpl_id','Stock Move Details')
    
class StockPicking(models.Model):
    _inherit='stock.picking'
    picking_partner_id=fields.Many2one('res.partner','Receive From',related='partner_id',store=True)
    ship_mark=fields.Char('P. Ship Mark',related='picking_partner_id.ref',store=True)
    s_ship_mark=fields.Char(related='picking_partner_id.s_ship_mark',string='S. Ship Mark',store=True)
#     def button_validate(self):
#         for each in self.move_ids_without_package:
#             if each.picking_type_id.code == 'incoming':
#                 each.product_id.write({'product_owner_id':self.partner_id.id,
#                                        'article':each.article,
#                                        'qty_per_ctn':each.qty_per_ctn,
#                                        'weight':each.weight,
#                                        'cbm':each.cbm,
#                                        'picking_id':self.id,})
#             
#         return super(StockPicking, self).button_validate()
    
class StockMove(models.Model):
    _inherit='stock.move'
    
    picking_date=fields.Date('Date')
    article=fields.Char('Article')
    qty_per_ctn=fields.Float('Qty/CTN')
    weight=fields.Float(string='Weight')
    cbm=fields.Float(string='CBM')
    total_qty=fields.Float('Total QTY')
#     lot_number=fields.Char('Lot No.')
#     location_id=fields.Many2one('stock.location',domain="['|',('company_id','=',False),('company_id','=',company_id)]")
#     done_qty=fields.Float('Done Qty')
#     
#     @api.onchange('lot_number','location_id','done_qty')
#     def cal_lot_number(self):
#         if self.lot_number and self.location_id and self.done_qty:
#             self.move_line_nosuggest_ids.unlink()
#             lot_lines = [(5,0,0)]
#             move_line={'location_dest_id':self.location_id.id,
#                        'qty_done':self.done_qty,
#                        'product_uom_id':self.product_uom.id,
#                        'product_id':self.product_id.id
#                                   }
#             lot_lines.append((0,0,move_line))
#             self.move_line_nosuggest_ids=lot_lines
            
            

                
class StockMoveLine(models.Model):
    _inherit='stock.move.line'
    
    picking_date=fields.Date('Date',related='move_id.picking_date',store=True)
    article=fields.Char('Article',related='move_id.article',store=True)
    qty_per_ctn=fields.Float('Qty/CTN',related='move_id.qty_per_ctn',store=True)
    weight=fields.Float(string='Weight',related='move_id.weight',store=True)
    cbm=fields.Float(string='CBM',related='move_id.cbm',store=True)
    total_qty=fields.Float('Total QTY',related='move_id.total_qty',store=True)
    picking_partner_id=fields.Many2one('res.partner','Receive From',related='picking_id.partner_id',store=True)
    picking_origin=fields.Char('Source Document',related='picking_id.origin',store=True)
    picking_type_id=fields.Many2one('stock.picking.type',related='picking_id.picking_type_id',store=True)
    ship_mark=fields.Char('P. Ship Mark',related='picking_partner_id.ref',store=True)
    s_ship_mark=fields.Char(related='picking_partner_id.s_ship_mark',string='S. Ship Mark',store=True)
    dest_location_id=fields.Many2one('stock.location',related='picking_id.location_dest_id',string='Warehouse',store=True)
    product_tmpl_id=fields.Many2one('product.template','Product Template',related='product_id.product_tmpl_id',store=True)
class Partner(models.Model):
    _inherit='res.partner'
    s_ship_mark=fields.Char('S. Ship Mark')

class AccountMove(models.Model):
    _inherit='account.move'
    ship_mark=fields.Char('P. Ship Mark',related='partner_id.ref',store=True)
    s_ship_mark=fields.Char(related='partner_id.s_ship_mark',string='S. Ship Mark',store=True)