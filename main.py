import os

import config
from API.nadeoAuth import NadeoAuth
from API.trackmaniaApi import TrackmaniaAPI


def filter_non_jp_players(leaderboards):
    jp_players = os.getenv('JP_PLAYERS', '{}')
    if not jp_players:
        return

    for item in leaderboards:
        item['member_map'] = {
            acc_id: name for acc_id, name in item['member_map'].items()
            if name in jp_players
        }

        filtered_records = [
            r for r in item['records']
            if r['accountId'] in item['member_map']
        ]

        filtered_records = filtered_records[:5]

        for i, record in enumerate(filtered_records, start=1):
            record['position'] = i

        item['records'] = filtered_records


def format_tm_time(ms):
    """Formats milliseconds into HH:MM:SS.ms, omitting hours/minutes if 0."""
    if ms < 0: return "0.000s"

    seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}.{milliseconds:03}"
    elif minutes > 0:
        return f"{minutes}:{seconds:02}.{milliseconds:03}"
    else:
        return f"{seconds}.{milliseconds:03}s"


def display_map_records(map_name, records, member_map):
    """Handles the visual formatting of the leaderboard with time deltas."""
    print(f"\n--- Map: {map_name} ---")
    if not records:
        print("No records found.")
        return

    print(f"{'順位':<3} | {'ドライバー':<17} | {'タイム':<8} | {'デルタ':<8}")
    print("-" * 52)

    # Reference for the first place time
    top_score = records[0].get('score', 0)

    for entry in records:
        acc_id = entry.get('accountId')
        name = member_map.get(acc_id, f"ID: {acc_id[:8]}")

        current_score = entry.get('score', 0)

        # Format main time
        time_str = format_tm_time(current_score)

        # Handle Delta
        if entry.get('position') == 1:
            delta_str = "Interval"
        else:
            delta_ms = current_score - top_score
            delta_str = f"+{format_tm_time(delta_ms)}"

        print(f"{entry.get('position'):<4} | {name[:20]:<20} | {time_str:<10} | {delta_str:<10}")


def display_leaderboard(campaign_name, leaderboards):
    print(f"\n{'-' * 40}")
    print(f"Weekly short: {campaign_name}")
    for item in leaderboards:
        display_map_records(
            map_name=item['name'],
            records=item['records'],
            member_map=item['member_map']
        )


def main():
    api = TrackmaniaAPI(NadeoAuth())
    club_id = config.CLUB_ID
    if not club_id:
        club_id = api.live.get_club_by_id()
        if not club_id:
            return

    # This single call orchestrates all services and auth
    print("Fetching Weekly Shorts data...")
    # Change offset to get older weeks. offset=1: Last week
    campaign_name, leaderboards = api.get_weekly_data(club_id, offset=1)
    if not campaign_name:
        print("Couldn't find leaderboards")
        return

    filter_non_jp_players(leaderboards)
    display_leaderboard(campaign_name, leaderboards)


if __name__ == "__main__":
    main()
