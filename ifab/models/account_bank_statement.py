# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero, pycompat
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError, ValidationError

import time
import math

class AccountBankStatementLine(models.Model):
    _name = "account.bank.statement.line"
    _inherit = "account.bank.statement.line"

    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
    
    
                invoice_ids = []
                for aml_dict in counterpart_aml_dicts or []:
                    if aml_dict['move_line'].invoice_id:
                        invoice_ids.append(aml_dict['move_line'].invoice_id.id)
                res = super(AccountBankStatementLine, self.with_context(
                        l10n_mx_edi_manual_reconciliation=False)).process_reconciliation(
                        counterpart_aml_dicts=counterpart_aml_dicts,
                        payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)
                if not self.l10n_mx_edi_is_required():
                    return res
                payments = res.mapped('line_ids.payment_id')
                payment_method = self.l10n_mx_edi_payment_method_id.id or self.journal_id.l10n_mx_edi_payment_method_id.id
                payments.write({
                    'name': self.env['ir.sequence'].next_by_code('account.payment.customer.invoice') or '/'  or _("Bank Statement %s") %  self.date, 
                    'l10n_mx_edi_payment_method_id': payment_method,
                    'invoice_ids': [(4, 0, invoice_ids)]
                        })
                payments._l10n_mx_edi_retry()

                return res

 
