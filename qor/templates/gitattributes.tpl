# Phase 181 (GH #238): pin governance artifacts to LF so canonical bytes
# never drift with host core.autocrlf settings. Seal digests are computed
# over LF-normalized bytes; this makes the working tree match by contract.
docs/*.md text eol=lf
docs/**/*.md text eol=lf
.qor/** text eol=lf
