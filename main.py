from auth import NadeoAuth
from api import TrackmaniaAPI


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
    # 1. Initialize our tools
    auth = NadeoAuth()
    api = TrackmaniaAPI()

    # 2. Get tokens (Refreshes if needed, otherwise logs in)
    print("Checking Authentication...")
    live_token = auth.get_token("live")
    core_token = auth.get_token("core")

    if not live_token or not core_token:
        print("Authentication failed. Check your config.py.")
        return

    # 3. Get your Club ID automatically
    club_id = "89488"  # KERORINPA
    # club_id = api.get_my_club_id(live_token)
    # if not club_id:
    #     print("No club found for this account.")
    #     return
    # print(f"Working with Club ID: {club_id}")

    # 4. Get the Member Names from Trackmania.io
    print("Fetching Club Member names...")
    member_map = api.get_club_members(club_id)
    print(f"Loaded {len(member_map)} members.")

    # 5. Get the Weekly Shorts Map UIDs
    print("Fetching Weekly Shorts maps...")
    map_uids = api.get_weekly_shorts_uids(live_token)

    # 6. Get the friendly names for those maps
    map_names = api.get_map_names(core_token, map_uids)

    # 7. Print the Leaderboards!
    for uid in map_uids:
        friendly_name = map_names.get(uid, uid)
        # 1. Get the raw data from API
        records = api.get_pb_leaderboard(live_token, club_id, uid)

        # 2. Display the data using our main function
        display_leaderboard(friendly_name, records, member_map)


if __name__ == "__main__":
    main()
