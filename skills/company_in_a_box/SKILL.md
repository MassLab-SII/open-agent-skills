---
name: notion-goals-restructure
description: Restructures the Current Goals section on the Company In A Box page by adding a new goal and converting all goals to toggleable headings with descriptions inside.
---

# Goals Restructure Skill

This skill restructures the Current Goals section on the Company In A Box page according to specific requirements.

## Basic Usage

```bash
python3 skills/company_in_a_box/goals_restructure.py
```

**This will automatically:**
1. Find the "Company In A Box" page
2. Locate the "Current Goals" section
3. Convert all four goal headings to toggleable headings
4. Move all descriptions inside the toggles as child blocks
5. Add a new goal: "🔄 Digital Transformation Initiative"
6. Preserve all content and formatting


## Task Details

The skill performs the following restructuring:

### 1. **Existing Goals to Convert to Toggles**
- ⚙️ Expand Operations to LATAM
- 🛠️ Push for Enterprise
- 🩶 Boost Employee Engagement

### 2. **New Goal to Add**
- 🔄 Digital Transformation Initiative

### 3. **Modifications Made**
- Each goal heading becomes a toggleable heading
- All descriptions and paragraphs move inside the toggle as child blocks
- All content and order is preserved

## Quick Start

**Simply run:**
```bash
python3 skills/company_in_a_box/goals_restructure.py
```

That's it! The skill will:
- Automatically find your Company In A Box page
- Restructure the Current Goals section
- Add the new goal heading
- Convert all goals to toggles
- Move descriptions inside

No configuration needed!

## Expected Result

The "Current Goals" section will have:
- 4 toggleable goal headings
- Each toggle containing its corresponding description
- Clean, organized layout with collapsible content
