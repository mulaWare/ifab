# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
import math
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, AccessError

class MaterialPurchaseRequisition(models.Model):
    _name = "material.purchase.requisition"
    _rec_name = 'sequence'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    @api.model
    def create(self , vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('material.purchase.requisition') or '/'
        return super(MaterialPurchaseRequisition, self).create(vals)

    @api.model
    def _map_lines_default_valeus(self, line):
        """ get the default value for the copied lines on requisition duplication """
        return {
            'product_id': line.product_id.id,
            'description': line.description,
            'qty': line.qty,
            'uom_id': line.uom_id.id,
            'requisition_action': line.requisition_action,
            'vendor_id': [(4, x) for x in line.vendor_id.ids],
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': [(4, x) for x in line.analytic_tag_ids.ids],
            'location_id': line.location_id.id,
        }

    @api.multi
    def map_lines(self, new_requisition_id):
        """ copy and map lines from old to new requisition """
        lines = self.env['requisition.line']
        # We want to copy archived lines, but do not propagate an active_test context key
        line_ids = self.env['requisition.line'].search([('requisition_id', '=', self.id)]).ids
        for line in self.env['requisition.line'].browse(line_ids):
            # preserve task name and stage, normally altered during copy
            defaults = self._map_lines_default_valeus(line)
            lines += line.copy(defaults)
        return self.browse(new_requisition_id).write({'requisition_line_ids': [(6, 0, lines.ids)]})

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
        requisition = super(MaterialPurchaseRequisition, self).copy(default)
        if 'requisition_line_ids' not in default:
            self.map_lines(requisition.id)
        return requisition

    @api.model
    def default_get(self, flds):
        result = super(MaterialPurchaseRequisition, self).default_get(flds)
        #result['employee_id'] = self.env.user.partner_id.id
        result['requisition_date'] = datetime.now()
        return result

    @api.multi
    def confirm_requisition(self):
        res = self.write({
                            'state':'department_approval',
                            'confirmed_by_id':self.env.user.id,
                            'confirmed_date' : datetime.now()
                        })
        template_id = self.env['ir.model.data'].get_object_reference(
                                              'bi_material_purchase_requisitions',
                                              'email_employee_purchase_requisition')[1]
        email_template_obj = self.env['mail.template'].sudo().browse(template_id)
        if template_id:
            values = email_template_obj.generate_email(self.id, fields=None)
            values['email_from'] = self.employee_id.work_email
            values['email_to'] = self.requisition_responsible_id.email
            values['res_id'] = False
            mail_mail_obj = self.env['mail.mail']
            #request.env.uid = 1
            msg_id = mail_mail_obj.sudo().create(values)
            if msg_id:
                mail_mail_obj.send([msg_id])
        return res

    @api.multi
    def department_approve(self):
        res = self.write({
                            'state':'ir_approve',
                            'department_manager_id':self.env.user.id,
                            'department_approval_date' : datetime.now()
                        })
        template_id = self.env['ir.model.data'].get_object_reference(
                                              'bi_material_purchase_requisitions',
                                              'email_manager_purchase_requisition')[1]
        email_template_obj = self.env['mail.template'].sudo().browse(template_id)
        if template_id:
            values = email_template_obj.generate_email(self.id, fields=None)
            values['email_from'] = self.env.user.partner_id.email
            values['email_to'] = self.employee_id.work_email
            values['res_id'] = False
            mail_mail_obj = self.env['mail.mail']
            #request.env.uid = 1
            msg_id = mail_mail_obj.sudo().create(values)
            if msg_id:
                mail_mail_obj.send([msg_id])
        return res

    @api.multi
    def action_cancel(self):
        res = self.write({
                            'state':'cancel',
                        })
        return res

    @api.multi
    def action_received(self):
        res = self.write({
                            'state':'received',
                            'received_date' : datetime.now()
                        })
        return res

    @api.multi
    def action_reject(self):
        res = self.write({
                            'state':'cancel',
                            'rejected_date' : datetime.now(),
                            'rejected_by' : self.env.user.id
                        })
        return res

    @api.multi
    def action_reset_draft(self):
        res = self.write({
                            'state':'new',
                        })
        return res


    @api.multi
    def action_approve(self):
        res = self.write({
                            'state':'approved',
                            'approved_by_id':self.env.user.id,
                            'approved_date' : datetime.now()
                        })
        template_id = self.env['ir.model.data'].get_object_reference(
                                              'bi_material_purchase_requisitions',
                                              'email_user_purchase_requisition')[1]
        email_template_obj = self.env['mail.template'].sudo().browse(template_id)
        if template_id:
            values = email_template_obj.generate_email(self.id, fields=None)
            values['email_from'] = self.employee_id.work_email
            values['email_to'] = self.employee_id.work_email
            values['res_id'] = False
            mail_mail_obj = self.env['mail.mail']
            #request.env.uid = 1
            msg_id = mail_mail_obj.sudo().create(values)
            if msg_id:
                mail_mail_obj.send([msg_id])
        return res

    @api.multi
    def create_picking_po(self):
        purchase_order_obj = self.env['purchase.order']
        purchase_order_line_obj = self.env['purchase.order.line']

        for line in self.requisition_line_ids:
            if line.requisition_action == 'purchase_order':
                for vendor in line.vendor_id:
                    pur_order = purchase_order_obj.search([('requisition_po_id','=',self.id),('partner_id','=',vendor.id)])
                    if pur_order:
                        po_line_vals = {
                                        'product_id' : line.product_id.id,
                                        'product_qty': line.qty,
                                        'name' : line.description,
                                        'price_unit' : line.product_id.list_price,
                                        'account_analytic_id' : line.account_analytic_id.id,
                                        'analytic_tag_ids': [(4, x) for x in line.analytic_tag_ids.ids],
                                        'date_planned' : self.requisition_deadline_date,
                                        'product_uom' : line.uom_id.id,
                                        'order_id' : pur_order.id,
                        }
                        purchase_order_line = purchase_order_line_obj.sudo().create(po_line_vals)
                        purchase_order_line.onchange_product_id()

                    else:
                        vals = {
                                'partner_id' : vendor.id,
                                'company_id' : self.env.user.company_id.id,
                                'date_order' : datetime.now(),
                                'requisition_po_id' : self.id,
                                'state' : 'draft',
                                'origin' : self.sequence,
                                'project_id' : self.project_id.id,
                                'pm_id': self.pm_id.id,
                                'account_analytic_id' : self.account_analytic_id.id,
                                'analytic_tag_ids': [(4, x) for x in self.analytic_tag_ids.ids],
                        }
                        purchase_order = purchase_order_obj.sudo().create(vals)
                        purchase_order.onchange_partner_id()
                        po_line_vals = {
                                        'product_id' : line.product_id.id,
                                        'product_qty': line.qty,
                                        'name' : line.description,
                                        'price_unit' : line.product_id.list_price,
                                        'account_analytic_id' : line.account_analytic_id.id,
                                        'analytic_tag_ids': [(4, x) for x in line.analytic_tag_ids.ids],
                                        'date_planned' : self.requisition_deadline_date,
                                        'product_uom' : line.uom_id.id,
                                        'order_id' : purchase_order.id,
                        }
                        purchase_order_line = purchase_order_line_obj.sudo().create(po_line_vals)
                        purchase_order_line.onchange_product_id()
            else:
                for vendor in line.vendor_id:
                    stock_picking_obj = self.env['stock.picking']
                    stock_move_obj = self.env['stock.move']
                    stock_picking_type_obj = self.env['stock.picking.type']
                    picking_type_ids = stock_picking_type_obj.search([('code','=','internal')])
                    #employee_id = self.env['hr.employee'].search('id','=',self.env.user.name)
                    pur_order = stock_picking_obj.search([('requisition_picking_id','=',self.id),('partner_id','=',vendor.id)])
                    if pur_order:
                        pic_line_val = {
                                        'name': line.product_id.name,
                                        'product_id' : line.product_id.id,
                                        'product_uom_qty' : line.qty,
                                        'picking_id' : stock_picking.id,
                                        'product_uom' : line.uom_id.id,
                                        'location_id': line.location_id.id,
                                        'location_dest_id' : self.employee_id.destination_location_id.id,

                        }
                        stock_move = stock_move_obj.sudo().create(pic_line_val)

                    else:
                        val = {
                                'partner_id' : vendor.id,
                                'location_id'  : line.location_id.id,
                                'location_dest_id' : self.employee_id.destination_location_id.id,
                                'picking_type_id' : picking_type_ids[0].id,
                                'company_id': self.env.user.company_id.id,
                                'requisition_picking_id' : self.id,
                                'origin' : self.sequence,
                        }
                        stock_picking = stock_picking_obj.sudo().create(val)
                        pic_line_val = {
                                        'partner_id' : vendor.id,
                                        'name': line.product_id.name,
                                        'product_id' : line.product_id.id,
                                        'product_uom_qty' : line.qty,
                                        'product_uom' : line.uom_id.id,
                                        'location_id': line.location_id.id,
                                        'location_dest_id' : self.employee_id.destination_location_id.id,
                                        'picking_id' : stock_picking.id

                        }
                        stock_move = stock_move_obj.sudo().create(pic_line_val)

        res = self.write({
                            'state':'po_created',
                        })
        return res

    @api.multi
    def _get_internal_picking_count(self):
        for picking in self:
            picking_ids = self.env['stock.picking'].search([('requisition_picking_id','=',picking.id)])
            picking.internal_picking_count = len(picking_ids)

    @api.multi
    def internal_picking_button(self):
        self.ensure_one()
        return {
            'name': 'Internal Picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_picking_id', '=', self.id)],
        }

    @api.multi
    def _get_purchase_order_count(self):
        for po in self:
            po_ids = self.env['purchase.order'].search([('requisition_po_id','=',po.id)])
            po.purchase_order_count = len(po_ids)

    @api.multi
    def purchase_order_button(self):
        self.ensure_one()
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('requisition_po_id', '=', self.id)],
        }

    @api.multi
    def _get_emp_destination(self):
        if not self.employee_id.destination_location_id:
            return
        self.destination_location_id = self.employee_id.destination_location_id

    @api.multi
    @api.onchange('project_id')
    def onchange_project_id(self):
        res = {}
        if not self.project_id:
            return res
        self.analytic_tag_ids = self.project_id.analytic_account_id.tag_ids.ids
        if not self.requisition_line_ids:
            return
        for line in self.requisition_line_ids:
            line.account_analytic_id = self.account_analytic_id.id
            line["analytic_tag_ids"]= [(6,0, x) for x in self.analytic_tag_ids.id]


    sequence = fields.Char(string='Sequence', readonly=True,copy =False)
    employee_id = fields.Many2one('hr.employee',string="Employee",required=True)
    department_id = fields.Many2one('hr.department',string="Department",required=True, related='employee_id.department_id', readonly=1)
    requisition_responsible_id  = fields.Many2one('res.users',string="Requisition Responsible")
    requisition_date = fields.Date(string="Requisition Date",required=True)
    received_date = fields.Date(string="Received Date",readonly=True)
    requisition_deadline_date = fields.Date(string="Requisition Deadline", default=fields.Datetime.now)
    state = fields.Selection([
                                ('new','New'),
                                ('department_approval','Waiting PM Approval'),
                                ('ir_approve','Waiting Purchasement Approved'),
                                ('approved','Approved'),
                                ('po_created','Purchase Order Created'),
                                ('received','Received'),
                                ('cancel','Cancel')],string='Stage',default="new")
    requisition_line_ids = fields.One2many('requisition.line','requisition_id',string="Requisition Line ID")
    confirmed_by_id = fields.Many2one('res.users',string="Confirmed By")
    department_manager_id = fields.Many2one('res.users',string="PM")
    approved_by_id = fields.Many2one('res.users',string="Approved By")
    rejected_by = fields.Many2one('res.users',string="Rejected By")
    confirmed_date = fields.Date(string="Confirmed Date",readonly=True)
    department_approval_date = fields.Date(string="Department Approval Date",readonly=True)
    approved_date = fields.Date(string="Approved Date",readonly=True)
    rejected_date = fields.Date(string="Rejected Date",readonly=True)
    reason_for_requisition = fields.Text(string="Reason For Requisition")
    source_location_id = fields.Many2one('stock.location',string="Source Location")
    destination_location_id = fields.Many2one('stock.location',string="Destination Location",compute="_get_emp_destination")
    internal_picking_id = fields.Many2one('stock.picking',string="Internal Picking")
    internal_picking_count = fields.Integer('Internal Picking', compute='_get_internal_picking_count')
    purchase_order_count = fields.Integer('Purchase Order', compute='_get_purchase_order_count')
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.user.company_id.id, index=1, readonly=1)
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.user.company_id.currency_id.id,
        required=True)
    project_id = fields.Many2one('project.project',
        string='Project',
        default=lambda self: self.env.context.get('default_project_id'),
        index=True,
        track_visibility='onchange',
        change_default=True)
    pm_id = fields.Many2one('res.users',string="PM",related='project_id.user_id',readonly=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account',related='project_id.analytic_account_id',readonly=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')


class RequisitionLine(models.Model):
    _name = "requisition.line"

    @api.multi
    @api.onchange('product_id','requisition_action',)
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        self.description = self.product_id.name
        self.account_analytic_id = self.requisition_id.account_analytic_id.id
        self.analytic_tag_ids = self.requisition_id.analytic_tag_ids.ids
        inventory =  self.env['stock.inventory.line'].search(['&',('product_id','=',self.product_id.id),('location_id.usage','=', 'internal')], limit=1)
        self.location_id = inventory.location_id.id

        for record in self:
            if record.requisition_action == 'internal_picking':
                partner = self.env.user.partner_id.id
                vendor = self.env['res.partner'].browse(partner)
                record.vendor_id = vendor
            if record.requisition_action == 'purchase_order':
                record.vendor_id = record.product_id.seller_ids.mapped('name')


    product_id = fields.Many2one('product.product', string="Product")
    description = fields.Text(string="Description")
    qty = fields.Float(string="Quantity",default=1.0)
    uom_id = fields.Many2one('product.uom',string="Unit Of Measure")
    requisition_id = fields.Many2one('material.purchase.requisition',string="Requisition Line")
    requisition_action = fields.Selection([('purchase_order','Purchase Order'),('internal_picking','Internal Picking')],default='internal_picking',string="Requisition Action")
    vendor_id = fields.Many2many('res.partner',string="Vendors")
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    qty_available = fields.Float(string="Qty Available",related='product_id.qty_available',readonly=True)
    location_id = fields.Many2one('stock.location', string='Location', )


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    requisition_picking_id = fields.Many2one('material.purchase.requisition',string="Purchase Requisition")

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    requisition_po_id = fields.Many2one('material.purchase.requisition',string="Purchase Requisition")

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    destination_location_id = fields.Many2one('stock.location',string="Destination Location")

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    destination_location_id = fields.Many2one('stock.location',string="Destination Location")
