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

    @api.multi
    @api.onchange('project_id')
    def onchange_project_id(self):
        res = {}
        if not self.project_id:
            return res
        self.analytic_tag_ids = self.project_id.analytic_account_id.tag_ids.ids

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
