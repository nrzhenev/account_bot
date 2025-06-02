def pd(d: dict):
    for key, val in d.items():
        print(f"{key}: {val}")


def pl(l: list):
    for i in l:
        print(i)


TEXT_PARSERS = {"HTML": {"underline": lambda x: f"<u>{x}</u>",
                         "bold": lambda x: f"<b>{x}</b>",
                         "italic": lambda x: f"<i>{x}</i>"}
                }