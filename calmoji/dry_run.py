# calmoji/dry_run.py

from calmoji.types import Event

# def dry_run(events: list[Event], phase_name: str):
#     """
#     Print a dry-run preview of meeting events for a given phase.
#     """
#     print(f"\n📆 Phase: {phase_name}")
#     print("─" * (12 + len(phase_name)))

#     for event in events:
#         start_str = event.start.strftime('%a %Y-%m-%d %H:%M')
#         summary_str = event.summary or "(No Summary)"
#         print(f"{summary_str.ljust(48)}  [{start_str}]")

#     print(f"\nTotal: {len(events)} meeting slots\n")

def dry_run(events: list[Event], label: str = "Event Preview", kind: str = "slots") -> None:
    """
    Print a dry-run preview of a set of calendar events.

    Args:
        events (list[Event]): List of events to preview.
        label (str): Title for this batch of events (e.g., phase name or week slug).
        kind (str): Event type (e.g., 'slots', 'blocks', 'rituals') for reporting.
    """
    print(f"\n📆 {label}")
    print("─" * (12 + len(label)))

    for event in events:
        start_str = event.start.strftime('%a %Y-%m-%d %H:%M')
        summary_str = event.summary or "(No Summary)"
        print(f"{summary_str.ljust(48)}  [{start_str}]")

    print(f"\nTotal: {len(events)} {kind}\n")
