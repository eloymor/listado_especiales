from datetime import datetime


def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, '%d/%m/%y').date()  # dd/mm/yy
    except ValueError:
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()  # dd/mm/yyyy
        except ValueError:
            return None
