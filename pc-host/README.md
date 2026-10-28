# PC setup host

The setup host is built by remote-loader's `tools/build_host.py`; this
repository does not maintain a separate DNS/HTTPS implementation. The generated
`webkit-autoloader-host_v<version>.py` embeds standalone HTML pages for both chains
(Relapse and Poops) carrying the installer ELF and a TLS certificate. At runtime, it
automatically routes firmwares where Relapse is unsupported (9.05) to Poops.
It needs only Python's standard library.

Optional PC setup page branding can be supplied without rebuilding. Create
a `custom/` folder beside the `.py` host script or `.exe`, then place any of
these files in it:

```text
custom/theme.json
custom/theme.css
custom/logo.svg
```

PNG and WebP logos are also supported as `logo.png` or `logo.webp`. In
`theme.json`, set `"logo"` to `/logo.svg`, `/logo.png`, or `/logo.webp` to
match the file. Restart the host after changes. The host embeds these files
directly into its HTML response, so the PS5 does not make separate theme asset
requests during exploit startup. The later installer page is served from the
installer ELF on the PS5 and only uses a theme bundled when that ELF was built.
See [`../custom/README.md`](../custom/README.md) for the JSON options.

Run the generated script, set the PS5's DNS to your PC's IP, then open Settings →
User's Guide. The page runs the exploit and installer; reboot after installation.
On systems requiring elevated privileges for ports 53/443, run the host with sudo.
Check that the IP printed by the host is the PC's address on the same LAN as
the PS5. VPNs can make automatic detection choose an unreachable address; use
`--ip <LAN-IP>` to override it. The host prints a DNS status line when the PS5
first reaches it and an HTTP line when the User's Guide page is requested.

For a local HTTP check without DNS or HTTPS:

```sh
python3 webkit-autoloader-host_v<version>.py --no-dns --no-https --http-port 8123
```

Use `--help` for upstream host options. `--extract <directory>` extracts the
embedded page. Build both versioned artifacts with `./build_release.sh`, or build
only the host from an existing installer with:

```sh
make host HOST_PAYLOAD=webkit-autoloader-installer_v<version>.elf
```
