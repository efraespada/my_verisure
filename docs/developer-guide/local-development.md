# Local Development Setup

This guide explains how to set up a local Home Assistant environment for developing and testing the My Verisure integration.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- [Cursor](https://cursor.sh) or [Visual Studio Code](https://code.visualstudio.com/)
- [Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) (usually pre-installed in Cursor)

## Quick Start with DevContainer

The project includes a complete DevContainer configuration that provides an isolated Home Assistant development environment.

### 1. Open in DevContainer

```bash
# Clone the repository (if you haven't already)
git clone <repository-url>
cd my_verisure

# Open in Cursor (or VS Code)
cursor .
# Or: code .
```

Cursor/VS Code will detect the `.devcontainer` configuration and prompt you to **"Reopen in Container"**. Click it.

Alternatively, open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) and select:
- **Remote-Containers: Reopen in Container**

### 2. Wait for Container Setup

The first time will take a few minutes:
- Downloads the Home Assistant dev container image (~2GB)
- Installs dependencies
- Sets up the development environment

### 3. Start Home Assistant

Once the container is ready, you have two options:

**Option A: Run from Cursor/VS Code Task**
1. Press `Cmd+Shift+P` / `Ctrl+Shift+P`
2. Select **Tasks: Run Task**
3. Select **Run Home Assistant**

**Option B: Run from Terminal**
```bash
container start
```

### 4. Access Home Assistant

Open your browser at: **http://localhost:7123**

On first run, you'll need to:
1. Create an admin user
2. Set up your home
3. Configure the My Verisure integration

## Development Workflow

### Making Changes

1. **Edit your code** in `custom_components/my_verisure/`
2. **Save the file** (auto-formatted with Black if enabled)
3. **Restart Home Assistant**:
   - From Cursor/VS Code: `Cmd+Shift+P` → **Tasks: Run Task** → **Restart Home Assistant**
   - From UI: Developer Tools → YAML → Restart
   - From Terminal: `container restart`

### Debugging with Breakpoints

1. Add breakpoints in your Python files (click in the gutter)
2. Press `F5` or go to **Run and Debug** panel
3. Select **Home Assistant (DevContainer)**
4. Click **Start Debugging** (green play button)

Home Assistant will start with the debugger attached. When code hits a breakpoint, Cursor/VS Code will pause and you can inspect variables.

**Note for Cursor users:** Debugging works exactly the same as in VS Code since Cursor is built on the same foundation.

### Running Tests

```bash
# Run all tests
pytest custom_components/my_verisure/tests/ -v

# Run specific test file
pytest custom_components/my_verisure/tests/test_config_flow.py -v

# Run with coverage
pytest --cov=custom_components.my_verisure custom_components/my_verisure/tests/
```

Or use the VS Code task:
- `Cmd+Shift+P` → **Tasks: Run Task** → **Run Tests**

### Code Quality Tools

```bash
# Linting
pylint custom_components/my_verisure

# Type checking
mypy custom_components/my_verisure

# Auto-formatting
black custom_components/my_verisure

# Check configuration
container check-config
```

Or use Cursor/VS Code tasks:
- **Lint: Pylint**
- **Format: Black**
- **Type Check: MyPy**
- **Check Config**

## Viewing Logs

### Real-time Logs

```bash
# In the DevContainer terminal
tail -f /config/home-assistant.log | grep my_verisure
```

### From Home Assistant UI

1. Go to **Developer Tools** → **Logs**
2. Filter by "my_verisure"

### Configure Log Levels

Edit `.devcontainer/configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.my_verisure: debug  # Your integration
    my_verisure: debug                    # Your library
    homeassistant.core: warning           # Reduce noise
```

## Testing Services

### From Developer Tools

1. Go to **Developer Tools** → **Services**
2. Select your service (e.g., `my_verisure.arm_away`)
3. Fill in the data:
   ```yaml
   installation_id: "123456"
   ```
4. Click **Call Service**

### From Scripts

Use the example scripts in `.devcontainer/scripts.yaml`:

1. Go to **Developer Tools** → **Services**
2. Select `script.test_arm_away`
3. Click **Execute**

## Testing Automations

Example automation in `.devcontainer/automations.yaml`:

```yaml
- id: test_alarm_state_change
  alias: "Test: Log Alarm State Changes"
  trigger:
    - platform: state
      entity_id: alarm_control_panel.my_verisure
  action:
    - service: system_log.write
      data:
        message: "Alarm changed from {{ trigger.from_state.state }} to {{ trigger.to_state.state }}"
        level: info
```

## Checking Entity States

### From Developer Tools

1. Go to **Developer Tools** → **States**
2. Search for "my_verisure"
3. View all entities and their attributes

### From Terminal

```bash
# List all entities
ha entities list | grep my_verisure

# Show specific entity
ha state get alarm_control_panel.my_verisure
```

## Alternative Setup Methods

### Option 1: Docker Container (No DevContainer)

If you prefer not to use VS Code DevContainer:

```bash
# Create config directory
mkdir -p ~/ha-test-config/custom_components

# Symlink your integration
ln -s "$(pwd)/custom_components/my_verisure" ~/ha-test-config/custom_components/

# Run Home Assistant
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=Europe/Madrid \
  -v ~/ha-test-config:/config \
  -p 8123:8123 \
  ghcr.io/home-assistant/home-assistant:stable

# View logs
docker logs -f homeassistant

# Access at http://localhost:8123
```

### Option 2: Python Virtual Environment

For lightweight testing without Docker:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Home Assistant
pip3 install homeassistant

# Create config directory
mkdir -p config/custom_components
ln -s "$(pwd)/custom_components/my_verisure" config/custom_components/

# Run Home Assistant
hass -c ./config
```

## Troubleshooting

### Container Won't Start

```bash
# Rebuild the container
# In Cursor/VS Code: Cmd+Shift+P → Remote-Containers: Rebuild Container

# Or manually:
docker stop homeassistant
docker rm homeassistant
# Reopen in container
```

### Integration Not Loading

1. Check logs for errors:
   ```bash
   tail -f /config/home-assistant.log | grep -i error
   ```

2. Verify the integration is in the right place:
   ```bash
   ls -la /config/custom_components/my_verisure
   ```

3. Check manifest.json is valid:
   ```bash
   container check-config
   ```

### Port Already in Use

If port 7123 is already in use, edit `.devcontainer/devcontainer.json`:

```json
"appPort": [
  "7124:8123"  // Change to another port
],
```

### Changes Not Reflecting

Make sure to restart Home Assistant after code changes:
```bash
container restart
```

Or reload the integration:
- Go to **Settings** → **Devices & Services**
- Click the 3 dots on My Verisure
- Click **Reload**

## Tips for Efficient Development

1. **Use hot reload**: Most changes don't require full restart. Use Developer Tools → YAML → Reload instead.

2. **Keep logs visible**: Have a terminal with `tail -f` running to catch errors immediately.

3. **Use breakpoints**: Debug mode is much faster than adding print statements.

4. **Test incrementally**: Make small changes and test frequently.

5. **Use the container commands**:
   ```bash
   container start        # Start HA
   container restart      # Restart HA
   container stop         # Stop HA
   container check-config # Validate config
   ```

## Next Steps

- [Integration Architecture](../architecture/README.md)
- [Testing Guide](./testing.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
- [API Documentation](../api-reference/README.md)
