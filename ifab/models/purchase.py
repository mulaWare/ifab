# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = "purchase.order"

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        if not self.requisition_id:
            return

        purchase_order_obj = self.env['purchase.order']
        purchase_order_line_obj = self.env['purchase.order.line']

        requisition = self.requisition_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id
        self.company_id = requisition.company_id.id
        self.currency_id = partner.currency_id.id
        if not self.origin or requisition.name not in self.origin.split(', '):
            if self.origin:
                if requisition.name:
                    self.origin = self.origin + ', ' + requisition.name
            else:
                self.origin = requisition.name
        self.notes = requisition.description
        self.date_order = requisition.date_end or fields.Datetime.now()
        self.picking_type_id = requisition.picking_type_id.id
        self.project_id = requisition.project_id.id

        self.onchange_partner_id()

        if requisition.type_id.line_copy != 'copy':
            return

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context({
                'lang': partner.lang,
                'partner_id': partner.id,
            })
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute taxes
            if fpos:
                taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id)).ids
            else:
                taxes_ids = line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id).ids

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_po_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
            else:
                product_qty = line.product_qty
                price_unit = line.price_unit

            if requisition.type_id.quantity_copy != 'copy':
                product_qty = 0

            # Create PO line
            order_line_values = line._prepare_purchase_order_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
                taxes_ids=taxes_ids)

            po_line_vals = {
                            'product_id' : line.product_id.id,
                            'product_qty': product_qty,
                            'name' : line.product_id.description,
                            'price_unit' : price_unit,
                            'account_analytic_id' : line.account_analytic_id.id,
                            'analytic_tag_ids': [(4, x) for x in line.analytic_tag_ids.ids],
                            'date_planned' : requisition.date_end or fields.Datetime.now(),
                            'product_uom' : line.product_uom_id.id,
                            'order_id' : self.id,
                            }    

            purchase_order_line = purchase_order_line_obj.sudo().create(po_line_vals)
            purchase_order_line.onchange_product_id()




    @api.multi
    @api.onchange('project_id')
    def onchange_project_id(self):
        res = {}
        if not self.project_id:
            return res
        self.analytic_tag_ids = self.project_id.analytic_account_id.tag_ids.ids
        if not self.order_line:
            return
        for line in self.order_line:
            line.account_analytic_id = self.account_analytic_id.id
            line["analytic_tag_ids"]= [(2, x) for x in line.analytic_tag_ids.ids]
            line["analytic_tag_ids"]= [(4, x) for x in self.analytic_tag_ids.ids]
        if self.requisition_id:
            requisition = self.requisition_id
            self.account_analytic_id = requisition.account_analytic_id.id
            self.analytic_tag_ids = requisition.analytic_tag_ids.ids
            return

    @api.multi
    @api.onchange('analytic_tag_ids')
    def onchange_analytic_tag_ids(self):
        if not self.analytic_tag_ids:
            return
        for line in self.order_line:
            line["analytic_tag_ids"]= [(2, x) for x in line.analytic_tag_ids.ids]
            line["analytic_tag_ids"]= [(4, x) for x in self.analytic_tag_ids.ids]

    project_id = fields.Many2one('project.project',
        string='Project',
        default=lambda self: self.env.context.get('default_project_id'),
        index=True,
        track_visibility='onchange',
        change_default=True)
    pm_id = fields.Many2one('res.users',string="PM",related='project_id.user_id',readonly=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account',related='project_id.analytic_account_id',readonly=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = "purchase.order.line"


    @api.multi
    @api.onchange('product_id',)
    def onchange_product_id_ana(self):
        res = {}
        if not self.product_id:
            return res
        self.account_analytic_id = self.order_id.account_analytic_id.id
        self.analytic_tag_ids = self.order_id.analytic_tag_ids.ids

class PurchaseRequisition(models.Model):
    _name = "purchase.requisition"
    _inherit = "purchase.requisition"

    @api.multi
    @api.onchange('project_id')
    def onchange_project_id(self):
        res = {}
        if not self.project_id:
            return res
        self.analytic_tag_ids = self.project_id.analytic_account_id.tag_ids.ids
        if not self.line_ids:
            return
        for line in self.line_ids:
            line.account_analytic_id = self.account_analytic_id.id
            line["analytic_tag_ids"]= [(2, x) for x in line.analytic_tag_ids.ids]
            line["analytic_tag_ids"]= [(4, x) for x in self.analytic_tag_ids.ids]

    @api.multi
    @api.onchange('analytic_tag_ids')
    def onchange_analytic_tag_ids(self):
        if not self.analytic_tag_ids:
            return
        for line in self.line_ids:
            line["analytic_tag_ids"]= [(2, x) for x in line.analytic_tag_ids.ids]
            line["analytic_tag_ids"]= [(4, x) for x in self.analytic_tag_ids.ids]


    project_id = fields.Many2one('project.project',
        string='Project',
        default=lambda self: self.env.context.get('default_project_id'),
        index=True,
        track_visibility='onchange',
        change_default=True)
    pm_id = fields.Many2one('res.users',string="PM",related='project_id.user_id',readonly=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account',related='project_id.analytic_account_id',readonly=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')



class PurchaseRequisitionLine(models.Model):
    _name = "purchase.requisition.line"
    _inherit = "purchase.requisition.line"

    @api.multi
    @api.onchange('product_id',)
    def onchange_product_id_ana(self):
        res = {}
        if not self.product_id:
            return res
        self.account_analytic_id = self.requisition_id.account_analytic_id.id
        self.analytic_tag_ids = self.requisition_id.analytic_tag_ids.ids

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    @api.multi
    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        self.ensure_one()
        requisition = self.requisition_id
        if requisition.schedule_date:
            date_planned = datetime.combine(requisition.schedule_date, time.min)
        else:
            date_planned = datetime.now()
        return {
            'name': name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'product_qty': product_qty,
            'price_unit': price_unit,
            'taxes_id': [(6, 0, taxes_ids)],
            'date_planned': date_planned,
            'account_analytic_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(4, x) for x in self.analytic_tag_ids.ids],
            'move_dest_ids': self.move_dest_id and [(4, self.move_dest_id.id)] or []
        }
