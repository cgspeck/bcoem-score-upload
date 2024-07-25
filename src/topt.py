import pyotp


def validate(v: str, base32secret: str, valid_minutes: int) -> bool:
    totp = pyotp.TOTP(base32secret)
    return totp.verify(v, valid_window=valid_minutes * 2)

if __name__ == "__main__":
    from os import environ
    import sys
    v = sys.argv[1]
    print(f"Validating {v}")
    print(validate(v, environ["TOPT_SECRET"], environ.get("TOPT_VALID_MINUTES", 10)))
