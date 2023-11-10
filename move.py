# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.i18n import gettext
from trytond.exceptions import UserError


class CancelMoves(metaclass=PoolMeta):
    __name__ = 'account.move.cancel'

    def transition_cancel(self):
        moves = self.records
        for move in moves:
            if move.origin is not None:
                raise UserError(gettext(
                    'account_es.msg_cancel_move_with_origin',
                    move=move.rec_name,
                    origin=move.origin.rec_name))
        return super().transition_cancel()
