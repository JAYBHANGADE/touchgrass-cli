# touchgrass

An offline CLI that gets you off the screen. Tell it how much time you have
and how you feel, and it builds you a concrete plan to go outside - generated
by an **open-weight model running locally on your machine** through
[Ollama](https://ollama.com). No cloud APIs, no accounts, no tracking. The
plan it gives you never leaves your laptop, which is kind of the point.

## Why

Every "wellness" app I tried solved screen time with... more screen time:
streaks, feeds, badges, notifications. `touchgrass` takes the opposite
approach - you type one line, you get a plan, and the last thing it tells
you is to close the terminal.

## Install

```bash
# 1. Install Ollama (https://ollama.com) and pull a small open-weight model
ollama pull qwen2.5:0.5b

# 2. Clone this repo - zero Python dependencies, stdlib only
git clone https://github.com/gajit9147-dev/touchgrass-cli.git
cd touchgrass-cli
```

## Use

```bash
python3 touchgrass.py "i have 45 minutes and low energy"
python3 touchgrass.py "full of energy, 1 hour before it gets dark"
python3 touchgrass.py --file examples/tired_evening.txt
python3 touchgrass.py --offline "20 min break"   # no model needed

# Input validation examples

python3 touchgrass.py
python3 touchgrass.py ""
python3 touchgrass.py "hello"
```

Example output:

```
*** Slow loop around the block ***

  1. Step outside and walk slowly around the block (15 min, phone stays in your pocket)
  2. Find a tree, bench, or stairs to sit on and just watch the world for 5 minutes
  3. Head back the long way and notice three things you never looked at before

why: Movement and daylight reset your attention better than any feed can.

~30 minutes away from the screen (local model (qwen2.5:0.5b via Ollama)).
Now close this terminal and go.
```

## How it works

- **Local inference**: your message goes to an open-weight model
  (default `qwen2.5:0.5b`, ~400 MB) served by Ollama on
  `localhost:11434`. Works on a train, in a park, in a village with no
  signal - anywhere your laptop is.
- **Graceful degradation**: if the model server is down or returns
  garbage, a built-in heuristic planner still gives you a real plan
  (`--offline` forces this). The tool never leaves you stuck at a prompt.
- **Stdlib only**: plain Python 3, no `pip install` anything. Reads from
  an argument, a file, or stdin.

## Model notes

Runs fine on tiny models you can pull in minutes. Tested with
`qwen2.5:0.5b` and `smollm2:135m`; bigger local models
(`qwen2.5:3b`, `llama3.2`) give noticeably nicer plans if you have the RAM.
Swap with `--model <name>`.

## License

MIT
