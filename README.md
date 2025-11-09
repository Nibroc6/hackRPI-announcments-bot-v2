# HackRPI Announcements Bot

A Discord bot that automatically sends event announcements based on a JSON schedule file. Built with discord.py, this bot sends customizable embed messages to a specified channel at scheduled times before events.

## Features

- 📅 Automatically schedules announcements based on JSON event data
- 🎨 Customizable embed templates with color coding by event type
- ⏰ Multiple announcement times (e.g., 15 min and 5 min before events)
- 🌍 Timezone support
- 💬 Admin commands for testing and managing announcements
- 🔧 Fully configurable via .env files

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" tab and click "Add Bot"
4. Under "Token", click "Copy" to copy your bot token
5. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
6. Go to "OAuth2" > "URL Generator"
   - Select scopes: `bot`
   - Select bot permissions: `Send Messages`, `Embed Links`, `Read Message History`
   - Copy the generated URL and use it to invite the bot to your server

### 3. Get Channel ID

1. In Discord, enable Developer Mode (User Settings > Advanced > Developer Mode)
2. Right-click the channel where you want announcements
3. Click "Copy Channel ID"

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```env
DISCORD_TOKEN=your_bot_token_here
CHANNEL_ID=your_channel_id_here
SATURDAY_DATE=2024-11-09
SUNDAY_DATE=2024-11-10
TIMEZONE=America/New_York
ANNOUNCE_BEFORE_MINUTES=15,5
```

### 5. (Optional) Customize Embed Templates

Edit `template_config.env` to customize how announcements appear:
- Change field names and emojis
- Enable/disable specific fields
- Modify templates with variables like `{title}`, `{location}`, `{speaker}`, etc.

### 6. Run the Bot

```bash
python bot.py
```

## Configuration

### Main Settings (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Your Discord bot token | `MTIzNDU2Nzg5...` |
| `CHANNEL_ID` | Channel ID for announcements | `123456789012345678` |
| `SCHEDULE_FILE` | Path to schedule JSON file | `scheduleData.json` |
| `SATURDAY_DATE` | Date for Saturday events | `2024-11-09` |
| `SUNDAY_DATE` | Date for Sunday events | `2024-11-10` |
| `SATURDAY_DAY_START` | Reference time for Saturday's startMinutesFromDayStart | `12:00` |
| `SUNDAY_DAY_START` | Reference time for Sunday's startMinutesFromDayStart | `00:00` |
| `TIMEZONE` | Timezone for event times | `America/New_York` |
| `ANNOUNCE_BEFORE_MINUTES` | Minutes before event to announce | `15,5` |

### Embed Colors

Customize colors for different event types (hex values):

```env
EMBED_COLOR_IMPORTANT=0xFF5733
EMBED_COLOR_FOOD=0x33FF57
EMBED_COLOR_WORKSHOP=0x3357FF
EMBED_COLOR_CONSTANT=0xFFFF33
EMBED_COLOR_DEADLINE=0xFF3333
EMBED_COLOR_DEFAULT=0x7289DA
```

### Template Customization (template_config.env)

Available variables for templates:
- `{title}` - Event title
- `{description}` - Event description
- `{location}` - Event location
- `{speaker}` - Speaker name
- `{time}` - Event start time
- `{duration}` - Duration in minutes
- `{event_type}` - Event type (important, food, workshop, etc.)

## Bot Commands

All commands use the `!` prefix.

### User Commands

- `!next` - Show the next scheduled announcement
- `!upcoming [count]` - Show upcoming announcements (default: 5, max: 10)

### Admin Commands

- `!reload` - Reload the schedule from JSON file
- `!test [index]` - Send a test announcement for a specific event (by index)

## Schedule JSON Format

The bot expects a JSON file with the following structure:

```json
{
  "saturdayEvents": [
    {
      "id": "unique-id",
      "title": "Event Name",
      "description": "Event description",
      "location": "Location",
      "speaker": "Speaker Name",
      "eventType": "important|food|workshop|constant|deadline",
      "visible": true,
      "column": 1,
      "startMinutesFromDayStart": 0,
      "durationMinutes": 60
    }
  ],
  "sundayEvents": [...]
}
```

### Event Fields

- `id` - Unique identifier
- `title` - Event name
- `description` - Event description (optional)
- `location` - Event location (optional)
- `speaker` - Speaker/presenter (optional)
- `eventType` - Type for color coding: `important`, `food`, `workshop`, `constant`, `deadline`
- `visible` - Whether to announce this event (true/false)
- `column` - Display column (not used by bot)
- `startMinutesFromDayStart` - Minutes from the configured day start time (e.g., if day starts at 12:00 PM, then 60 = 1:00 PM, 720 = 12:00 AM next day)
- `durationMinutes` - Event duration in minutes

### Understanding Day Start Time

The `SATURDAY_DAY_START` and `SUNDAY_DAY_START` settings define the reference point (hour 0) for your `startMinutesFromDayStart` values.

**Example 1:** If your Saturday events start at noon:
```env
SATURDAY_DAY_START=12:00
```
Then in your JSON:
- `startMinutesFromDayStart: 0` → 12:00 PM
- `startMinutesFromDayStart: 60` → 1:00 PM
- `startMinutesFromDayStart: 720` → 12:00 AM (next day)

**Example 2:** If your events follow a midnight-to-midnight schedule:
```env
SATURDAY_DAY_START=00:00
```
Then in your JSON:
- `startMinutesFromDayStart: 0` → 12:00 AM
- `startMinutesFromDayStart: 720` → 12:00 PM
- `startMinutesFromDayStart: 1440` → 12:00 AM (next day)

## Example Usage

1. Start the bot: `python bot.py`
2. The bot will automatically load and schedule all events
3. Announcements will be sent to the configured channel at the specified times
4. Use `!next` to see what's coming up
5. Use `!reload` after updating the JSON file to reschedule events

## Troubleshooting

**Bot doesn't connect:**
- Verify your `DISCORD_TOKEN` is correct
- Check that the bot has been invited to your server

**No announcements sent:**
- Verify `CHANNEL_ID` is correct
- Check that event dates are in the future
- Ensure events have `visible: true`
- Check bot permissions (Send Messages, Embed Links)

**Wrong times:**
- Verify `TIMEZONE` is set correctly
- Check `SATURDAY_DATE` and `SUNDAY_DATE` are correct
- Ensure `startMinutesFromDayStart` values are accurate

## License

MIT License - Feel free to use and modify for your events!
