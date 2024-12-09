# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from . import account
from . import company
from . import currency
from . import invoice
from . import party
from . import payment
from . import product
from . import tax
from . import move


def register():
    Pool.register(
        account.Account,
        account.AccountTemplate,
        account.Period,
        account.AccountType,
        account.AccountTypeTemplate,
        company.Company,
        currency.Currency,
        invoice.Invoice,
        invoice.InvoiceLine,
        party.PartyIdentifier,
        product.Category,
        product.CategoryAccount,
        product.Template,
        tax.TaxCodeTemplate,
        tax.TaxTemplate,
        tax.Tax,
        tax.TaxRuleTemplate,
        tax.TaxRuleLineTemplate,
        move.Move,
        module='account_es', type_='model')
    Pool.register(
        account.CreateChart,
        move.CancelMoves,
        module='account_es', type_='wizard')
    Pool.register(
        payment.AccountPaymentClearing,
        depends=['account_payment_clearing'],
        module='account_es', type_='model')
