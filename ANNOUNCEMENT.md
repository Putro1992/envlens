# Share envlens

Copy one of these posts. Please keep claims factual: the project is new, CI is
running, and there are open `good first issue` tasks. Do not invent stars,
forks, users or merged pull requests.

## English — X / LinkedIn

> I just published **envlens**, a zero-dependency Python tool for `.env` files.
> It checks a real config against `.env.example`, diffs two configs key by key,
> and lints for weak-looking secrets — with values redacted by default.
>
> It is stdlib-only, typed, has a CLI and 22 tests, and fails CI when a template
> drifts. I am looking for first contributors: four `good first issue` tasks are
> open (CI annotations, config file, Indonesian README, Docker Compose recipe).
>
> https://github.com/Putro1992/envlens

## English — Hacker News / Reddit (longer)

> **Show HN: envlens – verify, diff and audit .env files without leaking values**
>
> `.env.example` files rot silently: a key is added in production but not in the
> template, a value is left blank, a token stays `test`. A plain `diff` shows
> secret values and does not understand dotenv syntax.
>
> envlens is a single Python package (standard library only) that offers:
>
> - `check REFERENCE TARGET` — missing, extra and empty keys; exits 1 on drift
> - `diff OLD NEW` — added/removed/changed keys, values hidden by default
> - `lint FILE` — duplicate or malformed lines, empty values, weak secrets
> - JSON output and CI-friendly exit codes for automation
>
> It ships with 22 unit/CLI tests, a CI matrix on three OSes, and four beginner
> issues. Feedback and small PRs are very welcome.
>
> https://github.com/Putro1992/envlens

## Bahasa Indonesia — X / LinkedIn / komunitas

> Saya baru merilis **envlens**, library + CLI Python tanpa dependency untuk
> memeriksa file `.env`. Bisa mencocokkan `.env` dengan `.env.example`,
> membandingkan dua konfigurasi per key, dan mendeteksi value yang kosong atau
> terlihat lemah — nilai rahasia tetap disembunyikan by default.
>
> Cocok untuk CI: exit code 1 kalau ada key yang hilang. Sudah ada 22 tes dan 4
> issue `good first issue` untuk kontributor pertama.
>
> https://github.com/Putro1992/envlens

## Where to post

- X / LinkedIn: short version, include the repo link.
- r/programming, r/Python, r/devops: use the longer version; follow each subreddit's self-promotion rules.
- Hacker News: "Show HN" title, longer version, be present in the comments.
- Indonesian communities (Telegram/Discord programming): Indonesian version.

Questions from visitors should go to
[GitHub Discussions](https://github.com/Putro1992/envlens/discussions).
