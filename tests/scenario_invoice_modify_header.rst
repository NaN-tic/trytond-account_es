==============================
Invoice Modify Header Scenario
==============================

Imports::

    >>> from proteus import Model, Wizard
    >>> from decimal import Decimal
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, create_tax, get_accounts
    >>> from trytond.exceptions import UserWarning

Activate modules::

    >>> config = activate_modules('account_es')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> revenue = accounts['revenue']

Create tax and tax rule::

    >>> tax = create_tax(Decimal('.10'))
    >>> tax.save()
    >>> other_tax = create_tax(Decimal('.05'))
    >>> other_tax.save()

    >>> TaxRule = Model.get('account.tax.rule')
    >>> foreign = TaxRule(name='Foreign Customers', company=company)
    >>> foreign_tax = foreign.lines.new()
    >>> foreign_tax.origin_tax = tax
    >>> foreign_tax.tax = other_tax
    >>> foreign.save()

Create account categories::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_revenue = revenue
    >>> account_category.customer_taxes.append(tax)
    >>> account_category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')

    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('10')
    >>> template.account_category = account_category
    >>> template.save()
    >>> product, = template.products

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()
    >>> another = Party(name='Another Customer', customer_tax_rule=foreign)
    >>> another.save()

Create a invoice with a line::

    >>> Invoice = Model.get('account.invoice')
    >>> Line = Model.get('account.invoice.line')
    >>> invoice = Invoice()
    >>> invoice.party = customer
    >>> invoice_line = invoice.lines.new()
    >>> invoice_line.product = product
    >>> invoice_line.quantity = 3
    >>> invoice_line.unit_price = Decimal('10')
    >>> invoice_line_comment = invoice.lines.new(type='comment')
    >>> invoice.save()
    >>> invoice.untaxed_amount, invoice.tax_amount, invoice.total_amount
    (Decimal('30.00'), Decimal('3.00'), Decimal('33.00'))

Change the party::

    >>> modify_header = invoice.click('modify_header')
    >>> modify_header.form.party == customer
    True
    >>> modify_header.form.party = another
    >>> try:
    ...     modify_header.execute('modify')
    ... except UserWarning as warning:
    ...     _, (key, *_) = warning.args
    ...     raise  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
       ...
    UserWarning: ...
    >>> Warning = Model.get('res.user.warning')
    >>> Warning(user=config.user, name=key).save()
    >>> modify_header.execute('modify')

    >>> invoice.party.name
    'Another Customer'
    >>> invoice.untaxed_amount, invoice.tax_amount, invoice.total_amount
    (Decimal('30.00'), Decimal('3.00'), Decimal('33.00'))

Create a invoice with a line with party::

    >>> invoice = Invoice()
    >>> invoice.party = customer
    >>> invoice.save()

    >>> invoice_line = Line()
    >>> invoice_line.invoice = invoice
    >>> invoice_line.party = customer
    >>> invoice_line.product = product
    >>> invoice_line.quantity = 3
    >>> invoice_line.unit_price = Decimal('10')
    >>> invoice_line.save()
    >>> len(invoice.lines)
    1
    >>> line1, = invoice.lines
    >>> line1.party == invoice.party
    True

Change the party::

    >>> modify_header = invoice.click('modify_header')
    >>> modify_header.form.party == customer
    True
    >>> modify_header.form.party = another
    >>> try:
    ...     modify_header.execute('modify')
    ... except UserWarning as warning:
    ...     _, (key, *_) = warning.args
    ...     raise  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
       ...
    UserWarning: ...
    >>> Warning = Model.get('res.user.warning')
    >>> Warning(user=config.user, name=key).save()
    >>> modify_header.execute('modify')

    >>> invoice.party.name
    'Another Customer'
    >>> line1, = invoice.lines
    >>> line1.party == invoice.party
    True
