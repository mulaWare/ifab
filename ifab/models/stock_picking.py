# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import namedtuple
import json
import time
from datetime import date

from itertools import groupby
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from operator import itemgetter


class Picking(models.Model):
    _name = "stock.picking"
    _inherit = "stock.picking"

    @api.one
    def _is_internal_picking(self):
        # TDE FIXME: better implementation
        is_int = (self.partner_id.name == self.company_id.partner_id.name)
        self.is_internal_picking = bool(is_int)


    @api.onchange('is_ok')
    def _is_verification(self):
        if self.is_ok:
            res = self.write({
                             'is_verification':self.env.user.id,
                             'is_date' : fields.Datetime.now(),
                            })
            return


    READONLY_STATES = {
                        'done': [('readonly', True)],
                        'cancel': [('readonly', True)],
                      }
    is_internal_picking = fields.Boolean(string='Is internal picking ?', compute='_is_internal_picking')
    is_tech_specs = fields.Boolean(string='Is technical specs ok ?', states=READONLY_STATES)
    is_quality = fields.Boolean(string='Is Qualtity specs ok ?', states=READONLY_STATES)
    is_price = fields.Boolean(string='Is Price right ?', states=READONLY_STATES)
    is_qty = fields.Boolean(string='Is Quantity ok ?', states=READONLY_STATES)
    is_delivery = fields.Boolean(string='Is Delivery time ok ?', states=READONLY_STATES)
    is_ok = fields.Selection(string='Is authorized ?', states=READONLY_STATES,
        selection=[('ok', 'Ok'), ('no', 'No')],)
    is_verification = fields.Many2one('res.users',string="Verification Responsible",)
    is_date = fields.Date(string="Verification Date",)
