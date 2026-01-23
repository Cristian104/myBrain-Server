import time

# Stores the timestamp of the last database change
# We start with the current time
last_change_ts = time.time()


def touch():
    """Updates the timestamp to now (signals a change happened)."""
    global last_change_ts
    last_change_ts = time.time()
