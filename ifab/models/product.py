
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
            'Internal Reference', default=compute_default_value, readonly=True, copy=False)

    barcode = fields.Char(
        'Barcode', copy=False, oldname='ean13',
        help="International Article Number used for product identification.")

    _sql_constraints = [
        ('barcode_uniq', 'unique(barcode)', "A barcode can only be assigned to one product !"),
    ]





class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = "product.template"


    # related to display product product information if is_product_variant
    barcode = fields.Char('Barcode', oldname='ean13', related='product_variant_ids.barcode', readonly=False)
    default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code', readonly=True, 
        inverse='_set_default_code', copy=False, store=True)


    _sql_constraints = [
        ('barcode_uniq', 'unique(barcode)', "A barcode can only be assigned to one product !"),
    ]


    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.default_code = template.product_variant_ids.default_code
        for template in (self - unique_variants):
            template.default_code = ''

    @api.one
    def _set_default_code(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.default_code = self.default_code
