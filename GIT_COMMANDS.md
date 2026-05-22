# Git Commands for GitHub Push

## Step 1: Configure Git (if not done)
```bash
git config --global user.name "Your Name"
git config --global user.email "nachiket.kapure@spearhead.so"
```

## Step 2: Create New Branch
```bash
# Create and switch to new branch
git checkout -b feat/luxury-stylist-complete

# Or with more descriptive name
git checkout -b implementation/complete-system
```

## Step 3: Check Status
```bash
git status
```

**Expected output:**
```
On branch feat/luxury-stylist-complete
Changes not staged for commit:
  modified:   README.md
  new file:   .gitignore
  ...
```

## Step 4: Stage All Changes
```bash
# Stage specific files
git add README.md .gitignore requirements.txt

# Or stage everything (careful!)
git add .
```

## Step 5: Commit Changes
```bash
git commit -m "feat: Complete Luxury Stylist Concierge system

- Add comprehensive README with full documentation
- Create .gitignore with proper exclusions
- Update requirements with Groq and langchain-groq
- Implement Groq LLM integration for stylist notes
- Add query caching for token optimization
- Fix Stealth import and error handling

This completes the Quickeee Gen AI assignment with all requirements:
✅ Advanced scraping (Zara + Myntra, 100+ items)
✅ RAG with Vector DB (ChromaDB + embeddings)
✅ Agentic LLM workflow (Groq + fashion rules)
✅ Token optimization (caching + prompt optimization)
✅ FastAPI endpoint (POST /api/v1/style-me)
✅ Full documentation and deployment guides"
```

## Step 6: Push to GitHub
```bash
# First, ensure you have GitHub SSH key or personal token set up

# Push the branch
git push origin feat/luxury-stylist-complete

# Expected output:
# remote: Create a pull request for 'feat/luxury-stylist-complete' on GitHub
# To https://github.com/yourusername/luxury-stylist-concierge.git
#  * [new branch]      feat/luxury-stylist-complete -> feat/luxury-stylist-complete
```

## Step 7: Create Pull Request on GitHub

```bash
# Option 1: Using GitHub CLI (if installed)
gh pr create --title "Complete Luxury Stylist Concierge System" \
  --body "Completes all Quickeee Gen AI assignment requirements:
  
✅ Advanced scraping with 100+ items
✅ RAG pipeline with Vector DB
✅ Groq LLM integration
✅ Token optimization
✅ FastAPI backend
✅ Full documentation"

# Option 2: Manually on GitHub
# 1. Go to https://github.com/yourusername/luxury-stylist-concierge
# 2. Click "Compare & pull request" button
# 3. Fill in title and description
# 4. Click "Create pull request"
```

## Step 8: Merge to Main (After Review)

```bash
# Switch to main
git checkout main

# Pull latest changes
git pull origin main

# Merge the feature branch
git merge feat/luxury-stylist-complete

# Push merged changes
git push origin main
```

## Complete Workflow Script

Run this complete sequence:

```bash
#!/bin/bash

echo "🚀 Starting git workflow..."

# Create branch
git checkout -b feat/luxury-stylist-complete
echo "✅ Branch created"

# Stage changes
git add .
echo "✅ Changes staged"

# Commit
git commit -m "feat: Complete Luxury Stylist Concierge system

- Comprehensive README with full documentation
- .gitignore with proper exclusions
- Groq LLM integration
- Query caching system
- All assignment requirements met"
echo "✅ Changes committed"

# Push
git push origin feat/luxury-stylist-complete
echo "✅ Pushed to origin"

echo ""
echo "🎉 Workflow complete!"
echo ""
echo "Next steps:"
echo "1. Visit: https://github.com/yourusername/luxury-stylist-concierge"
echo "2. Create a pull request"
echo "3. Request code review"
echo "4. Merge to main when approved"
```

## If You Get Stuck

**Error: "Permission denied (publickey)"**
```bash
# Set up SSH keys
ssh-keygen -t ed25519 -C "nachiket.kapure@spearhead.so"
# Add to https://github.com/settings/keys
```

**Error: "fatal: 'origin' does not appear to be a git repository"**
```bash
# Add remote
git remote add origin https://github.com/yourusername/luxury-stylist-concierge.git
```

**Want to see what will be committed?**
```bash
git diff --cached
```

**Want to unstage something?**
```bash
git reset HEAD filename.txt
```

**Want to undo last commit?**
```bash
git reset --soft HEAD~1  # Keep changes
git reset --hard HEAD~1  # Discard changes
```
