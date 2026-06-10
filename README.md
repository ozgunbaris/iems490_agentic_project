# Coding Agent (IEMS 490 Final Project)

A small command-line coding agent. You give it an instruction in plain English and it
plans out the steps, calls tools (read/write files, run shell commands, search), and
keeps going until the task is done. The model decides what to do; the harness around it
actually executes the calls and feeds the results back.

The backbone here is Gemini (`gemini-2.5-flash`), but the point of the project is the
harness, not the model — the loop, tools, and skills are all our own code.

## What it can do

- Read files
- Create / overwrite files (asks first)
- Run shell commands (asks first unless you've whitelisted the command)
- Search for files by name pattern
- Dump the project structure (`ls -R`)
- Save notes to a memory file so context carries across steps

There's also a skill system for multi-step workflows you invoke by name — see below.

## Setup

You need Python 3.10+ and a Gemini API key.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Put your key in a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

(The `.env` is gitignored, so it won't get committed.)

## Running it

```bash
python agent.py
```

It'll prompt you for an instruction. Type whatever you want it to do, for example:

```
User Prompt: Add type hints to every function in utils.py
```

From there it runs on its own. When it wants to write a file or run a shell command it
stops and asks for a `y/n`. The loop is capped at 10 steps so it can't spin forever.

## Skills

Skills are reusable workflows. Each one is just a `.txt` file in `skills/` that holds the
instructions for a multi-step routine. To trigger one, put `/skillname` somewhere in your
prompt. The agent reads that file and follows it.

Two are included:

- `/codebase` — walk the project structure, find and read the relevant files, and write
  what it learns to `memory.txt` before starting the actual task.
- `/rewrite` — port the project to a different language: set up a new folder, translate
  the files, test, and document.

Adding a new skill is just dropping another `.txt` into `skills/` — no code changes.

## Safety

The agent can touch your filesystem and run commands, so there are a couple of guardrails:

- **Writes** always ask for confirmation.
- **Shell commands** ask for confirmation. You can answer `a` to "always allow" a command
  (it gets saved to `allowed.txt` so you're not asked again). Reads and searches don't
  prompt since they can't damage anything.
- A handful of obviously destructive commands (`rm`, `dd`, `mkfs`, `shutdown`, …) get a
  louder warning before they'll run.

## Files

| File | What it is |
|------|-----------|
| `agent.py` | the whole thing — tools, skill loader, and the agent loop |
| `skills/` | skill definitions (one `.txt` per skill) |
| `memory.txt` | scratch memory the agent writes to and reads back |
| `allowed.txt` | shell commands you've whitelisted |
| `requirements.txt` | dependencies |

## Notes / limitations

- The 10-step cap means very large tasks can run out of steps mid-way.
- "Always allow" matches on the command's first word, so it's coarse — `git` means all of
  `git`, not just `git status`.
- Skill detection looks for a literal `/name` token in the prompt.
