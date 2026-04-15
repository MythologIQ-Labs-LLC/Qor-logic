# Voice Integration Patterns Reference

## Speech Recognition Patterns

### Wake Word Detection
- Always-on low-power listening for trigger phrase
- Separate lightweight model for wake word vs full transcription
- Visual indicator when wake word detected (transition to active listening)
- Allow customizable wake words per user preference

### Continuous Recognition
- Stream audio to recognizer in real-time
- Distinguish interim results (in-progress) from final results (speech complete)
- Display interim transcription for user feedback
- Use Voice Activity Detection (VAD) for endpoint detection

### Recognition Modes
| Mode | Behavior | Use Case |
|------|----------|----------|
| Command | Short utterance, returns on silence | Quick actions, navigation |
| Dictation | Continuous, returns on pause | Note-taking, message composition |
| Conversation | Turn-based, alternates listen/speak | Multi-turn agent dialog |

### Offline Recognition
- On-device models (Whisper, Vosk) for privacy and latency
- Smaller models for command recognition, larger for dictation
- Fall back to cloud API when accuracy is insufficient
- Cache frequently used phrases for faster recognition

## Text-to-Speech Patterns

### Voice Selection
- Match voice to agent persona (distinct voices per agent)
- Respect user preferences (pitch, rate, volume)
- Use language-appropriate voice for multilingual content
- Provide preview before committing to voice change

### Speech Parameters
| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| Rate | 0.5 - 2.0 | 1.0 | Speed of speech |
| Pitch | 0.5 - 2.0 | 1.0 | Voice frequency |
| Volume | 0.0 - 1.0 | 1.0 | Loudness |

### SSML Patterns
- `<break time="500ms"/>` - Insert pauses for clarity
- `<emphasis level="strong">` - Stress important words
- `<say-as interpret-as="date">` - Format dates, numbers, currencies
- Fallback: strip tags for engines that don't support SSML

### TTS Controls
- Play / Pause / Stop buttons always visible during speech
- Keyboard shortcuts for hands-free control
- Auto-pause when user starts speaking (barge-in)
- Resume from interruption point (not restart)

## Voice UI Design

### Conversational Flow Design
1. System prompt (what the agent can help with)
2. User utterance (captured via speech recognition)
3. Intent parsing (extract action + entities)
4. Confirmation (explicit for destructive, implicit for safe actions)
5. Execution (perform the action)
6. Response (speak result, offer follow-up)

### Error Recovery Patterns
| Error | Recovery Strategy |
|-------|------------------|
| No speech detected | "I didn't hear anything. Try again?" |
| Low confidence | "Did you say [best guess]?" |
| Unknown intent | "I can help with [list capabilities]. What would you like?" |
| Ambiguous request | "Did you mean A or B?" |
| Action failed | "I couldn't [action]. Would you like to try again?" |

### Confirmation Patterns

**Explicit Confirmation** (for destructive/irreversible actions):
- "Delete all tasks? Say 'yes' to confirm or 'no' to cancel."
- Require exact confirmation word, not just "mm-hmm"

**Implicit Confirmation** (for safe/reversible actions):
- "Added 'buy groceries' to your task list."
- Allow undo: "Say 'undo' to remove it."

**Progressive Confirmation** (for multi-step actions):
- Confirm each step before proceeding
- Summarize all steps at end before final execution

### Discoverability
- On first use, offer guided tour of voice commands
- "Help" or "What can you do?" always available
- Provide visual command hints during idle state
- Context-sensitive suggestions based on current screen

## Audio Processing

### Input Pipeline
1. **Microphone capture** - Select input device, configure sample rate
2. **Noise cancellation** - Filter background noise, echo suppression
3. **Voice Activity Detection** - Detect speech start/end
4. **Preprocessing** - Normalize volume, resample if needed
5. **Recognition** - Send to speech-to-text engine
6. **Post-processing** - Punctuation, capitalization, formatting

### Audio Quality Settings
| Setting | Recommended | Notes |
|---------|-------------|-------|
| Sample Rate | 16kHz | Sufficient for speech, low bandwidth |
| Bit Depth | 16-bit | Standard for speech recognition |
| Channels | Mono | Stereo unnecessary for voice input |
| Format | PCM/WAV | Uncompressed for local; Opus for streaming |

### Device Management
- Detect available input/output devices
- Allow user to select preferred microphone and speaker
- Handle device changes gracefully (USB mic plugged/unplugged)
- Test audio level before starting recognition

## Intent Recognition

### Pattern Matching (Rule-Based)
```
Pattern: "remind me to {task} {date} at {time}"
Action: create_reminder
Entities: { task, date, time }

Pattern: "what is my {query}"
Action: query_information
Entities: { query }

Pattern: "cancel my {event_type}"
Action: cancel_event
Entities: { event_type }
```

### Intent Classification (ML-Based)
- Train classifier on labeled utterance dataset
- Use embeddings for semantic similarity matching
- Combine rule-based (high-precision) with ML (high-recall)
- Log low-confidence intents for training data improvement

### Entity Extraction
| Entity Type | Examples | Extraction Method |
|-------------|----------|-------------------|
| Date/Time | "tomorrow at 3pm", "next Friday" | Date parser library |
| Person | "Sarah", "Dr. Smith" | Named entity recognition |
| Number | "five", "42" | Number normalization |
| Duration | "30 minutes", "2 hours" | Duration parser |

### Confidence Handling
| Confidence | Action |
|-----------|--------|
| > 0.8 | Execute directly |
| 0.5 - 0.8 | Confirm with user: "Did you mean...?" |
| < 0.5 | Ask to rephrase: "I didn't understand. Could you say that differently?" |

## Voice Accessibility

### Motor Disability Support
- Complete app control via voice alone
- No time limits on speech input
- Support for switch-activated microphone
- Alternative activation methods (keyboard shortcut, gesture)

### Visual Impairment Support
- Voice output paired with screen reader compatibility
- Audio cues for state changes (listening, processing, error)
- No visual-only feedback (always pair with audio/haptic)
- Announce context changes via aria-live regions

### Cognitive Accessibility
- Keep voice prompts short and clear
- One question at a time
- Allow unlimited time to respond
- Repeat information on request
- Provide both voice and visual confirmation

### ADHD Support
- Voice input reduces friction for task capture
- Quick-fire mode: capture thoughts rapidly without confirmation
- Batch review captured items later
- Minimal required interaction per task

## Voice UI Testing

### Test Checklist
- [ ] Wake word detection works in quiet and noisy environments
- [ ] Recognition accuracy > 90% for supported commands
- [ ] Error recovery provides helpful guidance
- [ ] TTS output is clear and natural-sounding
- [ ] Keyboard alternatives exist for all voice functions
- [ ] Screen reader announces voice state changes
- [ ] Barge-in (interrupting TTS) works correctly
- [ ] Device switching handled without restart
- [ ] Privacy: no audio sent to cloud without user consent
- [ ] Latency: voice-to-response under 2 seconds

### Test Scenarios
| Scenario | Expected Behavior |
|----------|------------------|
| Speak clearly in quiet room | Accurate recognition, correct action |
| Speak with background noise | Degraded but functional, asks for repeat if needed |
| Speak with accent | Reasonable accuracy, graceful degradation |
| Say unknown command | Help message with available commands |
| Interrupt during TTS | TTS stops, system listens |
| No microphone available | Graceful fallback to text input |
| Long silence after prompt | Timeout message, option to retry |

## Architecture Decisions

### Browser API vs Native
| Approach | Pros | Cons |
|----------|------|------|
| Web Speech API | Cross-platform, no setup | Requires internet (Chrome), limited control |
| Native (Whisper) | Offline, privacy, customizable | Binary size, GPU/CPU requirements |
| Cloud API | Highest accuracy, many languages | Latency, cost, privacy concerns |

**Recommendation**: Start with Web Speech API, add native Whisper as optional enhancement for offline/privacy-sensitive users.

### Streaming vs Batch
| Approach | Latency | Accuracy | Use Case |
|----------|---------|----------|----------|
| Streaming | Low (real-time) | Lower | Live feedback, commands |
| Batch | Higher (wait for complete) | Higher | Transcription, dictation |

**Recommendation**: Use streaming for interactive commands, batch for long-form dictation.
