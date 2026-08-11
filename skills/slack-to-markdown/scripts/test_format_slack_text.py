"""Self-check for format_slack_text emphasis handling.

Run: python3 scripts/test_format_slack_text.py
"""
from export_slack import format_slack_text


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

    print("ok")


if __name__ == "__main__":
    demo()
