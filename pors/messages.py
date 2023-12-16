class Message:
    """
    it's a very simple class to handle the msgs for displaying in front.

    Examples:
        You have to instantiated in view module for once.

        ```
        m=Message()
        def some_view(request):
            m.add_message(
            "قرمه سبزی به سفارش امروز اضافه شد"
            ,Message.SUCCESS
            ,Message.DT_SHORT
            )
            return Response ({"data":date, "messages":m.messages()})
        ```

    Warnings:

        * BE CAREFUL THAT AFTER CALLING THE messages() METHOD THE _messages ATTR GET FLUSHED.
        * use messages() only in return statements
    """

    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    INFO = "INFO"
    ANNOUNCEMENT = "ANNOUNCEMENT"

    # The exact duration(in millisecond i guess) of these consts are defined
    # in the JS file, simply search it with the values
    DT_SHORT = "DISPLAY_TIME_SHORT"
    DT_TEN = "DISPLAY_TIME_TEN"
    DT_LONG = "DISPLAY_TIME_LONG"
    DT_PARAMENT = "DISPLAY_TIME_PARAMENT"

    def __init__(self):
        self._messages: list[dict[str, str]] = []

    def add_message(self, message: str, level=INFO, display_duration=DT_SHORT):
        self._messages.append(
            {
                "level": level,
                "message": message,
                "displayDuration": display_duration
            }
        )

    def messages(self):
        temp = self._messages
        # clear the messages list
        self._messages = []
        return temp
