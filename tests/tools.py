# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from proteus import Model, Wizard
from trytond.modules.company.tests.tools import get_company


def create_chart(company=None, account_code_digits=None, config=None):
    "Create chart of accounts"
    AccountConf = Model.get('account.configuration')
    AccountTemplate = Model.get('account.account.template', config=config)
    ModelData = Model.get('ir.model.data')

    if not company:
        company = get_company(config=config)

    data, = ModelData.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'pgc_0'),
            ], limit=1)

    if account_code_digits:
        account_conf = AccountConf(1)
        account_conf.default_account_code_digits = account_code_digits
        account_conf.save()

    account_template = AccountTemplate(data.db_id)

    create_chart = Wizard('account.create_chart')
    create_chart.execute('account')
    create_chart.form.account_template = account_template
    create_chart.form.company = company
    create_chart.execute('create_account')

    accounts = get_accounts(company, config=config)

    create_chart.form.account_receivable = accounts['receivable']
    create_chart.form.account_payable = accounts['payable']
    create_chart.execute('create_properties')
    return create_chart


def get_accounts(company=None, config=None):
    "Return accounts per kind"
    Account = Model.get('account.account', config=config)
    Data  = Model.get('ir.model.data', config=config)

    pgc_570, = Data.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'pgc_570_child'),
            ], limit=1)
    pgc_4700, = Data.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'pgc_4700_child'),
            ], limit=1)
    if not company:
        company = get_company(config=config)
    accounts = {}
    accounts['receivable'], = Account.find([
            ('type.receivable', '=', True),
            ('company', '=', company.id),
            ], limit=1)
    accounts['payable'], = Account.find([
            ('type.payable', '=', True),
            ('company', '=', company.id),
            ], limit=1)
    accounts['revenue'], = Account.find([
            ('type.revenue', '=', True),
            ('company', '=', company.id),
            ], limit=1)
    accounts['expense'], = Account.find([
            ('type.expense', '=', True),
            ('company', '=', company.id),
            ], limit=1)
    accounts['cash'], = Account.find([
            ('company', '=', company.id),
            ('template', '=', pgc_570.db_id),
            ], limit=1)
    accounts['tax'], = Account.find([
            ('company', '=', company.id),
            ('template', '=', pgc_4700.db_id),
            ], limit=1)
    return accounts


def create_tax(rate, company=None, config=None):
    "Create a tax of rate"
    Tax = Model.get('account.tax', config=config)

    if not company:
        company = get_company(config=config)

    accounts = get_accounts(company, config=config)

    tax = Tax()
    tax.name = 'Tax %s' % rate
    tax.description = tax.name
    tax.type = 'percentage'
    tax.rate = rate
    tax.invoice_account = accounts['tax']
    tax.credit_note_account = accounts['tax']
    tax.tax_kind = 'vat'
    return tax

def get_taxes(company=None, config=None):
    "Return accounts per kind"
    Account = Model.get('account.tax', config=config)
    Data  = Model.get('ir.model.data', config=config)

    iva_rep_21, = Data.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'iva_rep_21')], limit=1)
    iva_X21_compras_bc, = Data.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'iva_X21_compras_bc')], limit=1)
    iva_rep_10, = Data.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'iva_rep_10')], limit=1)
    iva_X10_compras_bc, = Data.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'iva_X10_compras_bc')], limit=1)
    if not company:
        company = get_company()
    taxes = {}
    taxes['customer_tax'], = Account.find([
            ('template', '=', iva_rep_21.db_id),
            ('company', '=', company.id),
            ], limit=1)
    taxes['supplier_tax'], = Account.find([
            ('template', '=', iva_X21_compras_bc.db_id),
            ('company', '=', company.id),
            ], limit=1)
    taxes['customer_tax_10'], = Account.find([
            ('template', '=', iva_rep_10.db_id),
            ('company', '=', company.id),
            ], limit=1)
    taxes['supplier_tax_10'], = Account.find([
            ('template', '=', iva_X10_compras_bc.db_id),
            ('company', '=', company.id),
            ], limit=1)
    return taxes

def get_tax(code, company=None):
    Tax = Model.get('account.tax')
    Data = Model.get('ir.model.data')

    if not company:
        company = get_company()

    ids = Data.find([
        ('module', '=', 'account_es'),
        ('fs_id', '=', code),
        ], limit=1)
    assert ids, f'Tax template {code} not found'
    taxes = Tax.find([
        ('template', '=', ids[0].db_id),
        ('company', '=', company),
        ], limit=1)
    assert taxes, f'Tax {code} not found in company {company.rec_name}'
    return taxes[0]
