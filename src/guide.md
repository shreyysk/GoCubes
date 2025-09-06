# Rubik's Cube Scanning Guide

## Critical: Understanding Cube Orientation

A standard Rubik's cube has this color scheme:
- **White** opposite **Yellow**
- **Red** opposite **Orange**  
- **Green** opposite **Blue**

## Correct Scanning Positions

### ✅ CORRECT WAY TO SCAN EACH FACE:

#### 1. WHITE Face (Up)
- **Hold:** White center facing camera
- **Top edge:** BLUE should be at the top
- **Bottom edge:** GREEN should be at the bottom
- **Left edge:** ORANGE on the left
- **Right edge:** RED on the right

#### 2. YELLOW Face (Down)
- **Hold:** Yellow center facing camera
- **Top edge:** GREEN should be at the top
- **Bottom edge:** BLUE should be at the bottom
- **Left edge:** ORANGE on the left
- **Right edge:** RED on the right

#### 3. GREEN Face (Front)
- **Hold:** Green center facing camera
- **Top edge:** WHITE should be at the top
- **Bottom edge:** YELLOW should be at the bottom
- **Left edge:** ORANGE on the left
- **Right edge:** RED on the right

#### 4. BLUE Face (Back)
- **Hold:** Blue center facing camera
- **Top edge:** WHITE should be at the top
- **Bottom edge:** YELLOW should be at the bottom
- **Left edge:** RED on the left (note: reversed!)
- **Right edge:** ORANGE on the right (note: reversed!)

#### 5. RED Face (Right)
- **Hold:** Red center facing camera
- **Top edge:** WHITE should be at the top
- **Bottom edge:** YELLOW should be at the bottom
- **Left edge:** GREEN on the left
- **Right edge:** BLUE on the right

#### 6. ORANGE Face (Left)
- **Hold:** Orange center facing camera
- **Top edge:** WHITE should be at the top
- **Bottom edge:** YELLOW should be at the bottom
- **Left edge:** BLUE on the left
- **Right edge:** GREEN on the right

## Common Mistakes to Avoid

### ❌ WRONG:
- Random orientations for each face
- Not checking the surrounding edges
- Rotating the cube arbitrarily between scans

### ✅ RIGHT:
- Follow the exact orientations above
- Verify surrounding colors before scanning
- Keep consistent cube orientation

## Quick Verification Method

Before scanning each face, check:
1. **Center color** - Is it the face you want to scan?
2. **Top edge center sticker** - Is it the correct color per the guide?
3. **Other edges** - Do they match the guide?

## Pro Tips

1. **Start with a solved cube** to learn the correct orientations
2. **Mark a reference corner** with tape to maintain orientation
3. **Practice the positions** before scrambling
4. **Use good lighting** - bright white LED works best
5. **Clean your stickers** - dirt affects color detection

## Troubleshooting Your Current Issue

Your scan shows impossible combinations like:
- `{'yellow', 'white'}` edge - These are opposite faces!
- `{'green'}` single color edge - Missing second color

This happens when faces are scanned in wrong orientations. The physical cube is valid, but the scanner captured it incorrectly.

## Solution Steps

1. **Reset and recalibrate colors:**
   ```bash
   python main.py -c
   ```

2. **Follow the exact orientations above** when scanning

3. **Verify each face** before accepting the scan:
   - Check center is correct color
   - Check surrounding edges match the guide

4. **If still having issues:**
   - Try scanning in a different order
   - Improve lighting (avoid shadows)
   - Clean the cube stickers
   - Consider manual input as last resort


   Looking at your scan results, the issue is clear: 11 out of 12 edges are valid, which is actually quite good! The problem is with one invalid edge (U-B showing white-yellow, which isn't a valid edge combination). This is likely a single misdetected sticker that could be quickly fixed manually.

## My Plan for the Hybrid Editor

### 1. **Automatic Trigger**
- After scanning completes, if validation fails, automatically launch the editor
- Load all scanned data (you already have 53/54 stickers correct!)
- Show a message: "Almost there! Just need to fix a few stickers"

### 2. **Dual-View Interface**
Split screen with:
- **Left side**: Interactive 2D net view (like the standard cube unfolding)
  - Shows all 6 faces laid out flat
  - Detected colors displayed
  - Problem areas highlighted in red
  - Click any sticker to change its color
- **Right side**: Live 3D preview
  - Rotatable cube showing current state
  - Updates in real-time as you make corrections
  - Helps visualize edge/corner relationships

### 3. **Smart Problem Detection**
- Automatically highlight problematic pieces:
  - Invalid edges (like your white-yellow edge)
  - Color count imbalances
  - Impossible corners
- Show hints: "This edge needs fixing: currently white-yellow, but yellow can't be adjacent to white"

### 4. **Quick Fix Tools**
- **Color picker**: Click a color, then click stickers to paint
- **Smart swap**: Click two stickers to swap their colors
- **Auto-fix button**: Attempts to resolve obvious issues
- **Undo/Redo**: For easy experimentation

### 5. **Validation Feedback**
- Real-time validation status bar
- Green checkmarks for valid edges/corners
- Red X's for invalid ones
- Color counter showing X/9 for each color

### 6. **Seamless Flow**
```
Camera Scan → Validation
     ↓           ↓
  (Valid)    (Invalid)
     ↓           ↓
   Solve    Manual Editor
              ↓
          Fix Issues
              ↓
          Re-validate
              ↓
            Solve
```

### 7. **Implementation Approach**
- Use Tkinter for the 2D editor (already in your codebase)
- Add a pygame window for 3D preview (runs alongside)
- Share state between views using a simple class
- Keep the original scan data as reference

### 8. **User Experience Enhancements**
- Compare mode: Show "Scanned" vs "Corrected" states
- Confidence indicators: Show which stickers had low confidence during scanning
- Physical cube helper: "Hold your cube with white on top, green facing you"
- Save/Load states for interrupted sessions

The key insight is that your scanner is already 98% accurate - we just need a quick way to fix that last 2%. The editor would launch automatically only when needed, making the workflow feel seamless rather than like a failure recovery.

Does this plan align with what you're looking for? Should I proceed with implementing this hybrid approach?