# jev-dev

A small CLI for asking [TypeSafe](https://docs.typesafe.ai)'s Jev model a typed question: yes/no (`noul`), pick-one (`choice`), or graded (`score`).

## Setup

1. Install [uv](https://docs.astral.sh/uv/) and Python 3.13+.
2. From this directory:

   ```bash
   uv sync
   ```

3. Put your TypeSafe API key in the environment, or in a `.env` file next to `jev.py`:

   ```bash
   TYPESAFE_API_KEY=your_key_here
   ```

   Create a key at [console.typesafe.ai](https://console.typesafe.ai).

`./jev.py` uses `uv run`, so you can call it directly after that.

## Usage

```bash
./jev.py -m <noul|choice|score> -q "<question>" [-s "" | -s /path/to/file] [--choices a,b,c]
```

| Flag | Meaning |
| --- | --- |
| `-m` / `--mode` | Question type: `noul`, `choice` (`choices` also works), or `score` |
| `-q` / `--query` | The question to ask |
| `-s` / `--state` / `-i` | State: an empty string, or a path to a text file |
| `--choices` | Required for `choice` (option labels) and `score` (ordered levels), comma-separated |

Answers print as JSON.

### Noul

Yes/no. Returns a probability from 0 (no) to 1 (yes). `--choices` is not used.

```bash
./jev.py -m noul -q "Is the sky typically blue during a clear day?" -s ""
```

```bash
./jev.py -m noul -q "Does the customer request a refund?" -s ./ticket.txt
```

### Choice

Pick one option from `--choices`.

```bash
./jev.py -m choice --choices calm,frustrated,angry -q "What is the customer's tone?" -s ./ticket.txt
```

`-i` and `--state` are the same as `-s`:

```bash
./jev.py -m choice --choices billing,technical,sales -q "Which team should handle this?" -i ./ticket.txt
```

### Score

Rate along ordered levels in `--choices` (lowest first).

```bash
./jev.py -m score --choices "can wait,this week,today" -q "How urgent is this ticket?" -s ./ticket.txt
```

## State

TypeSafe evaluates text `state` against the question. This script does not upload files: it reads a local text file and sends the contents.

- `-s ""` — no extra context; the question stands alone
- `-s ./ticket.txt` — read that file first, then send it as state

The file should be text. Images, PDFs, and other binaries are not supported.
