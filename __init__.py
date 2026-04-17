from trytond.pool import Pool

from . import wizard


def register():
    Pool.register(
        wizard.OpenAppointmentCopagoServices,
        wizard.GenerateAppointmentCopago,
        module='health_copago_shortcut', type_='wizard')
