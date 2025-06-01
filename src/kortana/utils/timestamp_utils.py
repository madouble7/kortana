import datetime


def get_iso_timestamp():
    """
    Generates the current UTC date and time in ISO 8601 format.

    Returns:
        str: The current UTC date and time string in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
    """
    # Get the current UTC time
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    # Format as ISO 8601 string with 'Z' suffix for UTC
    iso_timestamp = now_utc.isoformat(timespec="seconds").replace("+00:00", "Z")
    return iso_timestamp


# Example usage (optional, could be added for testing if needed later)
# if __name__ == "__main__":
#     print(get_iso_timestamp())
