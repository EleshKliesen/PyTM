from API.nadeoAuth import NadeoAuth
from API.trackmaniaApi import TrackmaniaAPI


def display_leaderboard(map_name, records, member_map):
    """Handles the visual formatting of the leaderboard."""
    print(f"\n--- Map: {map_name} ---")
    if not records:
        print("No records found.")
        return

    print(f"{'Pos':<4} | {'Player':<20} | {'Time':<10}")
    print("-" * 40)
    for entry in records:
        acc_id = entry.get('accountId')
        name = member_map.get(acc_id, f"ID: {acc_id[:8]}")
        time_s = entry.get('score', 0) / 1000
        print(f"{entry.get('position'):<4} | {name[:20]:<20} | {time_s:.3f}s")


def main():
    api = TrackmaniaAPI(NadeoAuth())
    club_id = "89488"  # KERORINPA
    # club_id = api.live.get_club_id()
    # if not club_id:
    #     return

    # This single call orchestrates all services and auth
    print("Fetching Weekly Shorts data...")
    leaderboards = api.get_weekly_data(club_id)
    if not leaderboards:
        return

    for item in leaderboards:
        display_leaderboard(
            map_name=item['name'],
            records=item['records'],
            member_map=item['member_map']
        )


if __name__ == "__main__":
    main()
