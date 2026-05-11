REGISTERED_HANDLERS = set()


def register(name: str):
    if name in REGISTERED_HANDLERS:
        print(f"⚠️ DUPLICATE HANDLER DETECTED: {name}")
    else:
        REGISTERED_HANDLERS.add(name)
        print(f"✅ REGISTERED: {name}")