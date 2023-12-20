"""
 توجهات **
0. تمنا دارم قبل از اعمال تغییر تمامی مستندات پروژه رو مطالعه بفرمایید



1. به هیچ وجه به صورت دستی در سطح دیتابیس عملیاتی صورت نگیرد. چرا که لاگ آن
در جدول ActionLog ذخیره نشده و پیامد چنین رفتاری با توسعه دهنده است. عملیات
باید از طریق پنل مخصوص ادمین صورت گیرد (منظور Django admin panel  نیست بلکه
پنل مخصوص طراحی شده است)

قرارداد ها **
 1. تاریخ به صورت شمسی و با دیتا تایپ charfield در دیتابیس باید قرار بگیرد

2. تغییر در یک از state ها که شامل داده در دیتابیس می شود باید در جدول
ActionLog ثبت شود.

3. قیمت ها همه جا به تومان است
"""

from django.db import models


class SystemSetting(models.Model):
    """
    متغیر های سیستمی. برای مثال برای از دسترس خارج سیستم به جای اینکه
    برویم و توی IIS سیستم رو داون کنیم فیلد این جدول رو از 1 به صفر
    تغییر می دهیم و اینطوری دیگه سفارشی پردازش نمیشه

    کلا همه متغیر های زیر از طریق دیتابیس باید دستخوش تغییر قرار گیرند

    همه این کار ها شده تا کاربر حس بهتری به سیستم فعلی بکنه
    توجه شود که فقط یک رکورد از این جدول باید ساخته شود
    """

    IsSystemOpenForPersonnel = models.BooleanField(
        default=True,
        help_text=(
            "در صورت بسته بودن برای پرسنل استاتوس در دسترس نبودن سیستم "
            "به کاربر نمایش "
            "داده می شود "
            "و ریکوعست های سمت بک پردازش نمی شوند"
        ),
    )
    IsSystemOpenForAdmin = models.BooleanField(
        default=True, help_text="مانند فیلد بالا"
    )
    SystemUpdating = models.BooleanField(
        default=False,
        help_text=(
            "هنگام آپدیت کردن سیستم گزینه را فعال کرده تا به یوزر "
            "نشان دهد که سیستم در حال آپدیت شدن است و امکان ثبت سفارش "
            "فعال نیست"
        ),
    )

    # برای ارسال لاگ به ادمین سیستم استفاده می شود و از طریق دیتابیس قابل
    # تغییر است ضمن اینکه می دونم خیلی بده ولی باید به صورت زیر باشه
    # "heshmat@eit,kabud@eit,abud@eit"
    SuperAdmins = models.CharField(max_length=250, null=True)

    BreakfastRegistrationWindowHours = models.IntegerField(
        default=0,
    )
    BreakfastRegistrationWindowDays = models.IntegerField(
        default=0,
    )

    LaunchRegistrationWindowHours = models.IntegerField(
        default=0,
    )
    LaunchRegistrationWindowDays = models.IntegerField(
        default=0,
    )

    IsSystemOpenForLaunchSubmission = models.BooleanField(
        default=False,
        help_text="سیستم خدمات مربوط به ناهار را انجام می دهد یا خیر",
    )

    IsSystemOpenForBreakfastSubmission = models.BooleanField(
        default=True,
        help_text="سیستم خدمات مربوط به صبحانه را انجام می دهد یا خیر",
    )

    TotalItemsCanOrderedForBreakfastByPersonnel = models.PositiveSmallIntegerField(
        null=True,
        default=1,
        help_text=(
            "در حال حاضر با توجه به قوانین واحد اداری هر فرد "
            "از منوی صبحانه فقط یک ایتم می تونه سفارش بده."
            "این فیلد جمع ایتم های قابل سفارش برای صبحانه را "
            "تعیین می کند"
        ),
    )

    @property
    def SuperAdminUsername(self):
        return (
            self.SuperAdmins.replace(" ", "").split(",")
            if self.SuperAdmins
            else []
        )


class Holiday(models.Model):
    """
       روز های تعطیلی رسمی کشور.
       عملیات غیر از Read روی این جدول به صورت معمول صورت گرفته نمی شود.
    احتمالا تاریخ تعطیلات رسمی کشور سال به سال در این جدول ورود اطلاعات خواهد شد
    """

    HolidayDate = models.CharField(max_length=10, verbose_name="تاریخ")

    @property
    def HolidayYear(self): ...

    @property
    def HolidayMonth(self): ...

    @property
    def HolidayDay(self): ...

    def __str__(self) -> str:
        return self.HolidayDate

    class Meta:
        verbose_name = "تعطیل رسمی"
        verbose_name_plural = "تعطیلات رسمی"


class Category(models.Model):
    """دسته بندی ایتم های قابل سفارش در این جدول قرار می گیرند
    توجه کنید که هر ایتم قابل سفارشی می تواند شامل دسته بندی باشد

    برای مثال پک قاشق و چنگال نیز می تواند در دسته اضافات قرار گیرد"""

    CategoryName = models.CharField(
        max_length=300, verbose_name="نام دسته بندی"
    )

    def __str__(self):
        return self.CategoryName

    class Meta:
        verbose_name = "دسته بندی ایتم"
        verbose_name_plural = "دسته بندی ایتم ها"


class Subsidy(models.Model):
    """مقدار یارانه یا سهم فناوران از سفارش به صورت روزانه


    نکات مربوط به لاچیک سوبسید شرکت:

    1. یارانه به صورت روزانه تعلق می گیرد به سفارش و امکان انباشت آن وجود
    ندارد

    2. در صورتی که فرد مورد نظر سفارشی با مبلغ کمتر از حد سوبسید خریداری
    کند از سهم فناوران چیزی به وی عودت داده نمی شود

    3. قرار داد ثبت تاریخ ها به صورت زیر تا در زمان query گیری از دیتابیس
    سهل الوصول تر باشد


    id   fromDate        untilDate      amount
    ------------------------------
    1    1402/02/05      1402/02/12     12
    2    1402/02/13      null           15

    توجه 1: روز 5 و 12 اردیبهشت ماه نیز با یارانه 12 حساب
    می شود
    توجه 2: ستونی که untildate آن null است سهم سوبسید فعلی را نشان می دهد
    """

    Amount = models.PositiveIntegerField(verbose_name="سهم فناوران به تومان")
    FromDate = models.CharField(max_length=10, verbose_name="تاریخ شروع")
    UntilDate = models.CharField(
        max_length=10,
        null=True,
        verbose_name="تاریخ پایان",
        help_text="خود تاریخ شروع و پایان نیز با همین سوبسید محاسبه می شود",
    )

    def current_subsidy_amount(self) -> int:
        """میزان سوبسید فعلی شرکت"""
        ...

    def __str__(self): ...

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["UntilDate"], name="untildate_unique"
            )
        ]
        verbose_name = "یارانه"
        verbose_name_plural = "یارانه ها"


class Item(models.Model):
    """هر چیز قابل سفارش دادن
    می تواند غذا باشد یا نوشیدنی / پک قاشق چنگال مثلا و ...
    """

    class MealTypeChoices(models.TextChoices):
        """برای مشخص کردن زمان سرو یک وعده غذایی از انتخاب های زیر استفاده
        می کنیم

        توجه**********: در صورت سینتکس کد باید کد متناظر در  فرانت هم
        بازنویسی شود!!!!
        پس با احتیاط عمل کن دوست خوب من
        """

        BREAKFAST = "BRF", "صبحانه"
        LAUNCH = "LNC", "ناهار"

    ItemName = models.CharField(max_length=500, verbose_name="نام ایتم")
    Category = models.ForeignKey(
        "Category", on_delete=models.CASCADE, verbose_name="دسته بندی"
    )
    MealType = models.CharField(
        choices=MealTypeChoices.choices,
        default=MealTypeChoices.BREAKFAST,
        max_length=3,
    )
    ItemDesc = models.TextField(blank=True, null=True, verbose_name="شرح ایتم")
    IsActive = models.BooleanField(default=True, help_text="")  # todo
    Image = models.ImageField(
        upload_to="media/items/",
        null=True,
        blank=True,
        help_text=(
            "در صورتی که عکس آپلود نشود سیستم به صورت خودکار عکس پیشفرض "
            "قرار می دهد"
        ),
    )

    # این فیلد نباید قابل تغییر توسط ادمین و یا حتی DBA باشد. تغییرات این
    # فیلد باید در صورت اضافه کردن رکورد جدید در جدول ItemPriceHistory صورت
    # بگیرد
    CurrentPrice = models.PositiveIntegerField(
        verbose_name="قیمت فعلی آیتم به تومان",
        help_text=(
            "برای تغییر این فیلد باید رکورد جدید در تاریخچه قیمت "
            "مربوط به این آیتم ایجاد کنید"
        ),
    )

    def __str__(self):
        return self.ItemName

    class Meta:
        verbose_name = "اطلاعات ایتم"
        verbose_name_plural = "اطلاعات ایتم ها"


class DeliveryPlaceChoices(models.TextChoices):
    PADIDAR = "PAD", "ساختمان پدیدار"
    GAN = "GAN", "ساختمان گاندی"


class Order(models.Model):
    """
    *** PersonnelDebt = TotalPrice - SubsidyCap
    توجه شود که PersonnelDebt هیچ گاه منفی نخواهد شد
    """

    Id = models.PositiveIntegerField(primary_key=True)
    Personnel = models.CharField(max_length=250, verbose_name="پرسنل")
    FirstName = models.CharField(max_length=250, verbose_name="نام")
    LastName = models.CharField(max_length=250, verbose_name="نام خانوادگی")
    DeliveryDate = models.CharField(max_length=10, verbose_name="سفارش برای")
    # DeliveryPlace = models.CharField(
    #     max_length=3,
    #     help_text=(
    #         "محل تحویل سفارش فرقی نمی کند که صبحانه باشد یا ناهار. هر "
    #         "چیزی که سفارش دهید یک جا تحویل می گیرید که از جدول "
    #         "OrderItem خوانده می شود"
    #     ),
    # )
    SubsidyCap = models.PositiveIntegerField(
        verbose_name="یارانه فناوران به تومان"
    )
    TotalPrice = models.PositiveIntegerField(
        verbose_name="مبلغ کل سفارش به تومان"
    )
    PersonnelDebt = models.PositiveIntegerField(verbose_name="بدهی به تومان")
    SubsidySpent = models.PositiveIntegerField(
        verbose_name="خرج فناوران"
    )  # TODO help text.
    openForBreakfast = models.BooleanField()
    openForLaunch = models.BooleanField()

    class Meta:
        managed = False
        db_table = "Order"
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"


class OrderItem(models.Model):
    """ایتم های سفارش داده شده برای کاربران"""

    Personnel = models.CharField(max_length=250, verbose_name="پرسنل")
    DeliveryDate = models.CharField(max_length=10, verbose_name="سفارش برای")
    # DeliveryPlace = models.CharField(
    #     max_length=3,
    #     choices=DeliveryPlaceChoices.choices,
    #     help_text=(
    #         "محل تحویل سفارش فرقی نمی کند که صبحانه باشد یا ناهار. هر "
    #         "چیزی که سفارش دهید یک جا تحویل می گیرید"
    #     ),
    # )
    Item = models.ForeignKey(
        Item, on_delete=models.CASCADE, verbose_name="آیتم"
    )
    Quantity = models.PositiveSmallIntegerField(
        default=1, verbose_name="تعداد"
    )

    # که از قیمت فعلی آیتم گرفته شده و در اینجا وارد می شود
    # افزونگی تکنیکی
    PricePerOne = models.PositiveIntegerField(verbose_name="قیمت به تومان")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["Personnel", "DeliveryDate", "Item"],
                name="unique_item_date_personnel",
            ),
        ]
        verbose_name = "آیتم سفارشی"
        verbose_name_plural = "آیتم های سفارشی"


class ItemsOrdersPerDay(models.Model):
    """
    ویوو زیر نمایان این که ایتم های روزانه ای که توسط اداری ثبت شده است تا
    به حال چند عدد ثبت سفارش گرفته است؟‌
    در صورتی که ایتمی ثبت سفارش نداشته باشد عدد 0 به عنوان TotalOrders
    بازگردانده می شود
    """

    Id = models.PositiveIntegerField(primary_key=True)
    Item = models.PositiveIntegerField(verbose_name="آیتم")
    Date = models.CharField(max_length=10, verbose_name="سفارش برای")
    TotalOrders = models.PositiveIntegerField(verbose_name="مجموع سفارش ها")

    class Meta:
        managed = False
        db_table = "ItemsOrdersPerDay"
        verbose_name = "تعداد سفارش بر حسب آیتم"
        verbose_name_plural = "تعداد سفارشات بر حسب آیتم"


class ItemPriceHistory(models.Model):
    """
    این جدول تاریخچه تغییر قیمت اقلام را نگه می دارد و لاگ ان در جدول
    جداگانه ذخیره می شود

    توجه شود که تاریخ شروع و پایان یک رکورد نیز با همان قیمت حساب می شود
    """

    Item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        verbose_name="ایتم",
    )

    Price = models.PositiveIntegerField(verbose_name="قیمت به تومان")
    FromDate = models.CharField(max_length=10, verbose_name="تاریخ شروع")
    UntilDate = models.CharField(
        max_length=10,
        null=True,
        verbose_name="تاریخ پایان",
        help_text=(
            "توجه شود که تاریخ شروع و پایان یک رکورد نیز با همان قیمت حساب"
            " می شود"
        ),
    )

    def __str__(self):
        return f"{self.Item.ItemName} {self.Price}"

    class Meta:
        verbose_name = "تاریخچه قیمت آیتم"
        verbose_name_plural = "تاریخچه قیمت آیتم ها"


class DailyMenuItem(models.Model):
    """
    اطلاعات غذای قابل سفارش در هر روز را مشخص می کند
    """

    AvailableDate = models.CharField(
        max_length=10, verbose_name="قابل سفارش برای"
    )
    Item = models.ForeignKey(
        Item, on_delete=models.CASCADE, verbose_name="ایتم"
    )
    IsActive = models.BooleanField(help_text="", default=True)  # todo

    @property
    def AvailableYear(self): ...

    @property
    def AvailableMonth(self): ...

    @property
    def AvailableDay(self): ...

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["AvailableDate", "Item"],
                name="unique_AvailableDate_Item",
            )
        ]
        verbose_name = "منو"
        verbose_name_plural = "منو ها"


class ActionLog(models.Model):
    """لاگ هر عملی که در این سیستم انجام شود در این جدول ذخیره  می شود
    اکشن ها قابل توسعه هستند

    --------------------------
     برای مثال فرض کنیم که برای تعداد غذا های قابل سفارش در یک روز محدودیت
     بگذاریم. مثلا 80 تا جوجه و 240 تا کوبیده

     در صورتی که اداری تصمیم بگیرد ظرفیت غذا ها را تغییر دهد عملی به نام
     تغییر ظرفیت غذا تعریف می شود به شرح زیر


     CHANGE_FOOD_LIMITATION = "CFL", "CHANGE FOOD LIMITATION"

     در ویوو مربوط هنگام عوض کردن STATE (دیتا) باید لاگ به صورت زیر ذخیره کنند

     ActionLog.objects.create(
        User= AuthenticatedUser,
        ActionCode= ObjectChoices.CHANGE_FOOD_LIMITATION,
        ActionDesc= "ظرفیت جوجه برای روز 1402/08/15 از 80 به 180 تغییر کرد"
        AdminActionReason= "طی تماس با رستوران افزایش ظرفیت اعمال شد"
     )

     --------------------------
    درباره ActionDesc: توضیح اصلی که  هنگام رخداد این عمل/ این عمل چه
    دیتایی تغییر کرده است یا به صورت کلی چه اتفاقی افتاده است به صورت کاملا
    شفاف باید بیان شود و طراحی ساختار پیام به عهده توسعه دهنده است

    --------------------------
    درباره AdminActionReason: سیستم, مخصوصا  سیستم ثبت / لغو و تغییر سفارش
    به گونه ای طراحی شده است تا نیازی به دخالت ادمین در این روند نباشد. در
    صورتی که به هر طریقی ادمین (اداری و یا تیم سامانه های ستادی) در این
    روند تغییری ایجاد کرده و یابه نحوی دخالت کنند باید دلیل این امر به صورت
    شفاف در این فیلد ذکر شود

    نکته مهم درباره فیلد AdminActionReason این است که  اجبار برای مقدار گرفتن
    این فیلد در سطح دیتابیس صورت نمی گیرد(null=True) و توسعه دهنده باید آن را
    هندل کند(هر جا که ادمین در حال اعمال تغییر بود باید این فیلد required شود)

    --------------------------
    به صورت خلاصه کنار اکشن هایی که نیاز است در صورت تغییر آن توسط ادمین
    دلیل آن نیز (AdminActionReason)ثبت شود نوشته REASON_REQUIRED کامنت شده است


    """

    # class ActionType(models.TextChoices):
    #     CREATE = "CREATE" "ساختن"
    #     READ = "READ" "خواندن"
    #     UPDATE = "UPDATE" "بروز رسانی"
    #     DELETE = "پاک کردن"
    #
    # # class ActionChoices(models.TextChoices):
    # #     ORDER_CREATION = "ORDER_CREATION", "سفارش جدید"
    # #     ORDER_MODIFICATION = (
    # #         "ORDER_MODIFICATION",
    # #         "تغییر سفارش",
    # #     )  # REASON_REQUIRED
    # #
    # #     # DELETE = "DEL", "DELETE"
    # #     # UPDATE = "UPT", "UPDATE"
    # #     # CANCEL = "CN", "CANCEL"
    # #     # EMAIL_TO_SUPER_ADMIN = ""
    # #     # EMAIL_TO_ADMIN = ""
    #
    # ActionAt = models.DateTimeField(auto_now_add=True)
    #
    # # در صورتی که سیستم به صورت خودکار اقدام به ثبت لاگ کرده باشد باید کاربر
    # # به صورت "SYSTEM" ثبت شود
    # User = models.CharField(max_length=250)
    # TabelName = models.CharField(max_length=50)
    # ReferencedRecordId = models.PositiveIntegerField()
    # ActionType = models.CharField(choices=ActionType.choices)
    #
    # ActionDesc = models.CharField(max_length=1000)
    # AdminActionReason = models.TextField(null=True)  # combo
    # OldData = models.JSONField(...)
    # # NewData = models.JSONField(...)


# class ItemDailyReport(models.Model):
#     Id = models.PositiveIntegerField(primary_key=True)
#     ItemName = models.CharField(max_length=500, verbose_name="نام ایتم")
#     DeliveryDate = models.CharField(max_length=10, verbose_name="سفارش برای")
#     PAD = models.CharField(max_length=3, verbose_name="ساختمان پدیدار")
#     OTH = models.CharField(max_length=3, verbose_name="ساختمان دیگر")

#     class Meta:
#         managed = False
#         db_table = "ItemDailyReport"
#         verbose_name = "گزارش سفارش روزانه"
#         verbose_name_plural = "گزارش سفارشات روزانه"


class PersonnelDailyReport(models.Model):
    Id = models.PositiveIntegerField(primary_key=True)
    Personnel = models.CharField(max_length=250)
    FirstName = models.CharField(max_length=250)
    LastName = models.CharField(max_length=250)
    TeamName = models.CharField(max_length=250)
    RoleName = models.CharField(max_length=250)
    ItemName = models.CharField(max_length=500, verbose_name="نام ایتم")
    Quantity = models.PositiveSmallIntegerField()
    DeliveryDate = models.CharField(max_length=10, verbose_name="سفارش برای")

    class Meta:
        managed = False
        db_table = "PersonnelDailyReport"

    def __str__(self) -> str:
        return self.Personnel
