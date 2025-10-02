from datetime import datetime, timedelta, date
import logging

def parse_time_expression(time_expr: str) -> date:
    """
    Parse time expressions like '30d+', '1h' into date
    Args:
        time_expr: String representing time since now (e.g., '30d+', '1h', '2w')
    Returns:
        date object representing the date (without time)
    """
    try:
        # Remove any '+' suffix
        time_expr = time_expr.strip().rstrip('+')
        
        # Extract number and unit
        # Validate input has both number and unit
        digits = ''.join(filter(str.isdigit, time_expr))
        letters = ''.join(filter(str.isalpha, time_expr.lower()))

        if not digits or not letters:
            logging.warning(f"Invalid time expression '{time_expr}', missing number or unit")
            return today

        # Extract number and unit
        number = int(digits)
        unit = letters        
        today = date.today()
        
        # For hours and minutes, return today
        if unit in ['h', 'm']:
            return today
            
        # Convert based on unit
        if unit == 'd':  # days
            return today - timedelta(days=number)
        elif unit == 'w':  # weeks
            return today - timedelta(weeks=number)
        elif unit == 'mo':  # months (approximate)
            return today - timedelta(days=number * 30)
        elif unit == 'y':  # years (approximate)
            return today - timedelta(days=number * 365)
        else:
            logging.warning(f"Unknown time unit in '{time_expr}', defaulting to current date")
            return today
            
    except Exception as e:
        logging.error(f"Error parsing time expression '{time_expr}': {e}")
        return date.today()