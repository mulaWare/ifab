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
