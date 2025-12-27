# Toniebox Integration for Home Assistant

A custom integration for Home Assistant to manage your Toniebox Creative Tonies via the Tonie Cloud API.

## Features

- **Sensor Entities** for each Creative Tonie:
  - Number of chapters present
  - Total duration of content
  - Remaining chapter capacity
  - Remaining duration capacity
  - Transcoding status
  - Last update timestamp

- **Services** to manage your Creative Tonies:
  - Upload audio files to Creative Tonies
  - Add chapters from already uploaded files
  - Clear all chapters from a Creative Tonie
  - Sort/reorder chapters

- **Multi-language Support**: English and French translations included

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add the URL of this repository
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

5. Your Creative Tonies will appear as devices with their associated sensors

## Usage

### Sensors

Each Creative Tonie will have the following sensors:

- **Chapters**: Current number of chapters on the Tonie
  - Attributes include the full chapter list with titles, durations, and IDs
- **Duration**: Total duration of all content in seconds
- **Remaining Chapters**: How many more chapters can be added
- **Remaining Duration**: How much more time (in seconds) can be added
- **Transcoding Status**: Shows if files are being processed (`ready` or `transcoding`)
- **Last Update**: Timestamp of the last modification

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
      transcoding: false
    - id: "chapter-2-id"
      title: "Chapter 2"
      file: "file-2-id"
      seconds: 95.3
      transcoding: false
```

### Finding Tonie IDs

You can find the Tonie ID in several ways:

1. **From the sensor entity**:
   - Go to Developer Tools → States
   - Find your Tonie sensor (e.g., `sensor.my_tonie_chapters`)
   - The device information will show the Tonie ID

2. **From sensor attributes**:
   - Check the chapter list attributes in the Chapters sensor
   - Each chapter includes the parent Tonie's household ID and ID

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
        entity_id: sensor.my_tonie_remaining_chapters
        below: 5
    action:
      - service: notify.mobile_app
        data:
          message: "Your Tonie only has {{ states('sensor.my_tonie_remaining_chapters') }} chapters left!"
```

## Troubleshooting

### Authentication Issues

If you receive authentication errors:
- Verify your email and password are correct
- Try logging in at [meine.tonies.de](https://meine.tonies.de) to ensure your account is active
- Check that you're using the correct region (this integration uses the default Tonie Cloud API)

### File Upload Fails

- Ensure the file path is accessible by Home Assistant
- Supported formats: MP3, M4A, OGG, WAV (check current API limits)
- Verify the file size doesn't exceed the Creative Tonie's capacity

### Sensors Not Updating

- The integration polls the API every 5 minutes by default
- You can manually refresh by calling the `homeassistant.update_entity` service
- Services automatically trigger a refresh after successful operations

## API Reference

This integration uses the unofficial [tonie-api](https://github.com/Wilhelmsson177/tonie-api) Python library.

**Note**: This integration is not affiliated with or endorsed by Boxine GmbH (tonies.de).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Credits

- [tonie-api](https://github.com/Wilhelmsson177/tonie-api) by Wilhelmsson177
- Inspired by the community's need for Home Assistant integration with Toniebox

## Support

For issues, questions, or feature requests, please open an issue on the [GitHub repository](https://github.com/your-username/tonies_hass).
