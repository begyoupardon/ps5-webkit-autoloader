# Optional custom appearance

Create a `custom/` directory at the repository root only when you want a
branded build. Without it, releases use the stock WebKit Autoloader name,
logo, and colors. The build copies supported files into the offline installer
cache; no runtime network access is needed.

- Add `custom/theme.json` to set brand text, logo, and built-in color tokens.
- Add `custom/logo.svg` with your SVG, or use `logo.png` / `logo.webp`, then
  set the matching path (`/logo.svg`, `/logo.png`, or `/logo.webp`) in `theme.json`.
- Add `custom/theme.css` for additional layout or visual changes. It loads after the
  built-in styles and may override them.

All files are optional; absent files use the stock project appearance. Color
values must be CSS hex colors (`#RGB`, `#RRGGBB`, or alpha variants). The logo
path must be one of `/logo.svg`, `/logo.png`, or `/logo.webp`. Text is inserted
as text, not HTML.

At build time, these files customize the on-console installer page. Placed
beside a generated PC host at runtime, they customize the PC setup pages.
Runtime files cannot change an installer ELF that has already been built. The
appearance does not alter the exploit chain, payload behavior, or homescreen
icon at runtime. During a release build, `theme.json` also sets the PS5 app
name and the cached autoloader page's colors and header. `logo.svg` is fitted
inside a square icon tile; the tile background uses `colors.accentEnd`.
The generated homescreen and Windows icons use the same tile. If no custom SVG
exists, the stock `assets/icon.svg` is used. Commit `custom/` only when your
release should include those assets; a clean checkout without it builds the
stock appearance.
