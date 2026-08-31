"""Self-check for format_slack_text emphasis handling.

Run: python3 scripts/test_format_slack_text.py
"""
from export_slack import format_slack_text, parse_list_url, apply_filters, render_message


def check(raw, expected, why):
    got = format_slack_text(raw, {})
    assert got == expected, f"{why}\n  in:  {raw!r}\n  got: {got!r}\n  want:{expected!r}"


def demo():
    # The bug this file exists for: a Google Doc id with an underscore came out
    # of Slack with the underscore rewritten to *, producing a dead link
    check(
        "https://docs.google.com/document/d/1YOef7khci8_Fs7H8oW0DBEQeDAnSTa8n9lVvHG5968M/edit",
        "https://docs.google.com/document/d/1YOef7khci8_Fs7H8oW0DBEQeDAnSTa8n9lVvHG5968M/edit",
        "underscore inside a URL is not emphasis",
    )
    check(":slightly_smiling_face:", ":slightly_smiling_face:", "emoji shortcode survives")
    check("call get_user_map() first", "call get_user_map() first", "snake_case survives")
    check("a_b_c_d", "a_b_c_d", "repeated intra-word underscores survive")

    # Real emphasis still converts
    check("_hello_", "*hello*", "italic at line bounds")
    check("say _hello_ there", "say *hello* there", "italic mid-line")
    check("*bold*", "**bold**", "bold at line bounds")
    check("a *bold* word", "a **bold** word", "bold mid-line")
    check("_two words_ here", "*two words* here", "multi-word italic")

    # Things that are not emphasis
    check("2 * 3 * 4", "2 * 3 * 4", "spaced asterisks are arithmetic, not bold")
    check("file_name.py and _real_ emphasis",
          "file_name.py and *real* emphasis",
          "both on one line, only the emphasis converts")

    # Channel refs
    check("join <#C08N2JFE97X|agu25>", "join #agu25", "channel ref with label")
    # Slack drops the label when a channel was linked by ID; keep the ID rather than invent a name
    check("join <#C08N2JFE97X|>", "join #C08N2JFE97X", "channel ref, empty label")
    check("join <#C08N2JFE97X>", "join #C08N2JFE97X", "channel ref, no label")
    check("see <https://x.com/a#b|docs>", "see [docs](https://x.com/a#b)", "a # in a URL is not a channel ref")

    # List URLs live at /lists/TEAM/FILE and must not be mistaken for channel URLs
    assert parse_list_url("https://w.slack.com/lists/T025QMQE3/F08CS9AG82Z") == ("F08CS9AG82Z", None)
    assert parse_list_url(
        "https://w.slack.com/lists/T025QMQE3/F08CS9AG82Z?record_id=Rec08L9JVG532"
    ) == ("F08CS9AG82Z", "Rec08L9JVG532")
    assert parse_list_url("https://w.slack.com/archives/C123/p1700000000000000") is None

    # --filter: case-insensitive substring, and repeated filters AND together
    ROWS = [
        {"Owner": "Alex Kim", "Status": "Done"},
        {"Owner": "alex morgan", "Status": "Open"},
        {"Owner": "Sam Lee", "Status": "Done"},
    ]
    assert apply_filters(ROWS, [("Owner", "alex")]) == ROWS[:2], "substring, case-insensitive"
    assert apply_filters(ROWS, [("Owner", "alex"), ("Status", "done")]) == [ROWS[0]], "filters AND"
    try:
        apply_filters(ROWS, [("Owner", "nobody")])
        raise AssertionError("a filter matching nothing must raise")
    except ValueError as e:
        # The error has to name the real columns -- they're user-defined per list, so guessing
        # the spelling is the whole problem it solves
        assert "Owner, Status" in str(e), f"error should list columns, got: {e}"

    # Every mode renders a message through render_message, so reactions and bodies can't drift
    MSG = {"user": "U1", "ts": "1700000000.0", "text": "hi",
           "reactions": [{"name": "tada", "count": 2}]}
    assert render_message(MSG, {"U1": "@Alex"})[0].startswith("**@Alex** ["), "default form"
    assert render_message(MSG, {"U1": "@Alex"}, heading=True)[0].startswith("### @Alex ["), "thread parent"
    assert render_message(MSG, {"U1": "@Alex"}, quoted=True)[0].startswith("> **@Alex** ["), "reply"
    assert "*Reactions: :tada: x2*\n" in render_message(MSG, {"U1": "@Alex"}), "reactions render"

    print("ok")


if __name__ == "__main__":
    demo()
