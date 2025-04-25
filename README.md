# money_parser

This is a project to parse futures statements.

# Run

```
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python parser.py
```

# Input

A Charles Schwab Futures daily statement named `document.pdf` should exist in the same directory.

# Output

A JSON document `parsed_statement.json` is output with the parsed contents.