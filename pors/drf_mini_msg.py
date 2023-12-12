class Msg:
    """
    it's a very simple class to handle the msgs for displaying in front.

    Examples:
        You have to instantiated in view module for once.

        ```
        m=Msg()
        def some_view(request):
            m.add_msg(
            "قرمه سبزی به سفارش امروز اضافه شد"
            ,Msg.SUCCESS
            ,Msg.DT_SHORT
            )
            return Response ({"data":date, "messages":m.msgs()})
        ```

    Warnings:

        * BE CAREFUL THAT AFTER CALLING THE msgs() METHOD THE _msgs ATTR GET FLUSHED.
        * use msgs() only in return statements
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
        self._msgs: list[dict[str, str]] = []

    def add_msg(self, msg: str, lvl=INFO, display_duration=DT_SHORT):
        self._msgs.append(
            {
                "level": lvl,
                "msg": msg,
                "displayDuration": display_duration
            }
        )

    def msgs(self):
        temp = self._msgs
        # clear the msgs list
        self._msgs = []
        return temp
