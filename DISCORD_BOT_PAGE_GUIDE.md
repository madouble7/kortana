# 🤖 Discord Bot Page Guide - Exact Steps

You're looking at the perfect page! Here's exactly what to do on this screen:

## 📍 You Are Here
```
Applications → kor'tana → Bot
```

---

## ✅ Step 1: Copy Your Bot Token (THIS PAGE)

**On the page you're viewing:**

1. Look for the **TOKEN** section
2. Click the **copy icon** 🔀 next to your token
3. Your token is now copied to clipboard

**What it looks like:**
```
Token
For security purposes, tokens can only be viewed once...
[Copy Icon] Click here to copy
```

✓ Token is copied


## ✅ Step 2: Enable Message Content Intent (THIS PAGE)

**Scroll down to "Privileged Gateway Intents"**

Look for three important intents:

### ☑️ Message Content Intent - REQUIRED
- Status: Should be **ENABLED** (toggled ON)
- Why: Needed for bot to read message content
- If it's OFF: Click toggle to turn ON

### ☑️ Server Members Intent - RECOMMENDED
- Status: Should be **ENABLED** (toggled ON)  
- Why: Helps with user context and permissions

### ☑️ Presence Intent - OPTIONAL
- Status: Can be ON or OFF
- Why: For tracking user online status

**Expected view:**
```
Privileged Gateway Intents
Message Content Intent [TOGGLE: ON] ✓
Server Members Intent [TOGGLE: ON] ✓
Presence Intent [TOGGLE: ON or OFF]
```

✓ Intents are configured


## ✅ Step 3: Check Authorization Settings (THIS PAGE)

**Look for "Authorization Flow" section:**

### ☑️ Public Bot - SHOULD BE ON
- This checkbox should be **CHECKED**
- Allows anyone to add bot to servers
- Status: ☑️ PUBLIC BOT

### ☑️ Requires OAuth2 Code Grant - CAN BE OFF
- Leave this **UNCHECKED** for now
- Status: ☐ (empty)

**Expected view:**
```
Authorization Flow
☑️ Public Bot (checked)
☐ Requires OAuth2 Code Grant (unchecked)
```

✓ Authorization is set correctly


## ✅ Step 4: Bot Permissions (THIS PAGE - DO LATER)

Don't worry about this now. For basic chat bot:
- **Send Messages** ✓
- **Read Message History** ✓
- **Embed Links** ✓
- **Use Slash Commands** ✓

These are basic and usually already set!

---

## 📋 Checklist Before Leaving This Page

- [ ] I copied my bot token (have it in clipboard)
- [ ] Message Content Intent is **ENABLED** (ON)
- [ ] Public Bot is **CHECKED** (ON)
- [ ] Bot username shows "kor'tana"
- [ ] Install count shows "1 Server"

---

## 🎯 Next: Run Setup Script

Once you've done the above on this page:

**Go to your terminal/command prompt and run:**

```bash
python setup_discord_bot_quick.py
```

**The script will:**
1. Ask you to paste your bot token
2. Create .env file with configuration
3. Validate everything works

That's it! ✅

---

## 🚀 Quick Reference

| Setting | Should Be |
|---------|-----------|
| Public Bot | ☑️ ON |
| Message Content Intent | ☑️ ON |
| Server Members Intent | ☑️ ON |
| Presence Intent | ☑️ ON or OFF |
| Bot Token | Copied! |

---

## ❓ Troubleshooting This Page

### Issue: Can't find Token section
**Solution:** Scroll down on the Bot page - it's below the Username

### Issue: Token is grayed out
**Solution:** Click "Reset Token" button to generate a new one

### Issue: Intents are grayed out
**Solution:** You might need to verify your bot first (only needed if 100+ servers)

### Issue: Can't copy token
**Solution:** Right-click on the token and select Copy

---

## ✅ When Done With This Page

You should have:
1. ✅ Bot token copied to clipboard
2. ✅ Message Content Intent enabled
3. ✅ Public Bot toggled on
4. ✅ Ready to run setup script

**Next:** `python setup_discord_bot_quick.py`

---

## 📸 Visual Guide

The page layout looks like:

```
┌─────────────────────────────────────────────┐
│ Applications > kor'tana > Bot               │
├─────────────────────────────────────────────┤
│                                             │
│ Icon & Banner Upload Section          │
│ (not needed for basic bot)                  │
│                                             │
│ Username: kor'tana                    │
│ (1479 discriminator)                       │
│                                             │
│ TOKEN [Copy 🔀]  ← CLICK THIS!      │
│                                             │
│ Authorization Flow:                         │
│   ☑️ Public Bot                             │
│   ☐ Requires OAuth2 Code Grant             │
│                                             │
│ Privileged Gateway Intents:                 │
│   ☑️ Message Content Intent   ← ENABLE!    │
│   ☑️ Server Members Intent    ← ENABLE!    │
│   ☑️ Presence Intent          ← ENABLE!    │
│                                             │
│ Bot Permissions: (skip for now)            │
│                                             │
└─────────────────────────────────────────────┘
```

---

That's all you need on this page! Once done:

1. Minimize/keep open Discord portal
2. Open terminal
3. Run: `python setup_discord_bot_quick.py`
4. Paste your token when asked
5. Done! ✅

