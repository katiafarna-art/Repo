import sys
from typing import Any
from datetime import datetime, timedelta

def _get_args(_array: Any) -> Any:
    """
    Retrieve the type arguments of a generic type depending on Python version.

    :param _array: The generic type to extract arguments from.
    :type _array: Any
    :return: Type arguments in Python 3.7+ or values in earlier versions.
    :rtype: Any
    """
    if sys.version_info[:2] < (3, 7):
        return _array.__values__
    else:
        return _array.__args__
    
def is_leap_year(year: int) -> bool:
    """
    Determine if a given year is a leap year.

    A leap year is divisible by 4 but not by 100, unless it is divisible by 400.

    :param year: The year to check.
    :type year: int
    :return: True if the year is a leap year, False otherwise.
    :rtype: bool
    """
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

   
def has_leap_day_between_dates(date1: datetime, date2: datetime) -> bool:
    """
    Check if there is a leap day (February 29) between two dates.

    :param date1: The start date.
    :type date1: datetime
    :param date2: The end date.
    :type date2: datetime
    :return: True if a leap day exists between the two dates, False otherwise.
    :rtype: bool
    """
    current_date = date1

    while current_date <= date2:
        if current_date.day == 29 and current_date.month == 2 and is_leap_year(current_date.year):
            return True

        # Aggiungi un giorno alla data corrente
        current_date += timedelta(days=1)

    return False