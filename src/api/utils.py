def records(df):
    """DataFrame -> list of JSON-safe dicts.

    df.where(df.notna(), None) alone doesn't work for numeric-dtype
    columns: assigning None into a float64 column gets silently coerced
    right back to NaN, which json.dumps then rejects. Casting to object
    dtype first makes None actually stick.
    """
    if df.empty:
        return []
    return df.astype(object).where(df.notna(), None).to_dict("records")
