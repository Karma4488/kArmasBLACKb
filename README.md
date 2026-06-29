# kArmasBLACKb 

Usage:
# Username search
python3 kArmasBLACKb.py -u <username>

# Email OSINT
python3 kArmasBLACKb.py -e target@example.com

# Save results + faster threads
python3 kArmasBLACKb.py -u <username> --save --threads 50 --timeout 10

# List all platforms
python3 kArmasBLACKb.py --list-platforms

# Skip matrix intro (Termux speed run)
python3 kArmasBLACKb.py -u <username> --no-matrix


Username search — scans 150+ platforms concurrently (GitHub, Reddit, TikTok, HackerOne, Bugcrowd, Steam, PyPI, npm, Codeforces, LeetCode, Mastodon, Bluesky, Threads, and many more)
Email search — passive OSINT references: Gravatar MD5 hash lookup, HaveIBeenPwned, Epieos, Hunter.io, GHunt pointer, and major platform sign-in pages
Multi-threaded — 30 threads by default, fully configurable
Auth gate — requires "I AGREE" before scanning
Matrix rain intro + skull ASCII art + full kArmas branding
Export — --save writes JSON + CSV
No pip dependencies — stdlib only (urllib, threading, queue, json, csv)
