import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import asyncio

# Load environment variables
load_dotenv()
load_dotenv('template_config.env')

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
SCHEDULE_FILE = os.getenv('SCHEDULE_FILE', 'scheduleData.json')
SATURDAY_DATE = os.getenv('SATURDAY_DATE')
SUNDAY_DATE = os.getenv('SUNDAY_DATE')
SATURDAY_DAY_START = os.getenv('SATURDAY_DAY_START', '00:00')
SUNDAY_DAY_START = os.getenv('SUNDAY_DAY_START', '00:00')
TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')
ANNOUNCE_BEFORE_MINUTES = [int(m.strip()) for m in os.getenv('ANNOUNCE_BEFORE_MINUTES', '15,5').split(',')]

# Embed color configuration
EMBED_COLORS = {
    'important': int(os.getenv('EMBED_COLOR_IMPORTANT', '0xFF5733'), 16),
    'food': int(os.getenv('EMBED_COLOR_FOOD', '0x33FF57'), 16),
    'workshop': int(os.getenv('EMBED_COLOR_WORKSHOP', '0x3357FF'), 16),
    'constant': int(os.getenv('EMBED_COLOR_CONSTANT', '0xFFFF33'), 16),
    'deadline': int(os.getenv('EMBED_COLOR_DEADLINE', '0xFF3333'), 16),
    'default': int(os.getenv('EMBED_COLOR_DEFAULT', '0x7289DA'), 16),
}

# Footer configuration
FOOTER_TEXT = os.getenv('EMBED_FOOTER_TEXT', 'HackRPI Announcements')
FOOTER_ICON = os.getenv('EMBED_FOOTER_ICON_URL', '')
THUMBNAIL_URL = os.getenv('EMBED_THUMBNAIL_URL', '')

# Template configuration
TITLE_TEMPLATE = os.getenv('ANNOUNCEMENT_TITLE_TEMPLATE', '📢 Upcoming Event: {title}')
DESCRIPTION_TEMPLATE = os.getenv('ANNOUNCEMENT_DESCRIPTION_TEMPLATE', '**{title}** is starting soon!')

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Store scheduled announcements
scheduled_events = []
announced_events = set()


def load_schedule():
    """Load schedule from JSON file"""
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading schedule: {e}")
        return None


def parse_event_datetime(event, day_date, day_start_time, timezone):
    """Convert event start time to datetime object"""
    date_obj = datetime.strptime(day_date, '%Y-%m-%d')
    tz = pytz.timezone(timezone)
    
    # Parse day start time (HH:MM format)
    start_hour, start_minute = map(int, day_start_time.split(':'))
    
    # Calculate start time from minutes after day start
    start_minutes = event['startMinutesFromDayStart']
    total_minutes = (start_hour * 60 + start_minute) + start_minutes
    
    # Handle overflow to next day
    days_offset = 0
    while total_minutes >= 1440:  # 1440 minutes in a day
        total_minutes -= 1440
        days_offset += 1
    
    hours = total_minutes // 60
    minutes = total_minutes % 60
    
    # Create datetime with timezone
    event_dt = tz.localize(datetime(
        date_obj.year, date_obj.month, date_obj.day,
        hours, minutes
    ))
    
    # Add days offset if event goes past midnight
    if days_offset > 0:
        event_dt += timedelta(days=days_offset)
    
    return event_dt


def create_embed(event, announce_minutes_before):
    """Create Discord embed for an event"""
    # Get color based on event type
    color = EMBED_COLORS.get(event.get('eventType', 'default'), EMBED_COLORS['default'])
    
    # Format time
    event_time = event.get('_datetime')
    if event_time:
        time_str = event_time.strftime('%I:%M %p')
    else:
        time_str = "TBD"
    
    # Format duration
    duration = event.get('durationMinutes', 0)
    
    # Create title and description from templates
    title = TITLE_TEMPLATE.format(
        title=event.get('title', 'Event'),
        description=event.get('description', ''),
        location=event.get('location', ''),
        speaker=event.get('speaker', ''),
        time=time_str,
        duration=duration,
        event_type=event.get('eventType', '')
    )
    
    description = DESCRIPTION_TEMPLATE.format(
        title=event.get('title', 'Event'),
        description=event.get('description', ''),
        location=event.get('location', ''),
        speaker=event.get('speaker', ''),
        time=time_str,
        duration=duration,
        event_type=event.get('eventType', '')
    )
    
    if announce_minutes_before > 0:
        description += f"\n\n⏰ Starting in **{announce_minutes_before} minutes**!"
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(pytz.UTC)
    )
    
    # Add fields based on template configuration
    if os.getenv('FIELD_TIME_ENABLED', 'true').lower() == 'true' and time_str:
        field_name = os.getenv('FIELD_TIME_NAME', '🕒 Time')
        field_value = os.getenv('FIELD_TIME_VALUE', '{time}').format(
            time=time_str, duration=duration, 
            title=event.get('title', ''), location=event.get('location', ''),
            speaker=event.get('speaker', ''), description=event.get('description', ''),
            event_type=event.get('eventType', '')
        )
        embed.add_field(name=field_name, value=field_value, inline=True)
    
    if os.getenv('FIELD_LOCATION_ENABLED', 'true').lower() == 'true' and event.get('location'):
        field_name = os.getenv('FIELD_LOCATION_NAME', '📍 Location')
        field_value = os.getenv('FIELD_LOCATION_VALUE', '{location}').format(
            location=event.get('location', ''), time=time_str, duration=duration,
            title=event.get('title', ''), speaker=event.get('speaker', ''),
            description=event.get('description', ''), event_type=event.get('eventType', '')
        )
        embed.add_field(name=field_name, value=field_value, inline=True)
    
    if os.getenv('FIELD_SPEAKER_ENABLED', 'true').lower() == 'true' and event.get('speaker'):
        field_name = os.getenv('FIELD_SPEAKER_NAME', '🎤 Speaker')
        field_value = os.getenv('FIELD_SPEAKER_VALUE', '{speaker}').format(
            speaker=event.get('speaker', ''), time=time_str, duration=duration,
            title=event.get('title', ''), location=event.get('location', ''),
            description=event.get('description', ''), event_type=event.get('eventType', '')
        )
        embed.add_field(name=field_name, value=field_value, inline=True)
    
    if os.getenv('FIELD_DURATION_ENABLED', 'true').lower() == 'true' and duration:
        field_name = os.getenv('FIELD_DURATION_NAME', '⏱️ Duration')
        field_value = os.getenv('FIELD_DURATION_VALUE', '{duration} minutes').format(
            duration=duration, time=time_str, title=event.get('title', ''),
            location=event.get('location', ''), speaker=event.get('speaker', ''),
            description=event.get('description', ''), event_type=event.get('eventType', '')
        )
        embed.add_field(name=field_name, value=field_value, inline=True)
    
    if os.getenv('FIELD_DESCRIPTION_ENABLED', 'true').lower() == 'true' and event.get('description'):
        field_name = os.getenv('FIELD_DESCRIPTION_NAME', 'ℹ️ Details')
        field_value = os.getenv('FIELD_DESCRIPTION_VALUE', '{description}').format(
            description=event.get('description', ''), time=time_str, duration=duration,
            title=event.get('title', ''), location=event.get('location', ''),
            speaker=event.get('speaker', ''), event_type=event.get('eventType', '')
        )
        embed.add_field(name=field_name, value=field_value, inline=False)
    
    # Add footer
    if FOOTER_TEXT:
        if FOOTER_ICON:
            embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON)
        else:
            embed.set_footer(text=FOOTER_TEXT)
    
    # Add thumbnail
    if THUMBNAIL_URL:
        embed.set_thumbnail(url=THUMBNAIL_URL)
    
    return embed


def schedule_events():
    """Schedule all events from the JSON file"""
    global scheduled_events
    scheduled_events = []
    
    schedule_data = load_schedule()
    if not schedule_data:
        print("Failed to load schedule data")
        return
    
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    
    print(f"\nCurrent time: {now.strftime('%Y-%m-%d %I:%M %p %Z')}")
    print(f"Saturday date: {SATURDAY_DATE} starting at {SATURDAY_DAY_START}")
    print(f"Sunday date: {SUNDAY_DATE} starting at {SUNDAY_DAY_START}")
    print(f"Announcement times: {ANNOUNCE_BEFORE_MINUTES} minutes before events\n")
    
    events_processed = 0
    events_in_past = 0
    
    # Process Saturday events
    for event in schedule_data.get('saturdayEvents', []):
        if not event.get('visible', True):
            continue
        
        events_processed += 1
        event_dt = parse_event_datetime(event, SATURDAY_DATE, SATURDAY_DAY_START, TIMEZONE)
        event['_datetime'] = event_dt
        event['_day'] = 'saturday'
        
        # Schedule announcements before the event
        for minutes_before in ANNOUNCE_BEFORE_MINUTES:
            announce_dt = event_dt - timedelta(minutes=minutes_before)
            
            # Only schedule if in the future
            if announce_dt > now:
                scheduled_events.append({
                    'event': event,
                    'announce_time': announce_dt,
                    'minutes_before': minutes_before
                })
            else:
                events_in_past += 1
    
    # Process Sunday events
    for event in schedule_data.get('sundayEvents', []):
        if not event.get('visible', True):
            continue
        
        events_processed += 1
        event_dt = parse_event_datetime(event, SUNDAY_DATE, SUNDAY_DAY_START, TIMEZONE)
        event['_datetime'] = event_dt
        event['_day'] = 'sunday'
        
        # Schedule announcements before the event
        for minutes_before in ANNOUNCE_BEFORE_MINUTES:
            announce_dt = event_dt - timedelta(minutes=minutes_before)
            
            # Only schedule if in the future
            if announce_dt > now:
                scheduled_events.append({
                    'event': event,
                    'announce_time': announce_dt,
                    'minutes_before': minutes_before
                })
            else:
                events_in_past += 1
    
    # Sort by announcement time
    scheduled_events.sort(key=lambda x: x['announce_time'])
    
    print(f"Processed {events_processed} visible events")
    print(f"Skipped {events_in_past} announcements (already past)")
    print(f"Scheduled {len(scheduled_events)} announcements")
    if scheduled_events:
        print(f"Next announcement at: {scheduled_events[0]['announce_time'].strftime('%Y-%m-%d %I:%M %p %Z')}")
        print(f"  Event: {scheduled_events[0]['event']['title']}")
    else:
        print("⚠️ No announcements scheduled - all events may be in the past!")
        print("   Check your SATURDAY_DATE and SUNDAY_DATE in .env file")


@tasks.loop(seconds=30)
async def check_announcements():
    """Check if any announcements should be sent"""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Could not find channel with ID {CHANNEL_ID}")
        return
    
    # Check all scheduled events
    events_to_remove = []
    for scheduled in scheduled_events:
        announce_time = scheduled['announce_time']
        
        # Create unique identifier for this announcement
        event_id = f"{scheduled['event']['id']}_{scheduled['minutes_before']}"
        
        # Check if it's time to announce and hasn't been announced yet
        if now >= announce_time and event_id not in announced_events:
            try:
                embed = create_embed(scheduled['event'], scheduled['minutes_before'])
                await channel.send(embed=embed)
                announced_events.add(event_id)
                events_to_remove.append(scheduled)
                
                print(f"Announced: {scheduled['event']['title']} ({scheduled['minutes_before']} min before)")
            except Exception as e:
                print(f"Error sending announcement: {e}")
    
    # Remove announced events from schedule
    for event in events_to_remove:
        scheduled_events.remove(event)


@check_announcements.before_loop
async def before_check_announcements():
    """Wait for bot to be ready before starting the loop"""
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    """Called when bot is ready"""
    print(f'{bot.user} has connected to Discord!')
    print(f'Monitoring channel ID: {CHANNEL_ID}')
    
    # Load and schedule events
    schedule_events()
    
    # Start announcement checker
    if not check_announcements.is_running():
        check_announcements.start()


@bot.command(name='reload')
@commands.has_permissions(administrator=True)
async def reload_schedule(ctx):
    """Reload the schedule from the JSON file"""
    global announced_events
    announced_events.clear()
    schedule_events()
    await ctx.send(f"✅ Schedule reloaded! {len(scheduled_events)} announcements scheduled.")


@bot.command(name='next')
async def next_announcement(ctx):
    """Show the next scheduled announcement"""
    if not scheduled_events:
        await ctx.send("No announcements currently scheduled.")
        return
    
    next_event = scheduled_events[0]
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    time_until = next_event['announce_time'] - now
    
    minutes_until = int(time_until.total_seconds() / 60)
    
    embed = discord.Embed(
        title="Next Scheduled Announcement",
        description=f"**{next_event['event']['title']}**",
        color=EMBED_COLORS.get(next_event['event'].get('eventType', 'default'), EMBED_COLORS['default'])
    )
    embed.add_field(name="Announcement Time", value=next_event['announce_time'].strftime('%I:%M %p'), inline=True)
    embed.add_field(name="Time Until", value=f"{minutes_until} minutes", inline=True)
    embed.add_field(name="Warning", value=f"{next_event['minutes_before']} min before event", inline=True)
    
    await ctx.send(embed=embed)


@bot.command(name='upcoming')
async def upcoming_events(ctx, count: int = 5):
    """Show upcoming announcements"""
    if not scheduled_events:
        await ctx.send("No announcements currently scheduled.")
        return
    
    count = min(count, 10)  # Limit to 10
    upcoming = scheduled_events[:count]
    
    embed = discord.Embed(
        title=f"Next {len(upcoming)} Announcements",
        color=EMBED_COLORS['default']
    )
    
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    
    for i, scheduled in enumerate(upcoming, 1):
        time_until = scheduled['announce_time'] - now
        minutes_until = int(time_until.total_seconds() / 60)
        
        embed.add_field(
            name=f"{i}. {scheduled['event']['title']}",
            value=f"In {minutes_until} min ({scheduled['announce_time'].strftime('%I:%M %p')})",
            inline=False
        )
    
    await ctx.send(embed=embed)


@bot.command(name='test')
@commands.has_permissions(administrator=True)
async def test_announcement(ctx, event_index: int = 0):
    """Test an announcement by sending it immediately"""
    schedule_data = load_schedule()
    if not schedule_data:
        await ctx.send("Failed to load schedule data")
        return
    
    all_events = schedule_data.get('saturdayEvents', []) + schedule_data.get('sundayEvents', [])
    
    if event_index < 0 or event_index >= len(all_events):
        await ctx.send(f"Invalid event index. Must be between 0 and {len(all_events)-1}")
        return
    
    event = all_events[event_index]
    
    # Parse datetime for the event
    if event in schedule_data.get('saturdayEvents', []):
        day_date = SATURDAY_DATE
        day_start = SATURDAY_DAY_START
    else:
        day_date = SUNDAY_DATE
        day_start = SUNDAY_DAY_START
    
    event['_datetime'] = parse_event_datetime(event, day_date, day_start, TIMEZONE)
    
    embed = create_embed(event, 15)
    await ctx.send("Test announcement:", embed=embed)


# Run the bot
if __name__ == '__main__':
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not found in .env file")
    elif not CHANNEL_ID:
        print("ERROR: CHANNEL_ID not found in .env file")
    else:
        bot.run(TOKEN)
