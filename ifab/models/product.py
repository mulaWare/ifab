
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression

from odoo.addons import decimal_precision as dp

from odoo.tools import float_compare, pycompat

import itertools

from odoo.tools import pycompat

class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    def compute_default_value(self):
        res = self.env['ir.sequence'].next_by_code('product.product.default_code') or '/'
        return res

    default_code = fields.Char(
            'Internal Reference', default=compute_default_value,
            readonly=True, copy=False)

    barcode = fields.Char(
        'Barcode', copy=False, oldname='ean13',
        help="International Article Number used for product identification.")

    _sql_constraints = [
        ('barcode_uniq', 'unique(barcode)', "A barcode can only be assigned to one product !"),
    ]
