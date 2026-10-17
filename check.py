import json, os, time, urllib.request

TOPIC = os.environ["NTFY_TOPIC"]
ROUNDS = 5      # how many checks per run
WAIT = 60       # seconds between checks


def load(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def notify(msg):
    r = urllib.request.Request(
        f"https://ntfy.sh/{TOPIC}",
        data=msg.encode(),
        headers={"Title": "Price alert"},
    )
    urllib.request.urlopen(r, timeout=30)


def check_once():
    cfg = load("coins.json", [])
    state = load("state.json", {})
    ids = ",".join(c["id"] for c in cfg)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    req = urllib.request.Request(url, headers={"User-Agent": "price-alert"})
    prices = json.load(urllib.request.urlopen(req, timeout=30))

    for c in cfg:
        name = c["id"]
        p = prices.get(name, {}).get("usd")
        if p is None:
            print("no price for", name)
            continue
        print(name, p)
        for kind in ("above", "below"):
            if kind not in c:
                continue
            key = f"{name}-{kind}-{c[kind]}"
            hit = p > c[kind] if kind == "above" else p < c[kind]
            if hit and not state.get(key):
                notify(f"{name} is ${p} ({kind} {c[kind]})")
                state[key] = True
            elif not hit:
                state[key] = False

    json.dump(state, open("state.json", "w"))


for i in range(ROUNDS):
    try:
        check_once()
    except Exception as e:
        print("check failed:", e)
    if i < ROUNDS - 1:
        time.sleep(WAIT)
