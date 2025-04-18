import datetime
import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import \
    set_fiscalyear_invoice_sequences
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        today = datetime.date.today()

        # Install modules
        activate_modules([
            'account_bank',
            'account_es',
            'account_payment_type',
            'account_payment',
            ])

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        payable = accounts['payable']
        expense = accounts['expense']
        revenue = accounts['revenue']
        receivable = accounts['receivable']
        Journal = Model.get('account.journal')
        expense_journal, = Journal.find([('code', '=', 'EXP')])
        revenue_journal, = Journal.find([('code', '=', 'REV')])

        # Create payment_type
        PaymentType = Model.get('account.payment.type')
        payment_type = PaymentType(
            name='Bank Account Payable',
            )
        payment_type.save()
        payment_type_receivable = PaymentType(
            name='Bank Account Receivable',
            kind='receivable',
            )
        payment_type_receivable.save()

        # Create payment journal
        PaymentJournal = Model.get('account.payment.journal')
        payment_journal_payable = PaymentJournal(
            name='Manual',
            process_method='manual',
            payment_type=payment_type,
            )
        payment_journal_payable.save()
        payment_journal_receivable = PaymentJournal(
            name='Manual',
            process_method='manual',
            payment_type=payment_type_receivable,
            )
        payment_journal_receivable.save()

        # Create parties
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()
        supplier = Party(name='Supplier')
        supplier.save()

        # Create payable move
        Move = Model.get('account.move')
        move = Move(
            journal=expense_journal,
            )
        move.lines.new(
            account=payable,
            party=supplier,
            credit=Decimal('50.00'),
            maturity_date=today,
            )
        move.lines.new(
            account=expense,
            debit=Decimal('50.00'),
            )
        move.click('post')

        # Create a payment group for the line
        Payment = Model.get('account.payment')
        line, = [l for l in move.lines if l.account == payable]
        pay_line = Wizard('account.move.line.create_payment_group', [line])
        pay_line.form.journal = payment_journal_payable
        pay_line.form.planned_date = today
        pay_line.execute('create_')
        payment, = Payment.find([('kind', '=', 'payable')])
        self.assertNotEqual(payment.group, None)
        self.assertEqual(payment.party, supplier)
        self.assertEqual(payment.amount, Decimal('50.00'))
        self.assertEqual(payment.state, 'processing')

        # Create receivable move
        move = Move(
            journal=revenue_journal,
            )
        move.lines.new(
            account=receivable,
            party=customer,
            debit=Decimal('50.00'),
            maturity_date=today,
            )
        move.lines.new(
            account=revenue,
            credit=Decimal('50.00'),
            )
        move.click('post')

        # Create a payment group for the line
        Payment = Model.get('account.payment')
        PaymentGroup = Model.get('account.payment.group')
        line, = [l for l in move.lines if l.account == receivable]
        pay_line = Wizard('account.move.line.create_payment_group', [line])
        pay_line.form.journal = payment_journal_receivable
        pay_line.form.planned_date = today
        pay_line.execute('create_')
        payment, = Payment.find([('kind', '=', 'receivable')])
        self.assertNotEqual(payment.group, None)
        self.assertEqual(payment.party, customer)
        self.assertEqual(payment.amount, Decimal('50.00'))
        self.assertEqual(payment.state, 'processing')

        # Create three payable moves
        move1 = Move(
            journal=expense_journal,
            )
        move1.lines.new(
            account=payable,
            party=supplier,
            credit=Decimal('30.00'),
            maturity_date=today,
            )
        move1.lines.new(
            account=expense,
            debit=Decimal('30.00'),
            )
        move1.click('post')

        move2 = Move(
            journal=expense_journal,
            )
        move2.lines.new(
            account=payable,
            party=supplier,
            credit=Decimal('150.00'),
            maturity_date=today,
            )
        move2.lines.new(
            account=expense,
            debit=Decimal('150.00'),
            )
        move2.click('post')
        move3 = Move(
            journal=expense_journal,
            )
        move3.lines.new(
            account=payable,
            party=customer,
            credit=Decimal('90.00'),
            maturity_date=today,
            )
        move3.lines.new(
            account=expense,
            debit=Decimal('90.00'),
            )
        move3.click('post')

        # Create a join payment group
        line1, = [l for l in move1.lines if l.account == payable]
        line2, = [l for l in move2.lines if l.account == payable]
        line3, = [l for l in move3.lines if l.account == payable]
        pay_line = Wizard('account.move.line.create_payment_group',
                          [line1, line2, line3])
        pay_line.form.journal = payment_journal_payable
        pay_line.form.planned_date = today
        pay_line.form.join = True
        pay_line.execute('create_')
        payment1, payment2 = Payment.find([])[-2:]
        group = PaymentGroup(3)
        self.assertEqual(payment1.amount, Decimal('150.00'))
        self.assertEqual(payment1.line, line2)
        self.assertEqual(payment1.group, group)

        self.assertEqual(payment2.amount, Decimal('90.00'))
        self.assertEqual(payment2.line, line3)

        self.assertEqual(group.payment_amount, Decimal('270.00'))
        self.assertEqual(group.join, True)
