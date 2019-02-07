
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

from odoo.addons import decimal_precision as dp

from odoo.tools import float_compare, pycompat


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'
    
    _sql_constraints = [
        ('barcode_uniq', 'Check(1=1)', "A barcode can only be assigned to one product !"),
    ]
