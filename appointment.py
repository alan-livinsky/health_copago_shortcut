from trytond.model import fields
from trytond.pool import PoolMeta


class Appointment(metaclass=PoolMeta):
    __name__ = 'gnuhealth.appointment'

    copago_paid = fields.Boolean('Copago Pagado', readonly=True)
    copago_status = fields.Function(
        fields.Selection([
            ('pendiente', 'Pendiente'),
            ('pagado', 'Pagado'),
        ], 'Estado Copago'),
        'get_copago_status')

    @staticmethod
    def default_copago_paid():
        return False

    def get_copago_status(self, name):
        return 'pagado' if self.copago_paid else 'pendiente'

    @classmethod
    def copy(cls, appointments, default=None):
        default = {} if default is None else default.copy()
        default.setdefault('copago_paid', False)
        return super(Appointment, cls).copy(appointments, default=default)
