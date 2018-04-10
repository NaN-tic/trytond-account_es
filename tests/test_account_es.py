# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
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
from trytond import backend
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
            ('kind', '=', 'receivable'),
            ('company', '=', company.id),
            ],
        limit=1)
    payable, = Account.search([
            ('kind', '=', 'payable'),
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

    data, = ModelData.search([('module', '=', 'account_es'),
        ('fs_id', '=', xml_id)], limit=1)
    template = AccountTaxTemplate(data.db_id)
    tax, = AccountTax.search([('template', '=', template.id)], limit=1)
    return (template, tax)

def get_codes(xml_ids):
    pool = Pool()
    ModelData = pool.get('ir.model.data')
    TaxCodeTemplate = pool.get('account.tax.code.template')

    datas = ModelData.search([('module', '=', 'account_es'),
        ('fs_id', 'in', xml_ids)])

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
        company = create_company()
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
                    ('kind', '=', 'revenue'),
                    ('code', 'like', '7000%'),
                    ], limit=1)
            receivable, = Account.search([
                    ('kind', '=', 'receivable'),
                    ('code', 'like', '430%')
                    ], limit=1)
            expense, = Account.search([
                    ('kind', '=', 'expense'),
                    ('code', 'like', '600%')
                    ], limit=1)
            payable, = Account.search([
                    ('kind', '=', 'payable'),
                    ('code', 'like', '400%')
                    ], limit=1)

            with set_company(company):

                for key in tax_result.keys():
                    xml_tax, tax_name = key
                    print xml_tax, tax_name
                    for type_ in tax_result[key]:
                        t, t2 = type_
                        print xml_tax, t, t2, "*"*10
                        invoice = Invoice()
                        invoice.type = t
                        invoice.state = 'draft'
                        invoice.currency = cu1
                        invoice.company = company
                        invoice.account = receivable
                        invoice.on_change_type()
                        invoice.party = party
                        invoice.on_change_party()
                        invoice.payment_term = term
                        line = InvoiceLine()
                        line.type = 'line'
                        line.account = revenue if t == 'out' else expense
                        line.quantity = 1 if t2 == 'invoice' else -1
                        line.unit_price = Decimal('100.00')
                        line.on_change_with_amount()
                        template, tax = get_tax(xml_tax)
                        line.taxes = [tax]
                        invoice.lines = [line]
                        invoice.invoice_date = date.today()
                        invoice.accounting_date = date.today()
                        invoice.on_change_lines()
                        invoice.save()
                        Invoice.post([invoice])
                        print 'invoice:', invoice.tax_amount, invoice.untaxed_amount
                        print "res:", tax_result[key][type_]['tax'], tax_result[key][type_]['base']
                        self.assert_(invoice.tax_amount ==
                                tax_result[key][type_]['tax'])
                        self.assert_(invoice.untaxed_amount ==
                                tax_result[key][type_]['base'])

                        xml_codes = tax_result[key][type_]['codes'].keys()
                        template_codes = get_codes(xml_codes)
                        tax_code = TaxCode.search(
                            [('template', 'in', template_codes)])
                        res_codes = tax_result[key][type_]['codes']

                        txc = [template_codes[x.template] for x in
                               tax_code]

                        self.assert_(
                            (set(txc) - set(res_codes.keys()))
                            == set())

                        for tc in tax_code:
                            v = template_codes[tc.template]
                            with Transaction().set_context(
                                    periods=[x.id for x in fiscalyear.periods]):
                                amount = TaxCode.get_amount([tc],
                                    res_codes[v][0])[tc.id]
                                print v, res_codes[v]
                                print "tryton:", amount, "res:", res_codes[v][1]
                                # import pdb; pdb.set_trace()
                                self.assert_(amount == res_codes[v][1])

                        cursor = Transaction().connection.cursor()

                        if backend.name() == 'sqlite':
                            cursor.execute("delete from account_invoice")
                            cursor.execute("delete from account_invoice_line")
                            cursor.execute("delete from account_invoice_tax")
                            cursor.execute("delete from account_move")
                            cursor.execute("delete from account_move_line")
                            cursor.execute("delete from account_tax_line")
                            cursor.execute('delete from "account_invoice-account_move_line"')
                            cursor.execute('delete from "account_invoice_line_account_tax"')
                        else:
                            cursor.execute("TRUNCATE account_invoice cascade;")
                        Transaction().commit()

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountTestCase))
    return suite
