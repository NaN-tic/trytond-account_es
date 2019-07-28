# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from . import account
from . import currency
from . import tax
from . import invoice


def register():
    Pool.register(
        account.Account,
        account.AccountTemplate,
        account.FiscalYear,
        account.Period,
        account.AccountType,
        account.AccountTypeTemplate,
        currency.Currency,
        tax.TaxCodeTemplate,
        tax.TaxTemplate,
        tax.Tax,
        tax.TaxRuleTemplate,
        tax.TaxRuleLineTemplate,
        invoice.InvoiceLine,
        module='account_es', type_='model')
