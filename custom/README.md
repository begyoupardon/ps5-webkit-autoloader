# Custom installer appearance

Put your custom installer theme in this directory. The build copies supported
files into the offline installer cache; no runtime network access is needed.

- Edit `theme.json` to set brand text, logo, and built-in color tokens.
- Replace `logo.svg` with your own SVG, or use `logo.png` / `logo.webp`, then
  set the matching path (`/logo.svg`, `/logo.png`, or `/logo.webp`) in `theme.json`.
- Edit `theme.css` for additional layout or visual changes. It loads after the
  built-in styles and may override them.

The JSON file is optional; absent files use the stock project appearance. Color
values must be CSS hex colors (`#RGB`, `#RRGGBB`, or alpha variants). The logo
path must be one of `/logo.svg`, `/logo.png`, or `/logo.webp`. Text is inserted
as text, not HTML.

At build time, these files customize the on-console installer page. Placed
beside a generated PC host at runtime, they customize the PC setup pages.
Runtime files cannot change an installer ELF that has already been built. The
appearance does not alter the exploit chain, payload behavior, or homescreen
icon. To customize the PS5 homescreen icon, replace `assets/icon.svg` with your own art
and run the normal release build; that icon is generated separately.
