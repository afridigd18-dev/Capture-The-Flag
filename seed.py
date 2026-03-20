"""
seed.py — Populates the database with 10 production-ready CTF challenges
and creates an admin user. Run once after `flask db upgrade`.

Usage:
    python seed.py
"""
import os
import sys

# Make sure the project root is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.challenge import Challenge, Hint
from app.utils.flag_crypto import hash_flag
from app.utils.markdown import slugify


# ------------------------------------------------------------------ #
# Challenge definitions                                                #
# ------------------------------------------------------------------ #

CHALLENGES = [
    {
        "title": "Base64 Warmup",
        "category": "crypto",
        "difficulty": "easy",
        "points": 50,
        "flag": "flag{base64_is_too_easy}",
        "description": """## Base64 Warmup

Welcome to your first cryptography challenge!

You intercepted the following encoded message:

```
ZmxhZ3tiYXNlNjRfaXNfdG9vX2Vhc3l9
```

**Hint:** Try decoding it from Base64.

Tools you might find useful:
- `echo "ZmxhZ3tiYXNlNjRfaXNfdG9vX2Vhc3l9" | base64 -d`
- CyberChef (cyberchef.org)
""",
        "hint_text": "Base64 uses only A–Z, a–z, 0–9, +, / and = as padding.",
        "hint_penalty": 10,
    },
    {
        "title": "Caesar's Last Message",
        "category": "crypto",
        "difficulty": "easy",
        "points": 40,
        "flag": "flag{caesar_loved_rot13}",
        "description": """## Caesar's Last Message

Julius Caesar was famously murdered. Before his death, he left an encrypted note:

```
synt{pnrfne_ybirq_ebg13}
```

The cipher is simple — a classic shift.

**Your mission:** Decode it and submit the flag.
""",
        "hint_text": "Try ROT13. Every letter is shifted by 13 positions.",
        "hint_penalty": 10,
    },
    {
        "title": "XOR Cipher",
        "category": "crypto",
        "difficulty": "medium",
        "points": 100,
        "flag": "flag{xor_is_beautifully_simple}",
        "description": """## XOR Cipher

You've intercepted a binary stream. Each byte has been XOR-encrypted with the key `0x42`.

Ciphertext (hex):
```
24 2d 23 7b 79 2f 72 5f 6b 73 5f 63 6c 23 7d 74 69 66 7c 6c 6c 79 5f 73 6b 6d 70 6c 65 7d
```

**Decode it!**

```python
key = 0x42
cipher = [0x24, 0x2d, 0x23, 0x7b, 0x79, 0x2f, 0x72, 0x5f,
          0x6b, 0x73, 0x5f, 0x63, 0x6c, 0x23, 0x7d, 0x74,
          0x69, 0x66, 0x7c, 0x6c, 0x6c, 0x79, 0x5f, 0x73,
          0x6b, 0x6d, 0x70, 0x6c, 0x65, 0x7d]
plain = bytes([c ^ key for c in cipher]).decode()
print(plain)
```
""",
        "hint_text": "XOR with the same key twice gets you back to plaintext: `x XOR key XOR key = x`",
        "hint_penalty": 25,
    },
    {
        "title": "EXIF Metadata Leak",
        "category": "forensics",
        "difficulty": "easy",
        "points": 60,
        "flag": "flag{exif_secrets_revealed}",
        "description": """## EXIF Metadata Leak

A photo was posted by a suspected agent. Intelligence suggests the flag is hidden inside the image's metadata.

Download the file and extract its EXIF data.

**Tools:**
```bash
exiftool challenge.jpg
# or
strings challenge.jpg | grep flag
```

Look for a field called `Comment` or `UserComment`.
""",
        "hint_text": "Check the `Comment` EXIF field. Tools: exiftool, strings, binwalk",
        "hint_penalty": 15,
    },
    {
        "title": "Hidden in ZIP",
        "category": "forensics",
        "difficulty": "easy",
        "points": 75,
        "flag": "flag{zip_forensics_master}",
        "description": """## Hidden in ZIP

We recovered an encrypted ZIP archive from a compromised server.

Password is known to be: **`infected`**

Extract the archive and look for `flag.txt`.

```bash
unzip -P infected challenge.zip
cat flag.txt
```
""",
        "hint_text": "The password is literally the word `infected`. Try `unzip -P infected archive.zip`",
        "hint_penalty": 15,
    },
    {
        "title": "Steganography Basics",
        "category": "forensics",
        "difficulty": "medium",
        "points": 120,
        "flag": "flag{strings_find_secrets}",
        "description": """## Steganography Basics

The enemy hides secrets in plain sight. This PNG image looks normal, but something is lurking beneath the surface.

Try running `strings` against the file and look for anything that resembles a flag.

```bash
strings image.png | grep flag
```

Or use `steghide`, `zsteg`, or `binwalk` for deeper analysis.
""",
        "hint_text": "Run `strings image.png | grep -i flag`. The flag has been embedded as raw ASCII in the image file.",
        "hint_penalty": 30,
    },
    {
        "title": "SQL Injection Lab",
        "category": "web",
        "difficulty": "medium",
        "points": 125,
        "flag": "flag{sql_injection_owned}",
        "description": """## SQL Injection Lab

A login portal has been discovered. The developer forgot to sanitise inputs.

**Target URL:** Simulated internally.

The backend query looks like this:
```sql
SELECT * FROM users WHERE username = '$username' AND password = '$password'
```

**Classic bypass payload:**
```
Username: admin' --
Password: anything
```

This turns the query into:
```sql
SELECT * FROM users WHERE username = 'admin' --' AND password = 'anything'
```

The `--` comments out the password check! Find the admin panel and retrieve the flag.
""",
        "hint_text": "Try `' OR '1'='1' --` as the username with any password. This bypasses the auth entirely.",
        "hint_penalty": 30,
    },
    {
        "title": "Cookie Monster",
        "category": "web",
        "difficulty": "medium",
        "points": 150,
        "flag": "flag{cookie_manipulation_101}",
        "description": """## Cookie Monster

This web app stores session info in a cookie. The cookie value looks like a Base64-encoded JSON object.

Inspect your cookies after logging in:
```
auth=eyJyb2xlIjoidXNlciIsInVzZXJuYW1lIjoiZ3Vlc3QifQ==
```

Decode it:
```bash
echo "eyJyb2xlIjoidXNlciIsInVzZXJuYW1lIjoiZ3Vlc3QifQ==" | base64 -d
# {"role":"user","username":"guest"}
```

Change `"role"` to `"admin"`, re-encode, and replace the cookie.

```bash
echo '{"role":"admin","username":"guest"}' | base64
```
""",
        "hint_text": "Decode the cookie (base64), change role to admin, re-encode and set it as your cookie.",
        "hint_penalty": 30,
    },
    {
        "title": "JavaScript Obfuscation",
        "category": "web",
        "difficulty": "medium",
        "points": 175,
        "flag": "flag{js_deobfuscation_pro}",
        "description": """## JavaScript Obfuscation

A web page contains a hidden API endpoint protected by an obfuscated JavaScript key check.

Obfuscated JS snippet:
```javascript
var _0x1a2b = ['ZmxhZ3tqc19kZW9iZnVzY2F0aW9uX3Byb30='];
(function(_0xabc, _0xdef) {
  var _0xghi = function(_0xjkl) {
    while (--_0xjkl) { _0xabc['push'](_0xabc['shift']()); }
  };
  _0xghi(++_0xdef);
}(_0x1a2b, 0x1b));
```

**Hint:** Look at the string array. It's Base64.
```bash
echo "ZmxhZ3tqc19kZW9iZnVzY2F0aW9uX3Byb30=" | base64 -d
```
""",
        "hint_text": "The obfuscated string array contains a Base64-encoded flag. Decode `_0x1a2b[0]`.",
        "hint_penalty": 40,
    },
    {
        "title": "Buffer Overflow Intro",
        "category": "pwn",
        "difficulty": "easy",
        "points": 200,
        "flag": "flag{stack_smash_success}",
        "description": """## Buffer Overflow Intro

A vulnerable C program reads user input into a fixed buffer without bounds checking:

```c
#include <stdio.h>
#include <string.h>

void win() {
    printf("flag{stack_smash_success}\\n");
}

void vuln() {
    char buf[64];
    gets(buf);  // Dangerous!
}

int main() {
    vuln();
    return 0;
}
```

**Your task:** Overflow the buffer and redirect execution to `win()`.

```bash
python3 -c "print('A'*64 + 'B'*8)" | ./vuln
# or use pwntools for a proper exploit
```

For this simulation, submitting the flag directly after understanding the concept is accepted.
""",
        "hint_text": "Fill 64 bytes of buffer + 8 bytes of saved RBP, then place the address of `win()`. Use `objdump -d ./vuln | grep win` to find the address.",
        "hint_penalty": 50,
    },
]


def seed():
    """Seed database with admin user and 10 challenges."""
    app = create_app("development")

    with app.app_context():
        # Create tables if not exists (dev only; use flask db upgrade in prod)
        db.create_all()

        # ---------------------------------------------------------------- #
        # Admin user                                                        #
        # ---------------------------------------------------------------- #
        admin_email = app.config.get("ADMIN_EMAIL", "admin@ctf.local")
        admin_pwd = app.config.get("ADMIN_PASSWORD", "Admin@CTF2024!")

        existing_admin = User.query.filter_by(email=admin_email).first()
        if not existing_admin:
            admin = User(
                username="admin",
                email=admin_email,
                role="admin",
            )
            admin.set_password(admin_pwd)
            db.session.add(admin)
            db.session.flush()
            author_id = admin.id
            print(f"✅ Admin user created: {admin_email} / {admin_pwd}")
        else:
            author_id = existing_admin.id
            print(f"ℹ️  Admin already exists: {admin_email}")

        # ---------------------------------------------------------------- #
        # Demo player                                                       #
        # ---------------------------------------------------------------- #
        demo_email = "player@ctf.local"
        if not User.query.filter_by(email=demo_email).first():
            player = User(username="h4cker", email=demo_email)
            player.set_password("Player@CTF2024!")
            db.session.add(player)
            print("✅ Demo player created: h4cker / Player@CTF2024!")

        # ---------------------------------------------------------------- #
        # Challenges                                                        #
        # ---------------------------------------------------------------- #
        for ch_data in CHALLENGES:
            existing = Challenge.query.filter_by(title=ch_data["title"]).first()
            if existing:
                print(f"⏭️  Skipping existing: {ch_data['title']}")
                continue

            slug = slugify(ch_data["title"])
            base_slug = slug
            counter = 1
            while Challenge.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1

            ch = Challenge(
                title=ch_data["title"],
                slug=slug,
                description=ch_data["description"],
                category=ch_data["category"],
                difficulty=ch_data["difficulty"],
                points=ch_data["points"],
                flag_hash=hash_flag(ch_data["flag"]),
                active=True,
                author_id=author_id,
            )
            db.session.add(ch)
            db.session.flush()

            if ch_data.get("hint_text"):
                hint = Hint(
                    challenge_id=ch.id,
                    text=ch_data["hint_text"],
                    penalty_points=ch_data.get("hint_penalty", 25),
                )
                db.session.add(hint)

            print(f"✅ Challenge: {ch_data['title']} [{ch_data['category']}] {ch_data['points']}pts")

        db.session.commit()
        print("\n🎉 Seeding complete! Visit http://localhost:5000 to start hacking.")
        print(f"\n   Admin login: {admin_email} / {app.config.get('ADMIN_PASSWORD', 'Admin@CTF2024!')}")
        print("   Demo login:  h4cker / Player@CTF2024!")


if __name__ == "__main__":
    seed()
