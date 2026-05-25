def side_effect(msg):
    # type: (str) -> None
    print(msg)


def no_type_info(data):
    return data


class Widget:
    def render(self):
        # type: () -> str
        return "<widget/>"

    def on_click(self, handler, context):
        # type: (Callable) -> None
        handler(context)
