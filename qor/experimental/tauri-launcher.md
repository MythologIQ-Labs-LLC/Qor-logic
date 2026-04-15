# Tauri Launcher Skill

Manages Tauri development server startup, window detection, and fallback strategies.

## Purpose
Automates the complex Tauri dev server launch process and handles common failure modes without manual intervention.

## Usage
When user wants to:
- Start Tauri development mode
- Test FirstRunSetup or any COREFORGE feature
- Debug why Tauri window won't open

## What This Skill Does

### 1. Clean Process Management
**Problem Learned:** Multiple background processes cause port conflicts
```bash
# Kill all existing Tauri/webpack/Python processes
pkill -f "tauri dev" || true
pkill -f "webpack" || true
pkill -f "python.*http.server" || true

# Wait for ports to release
sleep 2
```

### 2. Port Verification
**Problem Learned:** Port mismatch blocks Tauri window
```bash
# Read expected port from tauri.conf.json
EXPECTED_PORT=$(grep -A1 "devPath" src-tauri/tauri.conf.json | grep -oP '(?<=:)\d+' || echo "3000")

# Verify webpack will use that port
# Check package.json scripts or webpack config
# If mismatch detected, update tauri.conf.json
```

### 3. Staged Launch
```bash
# Stage 1: Start webpack dev server
npm run dev:react &
WEBPACK_PID=$!

# Stage 2: Wait for webpack to be ready
echo "Waiting for webpack dev server..."
for i in {1..30}; do
  if curl -s http://localhost:$EXPECTED_PORT > /dev/null 2>&1; then
    echo "✅ Webpack ready on port $EXPECTED_PORT"
    break
  fi
  sleep 1
done

# Stage 3: Start Tauri (which will use the ready webpack server)
npm run tauri:dev &
TAURI_PID=$!
```

### 4. Window Detection
**Problem Learned:** Tauri compiles successfully but window doesn't appear
```bash
# Wait up to 60 seconds for Tauri window
echo "Waiting for Tauri window to open..."
for i in {1..60}; do
  # Check if Tauri process is running
  if ! ps -p $TAURI_PID > /dev/null 2>&1; then
    echo "❌ Tauri process died unexpectedly"
    exit 1
  fi

  # Check for window (platform-specific)
  if wmctrl -l | grep -i "coreforge" > /dev/null 2>&1; then
    echo "✅ Tauri window detected"
    break
  fi

  # On Windows: check for process with window
  if tasklist /FI "IMAGENAME eq hearthlink.exe" | grep -q "hearthlink.exe"; then
    echo "✅ Tauri app running"
    break
  fi

  sleep 1
done
```

### 5. Fallback Strategies

#### Fallback 1: Check Logs
```bash
# If window doesn't appear, check for errors
tail -50 ~/.local/share/hearthlink/logs/latest.log 2>/dev/null ||
tail -50 %LOCALAPPDATA%/hearthlink/logs/latest.log 2>/dev/null
```

#### Fallback 2: Force Rebuild
```bash
# Sometimes a clean rebuild helps
cd src-tauri
cargo clean
cd ..
npm run tauri:dev
```

#### Fallback 3: Production Build
```bash
# If dev mode fails, try production
npm run build
npm run tauri:build
./src-tauri/target/release/hearthlink
```

## Expected Output

```markdown
## Tauri Launcher Report

### 🧹 Cleanup
- ✅ Killed 3 orphaned processes
- ✅ Ports 3000, 3001, 3005 now available

### 🚀 Launch Sequence

**Stage 1: Webpack Dev Server**
- Started on port 3000
- Compiled successfully in 8.2s
- Assets ready: index.html, bundle.js, main.css

**Stage 2: Port Verification**
- tauri.conf.json expects: localhost:3000
- Webpack serving on: localhost:3000
- ✅ Port match confirmed

**Stage 3: Tauri Process**
- Started process ID: 12345
- Rust compilation: success (42.1s)
- Frontend detection: success

**Stage 4: Window Detection**
- Waiting for window...
- ⏱️ 15s - Tauri process running
- ⏱️ 22s - Window handle detected
- ✅ COREFORGE window opened successfully

### 📊 Status
- **Dev Server:** Running on http://localhost:3000
- **Tauri Window:** Open and responding
- **Hot Reload:** Active
- **DevTools:** Available (F12)

### 🎯 Next Steps
1. Clear localStorage for FirstRunSetup test:
   - Open DevTools (F12)
   - Console: `localStorage.clear(); location.reload();`
2. Verify styled FirstRunSetup appears
3. Begin testing onboarding flow
```

## Error Handling

### If Port In Use
```markdown
❌ Port 3000 already in use (PID: 9876)
🔧 Automatically killed process 9876
✅ Port now available, retrying...
```

### If Window Doesn't Open
```markdown
⚠️ Tauri window not detected after 60s

**Diagnostics:**
- Tauri process: Running (PID 12345)
- Webpack: Serving correctly
- Logs show: "Waiting for devPath..."

**Likely Cause:** Port mismatch
**Fix Applied:** Updated tauri.conf.json to port 3000
**Action:** Restarting Tauri process...
```

### If Compilation Fails
```markdown
❌ Tauri compilation failed

**Error:** Missing dependency: libwebkit2gtk
**Platform:** Linux
**Fix:** Run `sudo apt install libwebkit2gtk-4.0-dev`
```

## Agent Assignment
- **Primary:** general-purpose agent (routine launches)
- **Escalate to:** QA agent (if compilation issues)
- **MCP Access:**
  - filesystem (read tauri.conf.json, logs)
  - playwright (optional, for window automation)

## Token Savings
- **Before:** 10-20K tokens manually debugging launch issues
- **After:** 1-3K tokens running this skill
- **Savings:** ~15K tokens (85% reduction)

## Learning from Session
Encodes these discoveries from 2025-10-24:
1. Multiple background processes cause conflicts - kill first
2. Webpack must start before Tauri reads its port
3. Port mismatch is #1 reason window doesn't open
4. Need staged launch with verification between stages
5. Window detection requires platform-specific checks
