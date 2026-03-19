# Remove OpenAI API Key from Git History

Your push was rejected because GitHub detected an API key in your commit history.

## Step 1: Revoke the exposed key (do this first)

1. Go to https://platform.openai.com/api-keys
2. Revoke the compromised key
3. Create a new key for future use

## Step 2: Remove the key from git history

### Option A: Using git-filter-repo (recommended)

```bash
# Install git-filter-repo
pip install git-filter-repo

# Run from project root
cd /Users/sritampatnaik/Masters/NUS-ISS\ Sritam/NUS-ISS\ Sem\ 3/Sign-Lang-v2
git filter-repo --replace-text .git-filter-repo-replacements --force
```

### Option B: Using git filter-branch (no extra install needed)

```bash
cd "/Users/sritampatnaik/Masters/NUS-ISS Sritam/NUS-ISS Sem 3/Sign-Lang-v2"

# Replace API key pattern with empty string in all commits (macOS compatible)
git filter-branch -f --tree-filter '
  find . -name "*.ipynb" -type f | while read f; do
    sed -i "" "s/sk-proj-[a-zA-Z0-9_-]\{50,\}//g" "$f" 2>/dev/null || true
  done
' HEAD
```

## Step 3: Force push (rewrites remote history)

```bash
git push --force origin main
```

**Warning:** Force push rewrites history. If others have cloned the repo, they'll need to re-clone or reset their local copy.

## Step 4: Use environment variable going forward

In your notebook, use:
```python
import os
# Set in terminal before running: export OPENAI_API_KEY="your-new-key"
# Or use: os.environ["OPENAI_API_KEY"] = ""  # Leave empty - set via terminal/env
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("Set OPENAI_API_KEY environment variable")
```

Never commit API keys. Use `.env` (add to .gitignore) or environment variables.
