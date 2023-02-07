# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import sys
import unittest
import trytond.tests.test_tryton
from datetime import date
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.modules.company.tests import create_company, set_company
from trytond.modules.account_es.tests.tax_result import tax_result
from trytond.modules.account.tests import get_fiscalyear
from trytond.modules.account_invoice.tests import set_invoice_sequences
from trytond.modules.currency.tests import create_currency, add_currency_rate
from decimal import Decimal


def create_chart(company, tax=False):
    pool = Pool()
    AccountTemplate = pool.get('account.account.template')
    ModelData = pool.get('ir.model.data')
    CreateChart = pool.get('account.create_chart', type='wizard')
    Account = pool.get('account.account')

    template = AccountTemplate(ModelData.get_id(
            'account_es', 'pgc_0'))

    session_id, _, _ = CreateChart.create()
    create_chart = CreateChart(session_id)
    create_chart.account.account_template = template
    create_chart.account.company = company
    create_chart.transition_create_account()
    receivable, = Account.search([
            ('type.receivable', '=', True),
            ('company', '=', company.id),
            ],
        limit=1)
    payable, = Account.search([
            ('type.payable', '=', True),
            ('company', '=', company.id),
            ],
        limit=1)
    create_chart.properties.company = company
    create_chart.properties.account_receivable = receivable
    create_chart.properties.account_payable = payable
    create_chart.transition_create_properties()


def get_tax(xml_id):
    pool = Pool()
    ModelData = pool.get('ir.model.data')
    AccountTax = pool.get('account.tax')
    AccountTaxTemplate = pool.get('account.tax.template')

    data, = ModelData.search([
            ('module', '=', 'account_es'),
            ('fs_id', '=', xml_id),
            ], limit=1)
    template = AccountTaxTemplate(data.db_id)
    tax, = AccountTax.search([('template', '=', template.id)], limit=1)
    return (template, tax)


def get_codes(xml_ids):
    pool = Pool()
    ModelData = pool.get('ir.model.data')
    TaxCodeTemplate = pool.get('account.tax.code.template')

    datas = ModelData.search([
            ('module', '=', 'account_es'),
            ('fs_id', 'in', xml_ids),
            ])
    res = {}
    for data in datas:
        res[TaxCodeTemplate(data.db_id)] = data.fs_id
    return res


class AccountTestCase(ModuleTestCase):
    'Test Account Es module'
    module = 'account_es'

    @with_transaction()
    def test_account_chart(self):
        'Test creation of minimal chart of accounts'
        create_company()
        # with set_company(company):
        #     create_chart(company, tax=True)

    @with_transaction()
    def test_taxes(self):
        pool = Pool()
        FiscalYear = pool.get('account.fiscalyear')
        Journal = pool.get('account.journal')
        Account = pool.get('account.account')
        Party = pool.get('party.party')
        PaymentTerm = pool.get('account.invoice.payment_term')
        Invoice = pool.get('account.invoice')
        InvoiceLine = pool.get('account.invoice.line')
        Address = pool.get('party.address')
        TaxCode = pool.get('account.tax.code')
        cursor = Transaction().connection.cursor()

        company = create_company()
        with set_company(company):
            create_chart(company, tax=True)

        party = Party(name='Party')
        party.save()
        address, = Address.create([{
                    'party': party.id,
                    'street': 'St sample, 15',
                    'city': 'City',
                    }])

        cu1 = create_currency('cu1')
        add_currency_rate(cu1, Decimal("1.0"))

        term, = PaymentTerm.create([{
            'name': 'cash',
            'lines': [
                ('create', [{
                            'sequence': 0,
                            'type': 'remainder',
                            'relativedeltas': [('create', [{
                                            'days': 30,
                                            },
                                        ]),
                                ],
                }])]}])

        with set_company(company):
            fiscalyear = get_fiscalyear(company)
            fiscalyear = set_invoice_sequences(fiscalyear)
            fiscalyear.save()
            FiscalYear.create_period([fiscalyear])

            journal_revenue, = Journal.search([
                    ('code', '=', 'REV'),
                    ])
            journal_expense, = Journal.search([
                    ('code', '=', 'EXP'),
                    ])
            revenue, = Account.search([
                    ('type.revenue', '=', True),
                    ('code', 'like', '7000%'),
                    ], limit=1)
            receivable, = Account.search([
                    ('type.receivable', '=', True),
                    ('code', 'like', '430%')
                    ], limit=1)
            expense, = Account.search([
                    ('type.expense', '=', True),
                    ('code', 'like', '600%')
                    ], limit=1)
            payable, = Account.search([
                    ('type.payable', '=', True),
                    ('code', 'like', '400%')
                    ], limit=1)

            # with set_company(company):
            with Transaction().set_context(
                    periods=[x.id for x in fiscalyear.periods]):
                count = 0
                for key in sorted(tax_result.keys()):
                    count += 1
                    xml_tax, tax_name = key
                    print('%s (%s)     %s/%s' % (tax_name, xml_tax, count,
                            len(tax_result.keys())), file=sys.stderr)
                    for type_ in sorted(tax_result[key].keys()):
                        in_out, credit_invoice = type_
                        print('- %s %s' % (credit_invoice, in_out),
                            file=sys.stderr)
                        invoice = Invoice()
                        invoice.type = in_out
                        invoice.state = 'draft'
                        invoice.currency = cu1
                        invoice.company = company
                        if in_out == 'in':
                            invoice.account = payable
                        else:
                            invoice.account = receivable
                        invoice.on_change_type()
                        invoice.party = party
                        invoice.on_change_party()
                        invoice.payment_term = term
                        line = InvoiceLine()
                        line.type = 'line'
                        line.account = revenue if in_out == 'out' else expense
                        line.quantity = (1 if credit_invoice == 'invoice' else
                            -1)
                        line.unit_price = Decimal('100.00')
                        line.on_change_with_amount()
                        template, tax = get_tax(xml_tax)
                        line.taxes = [tax]
                        invoice.lines = [line]
                        invoice.invoice_date = date.today()
                        if in_out == 'in':
                            invoice.accounting_date = date.today()
                        invoice.on_change_lines()
                        invoice.save()
                        Invoice.post([invoice])
                        self.assertEqual(invoice.tax_amount,
                            tax_result[key][type_]['tax'])
                        self.assertEqual(invoice.untaxed_amount,
                            tax_result[key][type_]['base'])

                        xml_codes = list(
                            tax_result[key][type_]['codes'].keys())
                        template_codes = get_codes(xml_codes)
                        tax_code = TaxCode.search([
                                ('template', 'in', template_codes),
                                ])
                        res_codes = tax_result[key][type_]['codes']

                        txc = [template_codes[x.template] for x in tax_code]
                        self.assertEqual((set(txc) - set(res_codes.keys())),
                            set())

                        for tc in tax_code:
                            v = template_codes[tc.template]
                            amount = TaxCode.get_amount([tc],
                                res_codes[v][0])[tc.id]
                            self.assertEqual(amount, res_codes[v][1][1],
                                tc.name)

                        # Not TRUNCATE tables because SQLITE not support it
                        cursor.execute('DELETE FROM account_invoice')
                        cursor.execute('DELETE FROM account_invoice_line')
                        cursor.execute('DELETE FROM account_invoice_tax')
                        cursor.execute('DELETE FROM account_move')
                        cursor.execute('DELETE FROM account_move_line')
                        cursor.execute('DELETE FROM account_tax_line')
                        cursor.execute(
                            'DELETE FROM '
                            '"account_invoice-account_move_line"')
                        cursor.execute(
                            'DELETE FROM '
                            '"account_invoice_line_account_tax"')


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountTestCase))
    return suite
