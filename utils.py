def format_time(ms):
    if ms <= 0:
        return "00:00"
    s = int(ms / 1000)
    return f"{s//60:02}:{s%60:02}"
