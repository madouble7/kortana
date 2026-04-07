# ⚡ KOR'TANA AUTONOMY QUICK START

**TL;DR**: Run ONE command. KOR'TANA handles everything else.

---

## 🚀 DEPLOY IN 15 MINUTES

### The Command

```powershell
cd c:\KOR-TANA\kortana
python autonomous_execution.py --all
```

### What Happens

1. KOR'TANA asks for GitHub token (you paste it)
2. KOR'TANA asks for Gemini API key (you paste it)
3. KOR'TANA does EVERYTHING else automatically
4. ✅ Server running at <http://localhost:8000>

### Time Breakdown

```
Your work:     10 min (create 2 credentials)
Automation:     5 min (KOR'TANA does the rest)
─────────────────────────────────
Total:         15 min to live
```

---

## 🔐 WHAT YOU NEED TO PROVIDE

### 1. GitHub Token (5 min)

```
Go to: https://github.com/settings/tokens
Click: Generate new token
Name: KOR-TANA-PRODUCTION
Scopes: repo, workflow, admin:repo_hook
Copy token, paste when asked
```

### 2. Gemini API Key (5 min)

```
Go to: https://makersuite.google.com/app/apikey
Click: Create API Key
Copy key, paste when asked
```

---

## 📋 WHAT KOR'TANA DOES AUTOMATICALLY

✅ Create PostgreSQL database
✅ Create .env configuration file
✅ Run database migrations
✅ Install Python dependencies
✅ Start the server
✅ Verify everything works
✅ Log all actions
✅ Handle errors automatically

**Zero approval needed** for any of these.

---

## ✨ SUCCESS LOOKS LIKE

```
✅ All steps completed
✅ Server running at http://localhost:8000
✅ API docs at http://localhost:8000/docs
✅ Database created
✅ Health checks passing

🎉 You're done!
```

---

## 🆘 SOMETHING WENT WRONG?

### Port 8000 already in use?

```powershell
python autonomous_execution.py --start-server --port 8001
```

### Database already exists?

```
That's OK! KOR'TANA detects it and continues.
```

### Migration failed?

```powershell
alembic downgrade base
alembic upgrade head
```

### Need to redo everything?

```powershell
python autonomous_execution.py --all
```

(Safe to rerun - all steps are idempotent)

---

## 📖 WANT TO LEARN MORE?

| Need | Read This |
|------|-----------|
| Simple instructions | SCAFFOLDED_HO_STEPS.md |
| How autonomy works | KOR_TANA_AUTONOMOUS_PROTOCOL.md |
| Integration details | AUTONOMY_CORE_INTEGRATION.md |
| Full reference | AUTONOMY_IMPLEMENTATION_COMPLETE.md |

---

## 🎯 RIGHT NOW

1. **Run this command:**

   ```powershell
   cd c:\KOR-TANA\kortana
   python autonomous_execution.py --all
   ```

2. **When asked:**
   - Create GitHub token (5 min)
   - Create Gemini API key (5 min)
   - Paste when prompted

3. **Then:** Let KOR'TANA finish (5 min)

4. **Done:** <http://localhost:8000> 🎉

---

## 💾 FILES CREATED

```
SCAFFOLDED_HO_STEPS.md ................. Detailed instructions
KOR_TANA_AUTONOMOUS_PROTOCOL.md ....... Technical spec
AUTONOMY_CORE_INTEGRATION.md ........... Integration guide
autonomous_execution.py ............... Execution engine
AUTONOMY_EXECUTION.log ................ Generated on run
AUTONOMY_IMPLEMENTATION_COMPLETE.md ... Full documentation
```

---

## ⚡ THE AUTONOMY PROMISE

> **KOR'TANA executes all automatable steps without your approval. You only provide credentials. Everything else happens automatically.**

---

**Status**: 🟢 Ready
**Next**: Run `python autonomous_execution.py --all`
**Time**: ~15 minutes
