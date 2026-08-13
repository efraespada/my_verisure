# Installation

## Requirements

| Requirement | Detail |
|-------------|--------|
| Home Assistant | `2026.8.1` (Core; Python >=3.14.2) |
| Integration icon in UI | **2026.3+** loads [`brand/`](../../custom_components/my_verisure/brand/) images locally; older cores use the [brands CDN](https://github.com/home-assistant/brands) or a placeholder if the domain is not published there |
| Python packages | Declared in [`manifest.json`](../../custom_components/my_verisure/manifest.json): `aiohttp`, `voluptuous`, `injector`, `PyJWT`, `Pillow` |
| Network | HTTPS access to Securitas Direct GraphQL (`VERISURE_GRAPHQL_URL` in [`core/const.py`](../../custom_components/my_verisure/core/const.py)) |

## Install via HACS (recommended)

1. Open **HACS** in Home Assistant.  
2. **Integrations → ⋮ → Custom repositories** (if this repo is not in the default store).  
3. Add the repository URL, category **Integration**, or use HACS search if published.  
4. **Download** "My Verisure" / this integration.  
5. **Restart Home Assistant** (required for new `custom_components`).  
6. Add the integration under **Settings → Devices & services** ([Configuration](configuration.md)).  

`hacs.json` sets `render_readme: true` so the store can show the root README.

## Manual installation

1. Copy the folder `custom_components/my_verisure/` into your configuration directory:  
   `<config>/custom_components/my_verisure/`  
2. Ensure `manifest.json` and all Python packages resolve (Home Assistant installs `requirements` from the manifest on startup).  
3. Restart Home Assistant.  
4. Add the integration from the UI.  

There is **no** YAML-only setup path documented for end users; configuration is **Config Flow** based (`"config_flow": true` in the manifest).

## Verify installation

- Check **Settings → Devices & services** for **My Verisure** without errors.  
- Enable debug logging if needed ([Troubleshooting](troubleshooting.md)):  

```yaml
logger:
  logs:
    custom_components.my_verisure: debug
```

## Version and metadata

- Integration version: see `version` in [`manifest.json`](../../custom_components/my_verisure/manifest.json)  
- Issue tracker / docs URLs in manifest point to the GitHub repository  
