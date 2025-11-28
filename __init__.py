# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from . import account
from . import company
from . import invoice
from . import party
from . import payment
from . import product
from . import tax


def register():
    Pool.register(
        account.Account,
        account.AccountTemplate,
        account.AccountType,
        account.AccountTypeTemplate,
        company.Company,
        party.PartyIdentifier,
        product.Category,
        product.CategoryAccount,
        product.Template,
        tax.TaxCodeTemplate,
        tax.TaxTemplate,
        tax.Tax,
        tax.TaxCode,
        tax.TaxRuleTemplate,
        tax.TaxRuleLineTemplate,
        module='account_es', type_='model')
    Pool.register(
        account.CreateChart,
        module='account_es', type_='wizard')
    Pool.register(
        payment.AccountPaymentClearing,
        depends=['account_payment_clearing'],
        module='account_es', type_='model')
    Pool.register(
        invoice.Invoice,
        invoice.InvoiceLine,
        depends=['account_invoice'],
        module='account_es', type_='model')
