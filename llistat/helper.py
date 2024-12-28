from datetime import datetime


def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, '%d/%m/%Y').date()  # Expected format: dd/mm/yyyy
    except ValueError:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()  # Another common format: yyyy-mm-dd
        except ValueError:
            return None
