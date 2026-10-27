# Public sharing

Do nothing here unless the user explicitly asks to publish the deck and
understands that the result is publicly reachable. "Can you share this?" is not
enough if the intended audience or host is unclear; ask before uploading.

## Preflight

1. Identify the exact upload set. A deck is a dedicated folder containing
   `index.html` and its `assets/`; never upload the folder's parent, the skill
   directory, or a home directory.
2. List the files and inspect them: `find <deck-dir> -type f`. No `.env`, keys,
   private notes, unpublished images, or unrelated documents.
3. Confirm every image/font reference is relative or intentionally remote, and
   open the deck locally to check that it renders.
4. Explain where it will be hosted, whether the URL is public, and how to take it
   down. Get a clear yes before running an upload command.

## Vercel, for example

Do not install Vercel globally and do not automate login. The user logs in
themselves:

```bash
npx --yes vercel@latest login
npx --yes vercel@latest whoami
```

Then deploy only the dedicated folder, from outside the folder:

```bash
npx --yes vercel@latest deploy <deck-dir> --yes
```

`npx` fetches the CLI into the npm cache for this run; it does not add a global
package. `--prod` is a separate decision: ask whether the user wants a production
alias or a preview URL. Remove the deployment from the Vercel dashboard when the
user asks to take it down.

Other static hosts are equally valid. The same rules apply: upload only the deck
folder, verify the URL and every asset, and record how to remove it.

## After uploading

- Open the live URL and check fonts, images, and navigation on a phone-sized
  viewport.
- Report the URL, the uploaded file set, and the takedown path.
- Do not describe a local file path as a public URL, and do not claim deployment
  succeeded from a command's exit status alone if the URL was not checked.
