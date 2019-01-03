# -*- coding: utf-8 -*-

import base64
from itertools import groupby
import re
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import BytesIO
import requests
from pytz import timezone

from lxml import etree
from lxml.objectify import fromstring
from suds.client import Client

from odoo import _, api, fields, models, tools
from odoo.tools.xml_utils import _check_with_xsd
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.tools import float_round
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_repr

CFDI_TEMPLATE = 'l10n_mx_edi.cfdiv32'
CFDI_TEMPLATE_33 = 'l10n_mx_edi.cfdiv33'
CFDI_XSLT_CADENA = 'l10n_mx_edi/data/%s/cadenaoriginal.xslt'
CFDI_XSLT_CADENA_TFD = 'l10n_mx_edi/data/xslt/3.3/cadenaoriginal_TFD_1_1.xslt'
# Mapped from original SAT state to l10n_mx_edi_sat_status selection value
# https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc?wsdl
CFDI_SAT_QR_STATE = {
    'No Encontrado': 'not_found',
    'Cancelado': 'cancelled',
    'Vigente': 'valid',
}

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
        
    @api.multi
    def _l10n_mx_edi_get_payment_policy(self):
        self.ensure_one()
        version = self.l10n_mx_edi_get_pac_version()
        term_ids = self.payment_term_id.line_ids
        if version == '3.2':
            if len(term_ids.ids) > 1:
                return 'Pago en parcialidades'
            else:
                return 'Pago en una sola exhibición'
        elif version == '3.3' and self.date_due and self.date_invoice:
            # In CFDI 3.3 - SAT 2018 rule 2.7.1.44, the payment policy is PUE
            # if the invoice will be paid before 17th of the following month,
            # PPD otherwise
            date_pue = (fields.Date.from_string(self.date_invoice) +
                        relativedelta(day=17, months=1))
            date_due = fields.Date.from_string(self.date_due)
            return 'PPD' if (
                self.payment_term_id.name != 'PUE') else 'PUE'
        return ''
