import time


def convert_date(date: str) -> str:
    """
    Convertit la date au format JJ/MM/AAAA
    """
    # Convert date like August 5, 2022
    if "," in date:
        return time.strftime("%d/%m/%Y", time.strptime(date, "%B %d, %Y"))
    if "-" in date:
        return time.strftime("%d/%m/%Y", time.strptime(date, "%Y-%m-%d"))
    if "/" in date:
        return date
    raise ValueError(f"Date {date} not recognized")


def two_decimals(number: float) -> float:
    """
    Round a number to two decimals
    """
    return round(number, 2)
