# Skill Evaluator

**META-SKILL:** Measures skill effectiveness and identifies improvements.

## Purpose
Closes the learning loop by tracking which skills actually save tokens/time and which need refinement.

## Auto-Trigger
- After any skill is executed
- Weekly report on all skill usage
- When user reports "skill didn't help"

## What This Skill Does

### 1. Usage Tracking
```bash
# Create .claude/skills/metrics/ directory
mkdir -p .claude/skills/metrics

# Log each skill execution
cat >> .claude/skills/metrics/$(date +%Y-%m).json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "skill": "build-doctor",
  "trigger": "CSS not loading",
  "tokens_before_skill": 1200,
  "tokens_after_skill": 800,
  "resolution_time_seconds": 45,
  "success": true,
  "user_feedback": "worked perfectly"
}
EOF
```

### 2. Effectiveness Calculation
```javascript
// For each skill, calculate:
const tokenSavings = estimatedManualTokens - actualSkillTokens;
const timeToResolution = timestamp(resolved) - timestamp(invoked);
const successRate = successful_executions / total_executions;
const netValue = (tokenSavings * successRate) - skillMaintenanceCost;
```

### 3. Skill Health Report
```markdown
## Skill Health Report - Week of 2025-10-20

### 🏆 Top Performing Skills
1. **build-doctor**
   - Usage: 12 times
   - Avg token savings: 35K per use
   - Success rate: 92%
   - Total impact: 420K tokens saved
   - Status: ✅ EXCELLENT

2. **tauri-launcher**
   - Usage: 8 times
   - Avg token savings: 18K per use
   - Success rate: 100%
   - Total impact: 144K tokens saved
   - Status: ✅ EXCELLENT

### ⚠️ Skills Needing Attention
1. **css-processor** (if exists)
   - Usage: 2 times
   - Success rate: 50%
   - Issue: Missing edge case for webpack 5
   - Action: Update with webpack 5 handling

### 📊 Unused Skills
1. **skill-debugging-assistant**
   - Never triggered
   - Reason: Unclear trigger conditions
   - Action: Improve description or deprecate

### 💡 Skill Gap Analysis
Problems solved without existing skill (new skill opportunities):
- "TypeScript compilation warnings" (3 occurrences, 15K tokens)
  → Suggested skill: typescript-config-doctor
- "Git merge conflicts" (2 occurrences, 8K tokens)
  → Suggested skill: merge-conflict-resolver
```

### 4. Continuous Improvement Recommendations
```markdown
## Improvements for build-doctor

**Data Shows:**
- 8% failure rate on Linux systems
- Common failure: "webkit2gtk not found"
- **Recommendation:** Add platform-specific dependency checks

**Updated Section:**
\```bash
# Platform-specific checks
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  dpkg -l | grep webkit2gtk || echo "Missing: libwebkit2gtk-4.0-dev"
fi
\```

## Improvements for tauri-launcher

**Data Shows:**
- 100% success but avg 45s launch time
- Delay caused by redundant port checks
- **Recommendation:** Cache last known good port

**Updated Section:**
\```bash
# Read cached port if available
LAST_PORT=$(cat .claude/cache/last_port 2>/dev/null || echo "3000")
\```
```

## Expected Output

```markdown
## Monthly Skill Performance Report - October 2025

### 📈 Overall Impact
- Total token savings: 892K
- Sessions improved: 34
- Average resolution time: 2.3 minutes (was 45 minutes)
- ROI: 178x (tokens saved vs. skill development cost)

### 🎯 Skill Rankings

| Skill | Uses | Success | Savings | Rank |
|-------|------|---------|---------|------|
| build-doctor | 24 | 96% | 840K | ⭐⭐⭐⭐⭐ |
| tauri-launcher | 18 | 100% | 324K | ⭐⭐⭐⭐⭐ |
| learning-capture | 1 | 100% | 450K | ⭐⭐⭐⭐⭐ |
| css-processor | 4 | 75% | 48K | ⭐⭐⭐ |

### 🔧 Recommended Actions

**High Priority:**
1. Update css-processor for webpack 5 edge cases
2. Create typescript-config-doctor (3 opportunities identified)
3. Deprecate unused skills to reduce cognitive load

**Medium Priority:**
4. Add caching to tauri-launcher for faster launches
5. Improve build-doctor platform detection
6. Create skill-dependency-mapper to optimize workflows

### 🧠 Learning Insights

**Pattern: Build tool issues dominate**
- 67% of skill usage is build-related (build-doctor, tauri-launcher, css-processor)
- Recommendation: Create unified build-troubleshooter meta-skill

**Pattern: Skills prevent recurring issues**
- Zero recurrence of CSS processing bugs after build-doctor created
- Zero recurrence of Tauri port mismatch after tauri-launcher created
- Conclusion: Skills successfully encode institutional knowledge

**Pattern: Meta-skills have highest ROI**
- learning-capture: 1 use, 450K token impact (created other skills)
- skill-evaluator: Ongoing value through continuous improvement
- Recommendation: Invest in more meta-skills
```

## Agent Assignment
- **Primary:** general-purpose (auto-runs after skill execution)
- **Schedule:** Weekly aggregation report
- **MCP Access:** filesystem (read/write metrics)

## Self-Evaluation
This skill itself will be measured on:
- Accuracy of token savings estimates
- Usefulness of improvement recommendations
- Speed of identifying skill gaps
- Quality of generated insights

## Integration with learning-capture
```
learning-capture creates skills
         ↓
skill-evaluator measures their effectiveness
         ↓
Provides feedback to learning-capture
         ↓
learning-capture improves skill generation
         ↓
[Continuous improvement loop]
```
