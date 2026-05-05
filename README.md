# Toniebox Integration for Home Assistant

A custom integration for Home Assistant to manage your Toniebox devices and Creative Tonies via the Tonie Cloud API.

## Features

- **Media Player** for each Toniebox:
  - Playback state (playing / idle)
  - Volume control
  - Mute toggle (maps to the ear-slap gesture)

- **Sensor Entities** for each Toniebox:
  - Maximum speaker volume
  - Maximum headphone volume
  - Connected Wi-Fi SSID
  - Battery level *(when exposed by firmware)*
  - Wi-Fi signal strength (RSSI) *(when exposed by firmware)*
  - Last played timestamp *(when exposed by firmware)*

- **Sensor Entities** for each Creative Tonie:
  - Number of chapters present
  - Total duration of content (seconds)
  - Remaining duration capacity (seconds)
  - Transcoding status (`ready` or `transcoding`)

- **Binary Sensor Entities** for each Toniebox:
  - Offline mode status

- **Binary Sensor Entities** for each Creative Tonie:
  - Live status
  - Private status

- **Switch Entities** for each Toniebox:
  - Ear Slap (tap-to-skip gesture) toggle

- **Select Entities** for each Toniebox:
  - LED level (`off`, `dimmed`, `on`)

- **Services** to manage your Creative Tonies and Toniebox:
  - Upload audio files to Creative Tonies
  - Add chapters from already uploaded files
  - Clear all chapters from a Creative Tonie
  - Sort/reorder chapters
  - Set maximum speaker volume

- **Multi-language Support**: English and French translations included

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add `https://github.com/homeassistant-fr-ecosystem/tonies-box-hass`
   - Select "Integration" as the category

2. Install the integration through HACS

3. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/tonies_box` folder to your Home Assistant's `custom_components` directory:
   ```
   <config_directory>/custom_components/tonies_box/
   ```

2. Restart Home Assistant

## Configuration

1. In Home Assistant, go to **Settings** → **Devices & Services**

2. Click **Add Integration**

3. Search for **Toniebox**

4. Enter your Toniebox cloud credentials (email and password)

5. Your Toniebox devices and Creative Tonies will appear as devices with their associated entities

## Usage

### Media Player

Each Toniebox appears as a media player entity. It reflects live playback state from the Tonie Cloud and supports:

- **Volume control** — adjusts the maximum speaker volume
- **Mute** — disables the ear-slap (tap-to-skip) gesture

> **Note:** Play/pause control is not supported — the Tonie Cloud API does not expose a playback endpoint.

### Toniebox Sensors

Each Toniebox has the following sensors:

- **Max Volume**: Maximum speaker volume (%)
- **Max Headphone Volume**: Maximum headphone volume (%)
- **SSID**: The Wi-Fi network the box is connected to
- **Battery**: Battery charge level (%) — only shown when your firmware reports it
- **WiFi Signal**: Signal strength in dBm — only shown when your firmware reports it
- **Last Played**: Timestamp of last playback — only shown when your firmware reports it

### Toniebox Controls

Each Toniebox has the following controls:

- **Ear Slap** (switch): Enable or disable the tap-to-skip ear gesture
- **LED** (select): Set the LED brightness — `off`, `dimmed`, or `on`

### Toniebox Binary Sensors

- **Offline Mode**: Whether the box is operating in offline mode

### Creative Tonie Sensors

Each Creative Tonie has the following sensors:

- **Chapters**: Current number of chapters on the Tonie
- **Duration**: Total duration of all content in seconds
- **Remaining**: How much more time (in seconds) can be added
- **Transcoding**: Shows if files are being processed (`ready` or `transcoding`)

### Creative Tonie Binary Sensors

- **Live**: Whether the Creative Tonie is set to live mode
- **Private**: Whether the Creative Tonie is set to private mode

### Services

#### Upload File to Tonie

Upload an audio file and add it as a new chapter:

```yaml
service: tonies_box.upload_file
data:
  tonie_id: "your-tonie-id-here"
  file_path: "/config/media/story.mp3"
  title: "My Story"
```

#### Add Chapter to Tonie

Add a previously uploaded file as a chapter:

```yaml
service: tonies_box.add_chapter
data:
  tonie_id: "your-tonie-id-here"
  file_id: "file-id-from-upload"
  title: "Chapter 1"
```

#### Clear All Chapters

Remove all chapters from a Creative Tonie:

```yaml
service: tonies_box.clear_chapters
data:
  tonie_id: "your-tonie-id-here"
```

#### Sort Chapters

Reorder chapters on a Creative Tonie:

```yaml
service: tonies_box.sort_chapters
data:
  tonie_id: "your-tonie-id-here"
  chapters:
    - id: "chapter-1-id"
      title: "Chapter 1"
      file: "file-1-id"
      seconds: 120.5
    - id: "chapter-2-id"
      title: "Chapter 2"
      file: "file-2-id"
      seconds: 95.3
```

#### Set Volume

Set the maximum speaker volume of a Toniebox (0–100):

```yaml
service: tonies_box.set_volume
data:
  box_id: "your-box-id-here"
  volume: 75
```

### Finding Tonie and Box IDs

You can find IDs in several ways:

1. **From Developer Tools → States**:
   - Find your entity (e.g., `sensor.my_tonie_chapters` or `sensor.my_toniebox_max_volume`)
   - The device information will show the ID

2. **From the Raw Data sensor**:
   - A `sensor.<entry>_raw_data` entity exposes the full API response as attributes, including all IDs

## Example Automations

### Notify When Transcoding is Complete

```yaml
automation:
  - alias: "Notify when Tonie is ready"
    trigger:
      - platform: state
        entity_id: sensor.my_tonie_transcoding
        from: "transcoding"
        to: "ready"
    action:
      - service: notify.mobile_app
        data:
          message: "Your Tonie {{ trigger.to_state.attributes.friendly_name }} is ready!"
```

### Upload Story at Night

```yaml
automation:
  - alias: "Upload bedtime story"
    trigger:
      - platform: time
        at: "19:00:00"
    action:
      - service: tonies_box.upload_file
        data:
          tonie_id: "your-tonie-id"
          file_path: "/config/media/bedtime_story.mp3"
          title: "Tonight's Story"
```

### Monitor Storage Capacity

```yaml
automation:
  - alias: "Warn when Tonie is almost full"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_tonie_remaining
        below: 300
    action:
      - service: notify.mobile_app
        data:
          message: "Your Tonie only has {{ states('sensor.my_tonie_remaining') }} seconds of space left!"
```

### Dim LED at Bedtime

```yaml
automation:
  - alias: "Dim Toniebox LED at bedtime"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.my_toniebox_led
        data:
          option: "dimmed"
```

### Adjust Volume Based on Time of Day

```yaml
automation:
  - alias: "Lower Toniebox volume at night"
    trigger:
      - platform: time
        at: "20:30:00"
    action:
      - service: media_player.volume_set
        target:
          entity_id: media_player.my_toniebox_media_player
        data:
          volume_level: 0.3
```

## Troubleshooting

### Authentication Issues

If you receive an authentication error during setup:
- Verify your email and password are correct
- Try logging in at [meine.tonies.de](https://meine.tonies.de) to ensure your account is active
- Check that your network can reach `login.tonies.com`

### Connection Errors During Setup

If you see a "cannot connect" error:
- Check your Home Assistant host has internet access
- Verify no firewall is blocking outbound HTTPS traffic

### File Upload Fails

- Ensure the file path is accessible by Home Assistant
- Supported formats depend on the Tonie API (MP3 is recommended)
- Verify the file size doesn't exceed the Creative Tonie's remaining capacity (check the `Remaining` sensor)

### Sensors Not Updating

- The integration polls the API every 5 minutes
- You can manually refresh by calling the `homeassistant.update_entity` service
- Services automatically trigger a refresh after a successful operation

### Battery / RSSI / Last Played Sensors Missing

These sensors only appear when your Toniebox firmware reports the corresponding data. Not all firmware versions expose battery level, signal strength, or last-played timestamp. If these sensors are missing, your device likely doesn't report them yet.

## API Reference

This integration communicates directly with the Tonie Cloud REST API (`api.tonie.cloud`) and GraphQL endpoint (`api.prod.tcs.toys`).

**Note**: This integration is not affiliated with or endorsed by Boxine GmbH (tonies.de).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request on [GitHub](https://github.com/homeassistant-fr-ecosystem/tonies-box-hass).

## License

This project is licensed under the MIT License.

## Credits

Inspired by the community's need for Home Assistant integration with Toniebox.
