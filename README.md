# Coding Agent (IEMS 490 Final Project)

The backbone we use is Gemini (`gemini-2.5-flash`), and out harness with the tools and skill calling is built out in agent.py.

## What it can do

- Read files
- Create / overwrite files (asks first)
- Run shell commands (asks first)
- Search for files by name pattern
- Dump the project structure (`ls -R`)
- Save notes to a memory file so context carries across steps

There's also a skill system for multi-step workflows you invoke by name.

## Setup

You need Python 3.10+ and a Gemini API key.

```bash
python -m venv venv
source venv/bin/activate        
pip install -r requirements.txt
```

Put your key in a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

## Running it

```bash
python agent.py
```

It'll prompt you for an instruction. Type whatever you want it to do, for example:

```
User Prompt: Add type hints to every function in utils.py
```

## Skills

Skills are reusable workflows. Each one is just a `.txt` file in `skills/` that holds the
instructions for a multi-step routine. To trigger one, put `/skillname` somewhere in your
prompt. The agent reads that file and follows it.

Two are included:

- `/codebase` — understand the project structure, find and read the relevant files, and write
  what it learns to `memory.txt` before starting the actual task.
- `/rewrite` — change the project to a different language by setting up a new folder, translating
  the files, testing, and documenting.

Adding a new skill is done by making a new `.txt` and putting it into `skills/`.

## Safety

Guardrails for the agent:

- **Writes** always ask for confirmation.
- **Shell commands** ask for confirmation. You can answer `a` to "always allow" a command
  (it gets saved to `allowed.txt`). Reads and searches don't
  prompt since they can't damage anything.
- A handful of obviously destructive commands (`rm`, `dd`, `mkfs`, `shutdown`, …) get a
  different warning before they'll run.

## Files

| File | What it is |
|------|-----------|
| `agent.py` | agent loop, tools, skill handler |
| `skills/` | skill definitions (one `.txt` per skill) |
| `memory.txt` | scratch memory the agent writes to and reads back |
| `allowed.txt` | shell commands you've whitelisted |
| `requirements.txt` | dependencies |
