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
        move.Move,
        invoice.CreditInvoiceStart,
        module='account_es', type_='model')
    Pool.register(
        account.CreateChart,
        move.CancelMoves,
        invoice.CreditInvoice,
        module='account_es', type_='wizard')
    Pool.register(
        payment.Journal,
        payment.Group,
        payment.Payment,
        payment.ProcessPaymentStart,
        payment.CreatePaymentGroupStart,
        payment.MoveLine,
        depends=['account_payment'],
        module='account_es', type_='model')
    Pool.register(
        payment.CreatePaymentGroup,
        payment.PayLine,
        payment.ProcessPayment,
        depends=['account_payment'],
        module='account_es', type_='wizard')
    Pool.register(
        payment.AccountBankJournal,
        depends=['account_bank', 'account_payment'],
        module='account_es', type_='model')
    Pool.register(
        invoice.Invoice,
        invoice.InvoiceLine,
        depends=['account_invoice', 'account_payment'],
        module='account_es', type_='model')
    Pool.register(
        payment.AccountPaymentClearing,
        depends=['account_payment_clearing'],
        module='account_es', type_='model')
