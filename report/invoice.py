from trytond.report import Report


class CopagoInvoiceReport(Report):
    __name__ = 'health_copago_shortcut.invoice'

    @classmethod
    def get_context(cls, records, header, data):
        context = super().get_context(records, header, data)
        format_number = context.get('format_number')

        def format_number_symbol(value, lang, symbol, digits=None):
            if format_number:
                try:
                    number = format_number(value, lang, digits=digits)
                except TypeError:
                    number = format_number(value, lang)
            else:
                number = str(value)

            symbol_text = (
                getattr(symbol, 'symbol', None)
                or getattr(symbol, 'name', None)
                or getattr(symbol, 'rec_name', None)
                or '')
            return ('%s %s' % (number, symbol_text)).strip()

        context['format_number_symbol'] = format_number_symbol
        return context
