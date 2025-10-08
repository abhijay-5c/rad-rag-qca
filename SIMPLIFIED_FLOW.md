# Simplified Radiology Q&A Flow

## Current Problem:
- Questions showing as "screening_0", "screening_5" (not helpful)
- No actual question text displayed
- Hierarchical system is too complex

## Correct Flow Should Be:

### **Level 1: Category Screening**
**Question:** "Are there any abnormalities in the Airways?"
- **If NO** → Skip all airway questions, move to next category
- **If YES** → Ask specific airway questions

### **Level 2: Specific Questions (only if Level 1 = YES)**
1. "Is the trachea patent and normal in caliber?"
   - If YES → "Describe the size, location, and characteristics"
2. "Are there any bronchial abnormalities?"
   - If YES → "Describe stenosis, obstruction, or lesions"

### **Example for CT Chest:**

```
1. Category: Airways
   Q: Are there any abnormalities in the airways?
   A: YES
   
   → 1a. Is the trachea normal?
        A: YES → Details: "Trachea is narrowed at mid-level, 8mm diameter"
   
   → 1b. Are there bronchial abnormalities?
        A: NO
   
2. Category: Pleura
   Q: Are there any abnormalities in the pleura?
   A: YES
   
   → 2a. Is there pleural effusion?
        A: YES → Details: "Right pleural effusion, 200ml, simple density"
   
   → 2b. Is there pneumothorax?
        A: NO

3. Category: Lungs
   Q: Are there any abnormalities in the lungs?
   A: NO
   → Skip all lung questions

4. Category: Heart
   ...
```

## What We Need:

### Simple 2-Level System:
1. **Category Questions** (broad screening)
2. **Specific Questions** (only if category is positive)

### Question Format:
- **Category:** "Are there any abnormalities in [Airways/Pleura/Lungs/etc]?"
- **Specific:** Actual clinical findings questions

### This gives us:
- ✅ Efficient (skip negative categories)
- ✅ Comprehensive (detailed when needed)
- ✅ Clear question text
- ✅ Proper measurements/details
- ✅ Useful for report generation



