# Remote Study Workspace

The lesson site saves one private study record to Netlify Blobs. That record contains all lesson responses, implementation plans, reflections, and statuses. It is the shared source of truth for phone, browser, and home agent use.

## Configure Netlify

1. Deploy this repository to Netlify. The existing build publishes `site/`.
2. In **Project configuration → Environment variables**, add `STUDY_ACCESS_TOKEN`. Use a long, unique value and do not commit it.
3. Deploy again. Netlify installs `@netlify/blobs` and provisions the site storage automatically when the study function first saves data.

## Study on a phone

Open the deployed site, then open a lesson. Select **Connect sync** and enter `STUDY_ACCESS_TOKEN`. The token is retained only in that browser tab/session. Notes save automatically and are available from any browser session that uses the same token.

## Use the notes at home

Set the site URL and token in your local shell, then fetch the latest record:

```sh
export STUDY_SITE_URL="https://your-site.netlify.app"
export STUDY_ACCESS_TOKEN="your-private-token"
./tools/fetch-study-notes
```

The command writes two ignored, local outputs:

- `curriculum/data/study.json` — the complete remote snapshot.
- `curriculum/data/study-notes/<lesson-id>.json` — one generated note file per lesson, for example `0006-agent-loop-primitive.json`.

The per-lesson directory is generated from the remote record on every fetch. Do not edit those files by hand: the next fetch replaces them, and removes files for lessons that no longer exist remotely. This keeps the phone-saved record as the single source of truth.

For example: “Run `./tools/fetch-study-notes`, then read `curriculum/data/study-notes/0006-agent-loop-primitive.json` and help me build its first proof.”

## Security model

The site itself can be public. Study data is only returned when the request includes the private token. Treat the token like a password: do not place it in the repository, source code, or a public URL.
