import re


def validate_dates(date_list):
    dates = []
    for date in date_list:
        date_pattern = "^\d{4}-\d{2}-\d{2} \d{2}\.\d{2}$"
        if bool(re.match(date_pattern, date)):
            dates.append(date)
    return dates
