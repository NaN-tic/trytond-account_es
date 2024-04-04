# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import fields
from trytond.model import ModelView
from trytond.pyson import Eval
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


class Move(metaclass=PoolMeta):
    __name__ = 'account.move'

    allow_draft = fields.Function(fields.Boolean('Allow Draft Move'),
        'get_allow_draft')

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        if 'state' not in cls._check_modify_exclude:
            cls._check_modify_exclude.append('state')
        cls._buttons.update({
            'draft': {
                'invisible': ((Eval('state') == 'draft')
                    | ((Eval('state') != 'draft') &
                       (~Eval('allow_draft', True)))),
                'depends': ['allow_draft'],
                },
            })

    @classmethod
    def copy(cls, moves, default=None):
        pool = Pool()
        Date = pool.get('ir.date')
        Period = pool.get('account.period')

        moves_changed = []
        final_moves = []
        for move in moves:
            if move.period.state != 'open':
                today = Date.today()
                period = Period.find(move.company, date=today)
                if default is None:
                    default_changed = {}
                else:
                    default_changed = default.copy()
                default_changed['period'] = period
                default_changed['date'] = today
                moves_changed.extend(super().copy([move], default=default_changed))
            else:
                final_moves.append(move)
        if final_moves:
            moves_changed.extend(super().copy(final_moves, default=default))
        return moves_changed

    @classmethod
    @ModelView.button
    def draft(cls, moves):
        pool = Pool()
        Line = pool.get('account.move.line')

        moves_to_draft = [m for m in moves if m.allow_draft]
        if moves_to_draft:
            cls.write(moves_to_draft, {
                'state': 'draft',
                })
            Line.check_modify([l for m in moves_to_draft for l in m.lines])

    def get_allow_draft(self, name):
        origin_lines = [l.origin for l in self.lines if l.origin]
        if self.origin or origin_lines:
            return False
        return True
