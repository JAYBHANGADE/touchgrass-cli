#!/usr/bin/env python3
"""touchgrass - an offline CLI that gets you off the screen.

Tell it how much time you have and how you feel, and a local open-weight
model (through Ollama) builds you a concrete plan to go touch grass.
No cloud APIs, no accounts, no tracking. Your plans never leave your machine.
"""
import argparse, json, re, sys, urllib.request, urllib.error

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:0.5b"

PROMPT = """You turn screen time into outside time. Given a person's free time
and energy, you invent a concrete mini-adventure away from all screens.

Example input: "i have 45 minutes and low energy"
Example answer:
{"plan_title": "Chai and the long way home", "steps": ["Walk to the nearest chai stall or corner shop without your phone (10 min)", "Drink it standing outside, watching the street like a movie (10 min)", "Walk back a route you have never taken and count three things you never noticed (25 min)"], "why_it_works": "A small errand outside beats another scroll hole and you are home before dinner.", "screen_minutes_saved": 45}

Now do the same for this person: "{message}"

Reply with ONLY the JSON object, same keys as the example. Rules: steps must
be offline, free, doable alone right now, fit the available time, and be
specific (name real things: stairs, trees, chai stall, rooftop, park gate)."""


TIME_WORDS = [
    (r"half an? hour", lambda m: 30),
    (r"an?\s+hour", lambda m: 60),
    (r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)(?:\s*(?:and\s*)?(\d+)\s*(?:minutes?|mins?))?",
     lambda m: round(float(m.group(1)) * 60) + int(m.group(2) or 0)),
    (r"(\d+)\s*(?:minutes?|mins?)", lambda m: int(m.group(1))),
]
ENERGY_WORDS = {
    "low": ["tired", "exhausted", "low energy", "lazy", "sleepy", "drained", "burnt"],
    "high": ["energetic", "pumped", "full of energy", "fresh", "restless"],
}


def extract_minutes(text):
    for pat, conv in TIME_WORDS:
        m = re.search(pat, text, re.I)
        if m:
            return conv(m)
    return None


def extract_energy(text):
    t = text.lower()
    for level, words in ENERGY_WORDS.items():
        if any(w in t for w in words):
            return level
    return "medium"


def offline_plan(minutes, energy):
    """Heuristic fallback: no model needed, still no screen."""
    minutes = max(minutes or 30, 10)
    if energy == "low":
        steps = [
            f"Step outside and walk slowly around the block ({min(minutes, 15)} min, phone stays in your pocket)",
            "Find a tree, bench, or stairs to sit on and just watch the world for 5 minutes",
            "Head back the long way and notice three things you never looked at before",
        ]
        title = "Slow loop around the block"
    elif energy == "high":
        steps = [
            f"Brisk walk or jog to the farthest point you can reach in {minutes // 2} minutes",
            "Do 3 sets of stairs, a hill sprint, or 20 push-ups in a park on the way",
            "Cool down walking back a route you have never taken before",
        ]
        title = "Out and back, the long way"
    else:
        steps = [
            f"Walk out for {minutes // 2} minutes in any direction - no headphones for the first 5",
            "Pick one spot (park, chai stall, rooftop) and stay there screen-free for 10 minutes",
            "Walk back and write down one thing you saw, on paper",
        ]
        title = "There and back again"
    return {
        "plan_title": title,
        "steps": steps,
        "why_it_works": "Movement and daylight reset your attention better than any feed can.",
        "screen_minutes_saved": minutes,
        "source": "offline heuristic (model unavailable)",
    }


def ask_model(model, message):
    body = json.dumps({
        "model": model,
        "prompt": PROMPT.replace("{message}", message.replace('"', "'")),
        "stream": False,
        "options": {"temperature": 0.4, "num_ctx": 2048, "num_predict": 800},
        "format": "json",
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            out = json.load(r)
    except urllib.error.URLError:
        return None
    text = out.get("response", "").strip()
    try:
        plan = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return None
        try:
            plan = json.loads(m.group(0))
        except json.JSONDecodeError:
            # truncated JSON: salvage the fields
            title = re.search(r'"plan_title"\s*:\s*"([^"]+)"', text)
            steps = re.findall(r'"([^"\n]{10,160})"', text)
            plan = {
                "plan_title": title.group(1) if title else "Get outside",
                "steps": [s for s in steps if s not in
                          ("plan_title", "steps", "why_it_works")][:3],
                "why_it_works": "",
                "screen_minutes_saved": 0,
            }
    if not isinstance(plan.get("steps"), list) or not plan["steps"]:
        return None
    plan["source"] = f"local model ({model} via Ollama)"
    return plan


def render(plan, minutes, energy):
    saved = plan.get("screen_minutes_saved") or minutes or 30
    print(f"\n*** {plan.get('plan_title', 'Get outside')} ***\n")
    for i, s in enumerate(plan["steps"], 1):
        print(f"  {i}. {s}")
    if plan.get("why_it_works"):
        print(f"\nwhy: {plan['why_it_works']}")
    print(f"\n~{saved} minutes away from the screen "
          f"({plan.get('source', 'unknown source')}).")
    print("Now close this terminal and go.\n")


def main():
    p = argparse.ArgumentParser(
        description="Offline CLI that plans your next screen-free break (Ollama-powered)")
    p.add_argument("message", nargs="?", help="how much time you have and how you feel")
    p.add_argument("--file", help="read the message from a text file")
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help=f"Ollama model to use (default: {DEFAULT_MODEL})")
    p.add_argument("--offline", action="store_true",
                   help="skip the model and use the built-in heuristic planner")
    args = p.parse_args()

    message = args.message
    if args.file:
        message = open(args.file).read().strip()
    if not message and not sys.stdin.isatty():
        message = sys.stdin.read().strip()
    if not message:
        p.error("tell me how much time you have, e.g. "
                'touchgrass "i have 45 minutes and low energy"')

    minutes = extract_minutes(message)
    energy = extract_energy(message)
    plan = None if args.offline else ask_model(args.model, message)
    if plan is None:
        plan = offline_plan(minutes, energy)
    render(plan, minutes, energy)


if __name__ == "__main__":
    main()
