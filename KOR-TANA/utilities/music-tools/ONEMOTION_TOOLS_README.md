# 🎹 OneMotion Helper Tools

Complete toolkit for creating OneMotion Chord Player JSON files!

---

## 🚀 Quick Start

### Option 1: Interactive Builder (Recommended!)

```bash
cd C:\kordtana_starter_pack
python onemotion_builder.py
```

**What it does:**

- Walks you through step-by-step
- Asks for song name, key, scale, tempo
- Builds chord progression interactively
- Automatically creates valid JSON
- No need to remember field names!

**Perfect for:** First-time users, quick compositions

---

### Option 2: Copy & Modify Template

```bash
# Copy the template
cp onemotion_template.json my_song.json

# Edit in VS Code
code my_song.json

# Validate when done
python onemotion_validator.py my_song.json
```

**Perfect for:** When you know what you want, faster workflow

---

### Option 3: AI-Powered Harmony Studio

```bash
python harmony_studio.py
```

**What it does:**

- Uses AI to generate advanced chord progressions
- 8 harmonic styles (jazz, neo-soul, modal interchange, etc.)
- 5 melodic approaches
- Creates musically sophisticated compositions
- Costs ~$0.0025 per composition

**Perfect for:** Complex compositions, learning music theory, experimentation

---

## 🛠️ Tools Included

### `onemotion_builder.py`

Interactive builder - easiest way to create JSONs

### `onemotion_validator.py`

Checks your JSON for errors

```bash
python onemotion_validator.py your_file.json
```

### `harmony_studio.py`

AI-powered advanced composition tool

### `onemotion_template.json`

Valid template with all required fields

---

## 📚 Documentation

### `ONEMOTION_QUICKREF.md`

- Chord types reference
- Scale types
- Common patterns
- Troubleshooting tips

### `ONEMOTION_GUIDE.md`

- Complete field reference
- Format differences from Kordtana.card
- Validation checklist
- Common mistakes

---

## 🎯 Workflow Examples

### Create Simple Song

1. Run builder: `python onemotion_builder.py`
2. Answer prompts
3. Done! File is created and validated

### Create Complex Harmonic Piece

1. Run harmony studio: `python harmony_studio.py`
2. Select source composition
3. Choose harmonic style (e.g., "jazz extensions")
4. Choose melodic approach
5. AI generates sophisticated progression
6. Load in OneMotion Chord Player

### Fix Existing JSON

1. Validate: `python onemotion_validator.py broken.json`
2. Read error messages
3. Fix issues in VS Code
4. Validate again until clean

---

## ⚠️ Common Issues & Solutions

### "parallellScaleChords is not defined"

**Fix:** Use `parallellScaleChords` with double-l (it's intentional!)

### "Invalid JSON file"

**Fix:** Run `python onemotion_validator.py file.json` for specific errors

### "Chords not playing"

**Check:**

- `sequence` has valid chord types (`min`, `maj`, etc.)
- `rootPos` is between 0-11
- `length` is positive number

### "Effects not working"

**Check:**

- `effectType` is at root level (not nested)
- `effectEcho.active` is `true`
- All effectEcho fields present

---

## 🎼 Example Files

Check these working examples in this folder:

- `onemotion_template.json` — Basic valid template
- `over_trap_remix.json` — Trap-style remix
- `over_house_remix.json` — House-style remix
- `root_onemotion.json` — Simple composition

---

## 💡 Pro Tips

1. **Start with the builder** — Get comfortable with the format first
2. **Validate often** — Run validator after every edit
3. **Keep template open** — Reference for field structure
4. **Use harmony studio** — Learn music theory through AI examples
5. **Copy working files** — Modify existing JSONs for similar styles

---

## 🆘 Need Help?

1. Check `ONEMOTION_QUICKREF.md` for quick answers
2. Run validator for specific error messages
3. Compare your JSON with `onemotion_template.json`
4. Check `ONEMOTION_GUIDE.md` for complete field reference

---

## 📝 Validation Checklist

Before loading in OneMotion Chord Player:

- [ ] Run `python onemotion_validator.py your_file.json`
- [ ] All errors fixed (❌ marks)
- [ ] Warnings reviewed (⚠️ marks)
- [ ] File name descriptive
- [ ] Song name filled in
- [ ] Key and scale correct

---

**Ready to create amazing chord progressions! 🎊**
