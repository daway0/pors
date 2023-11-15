"""
 توجهات **
0. تمنا دارم قبل از اعمال تغییر تمامی مستندات پروژه رو مطالعه بفرمایید



1. به هیچ وجه به صورت دستی در سطح دیتابیس عملیاتی صورت نگیرد. چرا که لاگ آن
در جدول ActionLog ذخیره نشده و پیامد چنین رفتاری با توسعه دهنده است. عملیات
باید از طریق پنل مخصوص ادمین صورت گیرد (منظور Django admin panel  نیست بلکه
پنل مخصوص طراحی شده است)

قرارداد ها **
 1. تاریخ به میلادی در دیتابیس ذخیره می شود در صورت نیاز از calculate  فیلد ها
 ویا view  ها دیتابیسی استفاده شود

2. تغییر در یک از state ها که شامل داده در دیتابیس می شود باید در جدول
ActionLog ثبت شود.

"""

from django.db import models


class Holiday(models.Model):
    """
    روز های تعطیلی
    تعطیلات رسمی و غیر رسمی مانند آلودگی هوا / سرمای هوا / مشکلات شرکت و غیره

    پنج شنبه ها و جمعه ها در این جدول آورده نمی شوند و با پکیج JDATETIME
    محاسبه می شوند

    در صورتی که تعطیلی رسمی نباشد (IsOfficial=False) باید علت تعطیلی ذکر
    شود (Reason باید مقدار گیرد)

    """

    HolidayDate = models.CharField(max_length=10)

    @property
    def HolidayYear(self):
        ...

    @property
    def HolidayMonth(self):
        ...

    @property
    def HolidayDay(self):
        ...


class Category(models.Model):
    """دسته بندی ایتم های قابل سفارش در این جدول قرار می گیرند
    توجه کنید که هر ایتم قابل سفارشی می تواند شامل دسته بندی باشد

    برای مثال پک قاشق و چنگال نیز می تواند در دسته اضافات قرار گیرد"""

    class Meta:
        verbose_name = "دسته بندی ایتم"
        verbose_name_plural = "دسته بندی ایتم ها"

    CategoryName = models.CharField(
        max_length=300, verbose_name="نام دسته بندی"
    )

    def __str__(self):
        return self.CategoryName


class Subsidy(models.Model):
    """مقدار یارانه یا سهم فناوران از سفارش به صورت روزانه

    #todo
    منتقل شه به دیزاین داک
    نکات مربوط به لاچیک سوبسید شرکت:

    1. یارانه به صورت روزانه تعلق می گیرد به سفارش و امکان انباشت آن وجود
    ندارد

    ---------------
    در باره نحوه محسابه یارانه سفارش ها:
    فرض کنیم در جدول سوبسید رکورد ها زیر را داریم

    1 10000   1402/05/06  0
    2 20000   1402/11/06  0
    3 30000   1403/05/06  0
    4 50000   1403/11/06  1

    هر سفارشی که در سیستم ثبت می شود دارای سوبسید است بنابراین فقط کافیست
    که تاریخ اعمال سفارش یعنی DeliveryDate با مدت زمان فعال بودن سوبسید چک شود
    مثال:

    فرض کنیم که DeliveryDate برای سفارشی 1402/12/09 باشد سیستم باید چک کند
    که برای این سفارش کدام سوبسید باید در نظر گرفته شود.
    سوبسید 2 یارانه مد نظر است
    """

    Amount = models.PositiveIntegerField()
    FromDate = models.CharField(max_length=10)
    UntilDate = models.CharField(
        max_length=10,
        null=True,
        unique=True,
        help_text=(
            "برای تاکید کردن روی غیر قابل استفاده بودن سوبسید این "
            "فیلد باید False شود در واقع این محدودیت دیتابیسی است که "
            "منطق unique بودن سوبسید فعال را تضمین می کند"
        ),
    )


class Item(models.Model):
    """هر چیز قابل سفارش دادن
    می تواند غذا باشد یا نوشیدنی / پک قاشق چنگال مثلا و ...

    #todo
    درباره IsActive: توجه شود که هنگام سفارش دادن یک غذا باید فیلد IsActive
     برای دو مدل چک شود هم مدل Item و هم مدل PriceItemHistory
     در صورتی که برای هر دو مدل IsActive=True بود امکان اضافه کردن به سفارش
     وجود دارد

    """

    class Meta:
        verbose_name = "اطلاعات ایتم"
        verbose_name_plural = "اطلاعات ایتم ها"

    ItemName = models.CharField(max_length=500, verbose_name="نام ایتم")
    Category = models.ForeignKey(
        "Category", on_delete=models.CASCADE, verbose_name="دسته بندی"
    )
    ItemDesc = models.TextField(blank=True, null=True)
    IsActive = models.BooleanField(default=True)

    # در صورتی که غذایی عکس نداشت باید به صورت پیش فرض به کلاینت عکس دهیم
    Image = models.CharField(max_length=500, null=True, blank=True)
    CurrentPrice = models.PositiveIntegerField()

    def __str__(self):
        return self.ItemName


class Order(models.Model):
    Personnel = models.CharField(max_length=250)
    DeliveryDate = models.CharField(max_length=10)
    IsDeleted = models.BooleanField(
        default=True, help_text="IsDeleted?(Soft Delete)"
    )
    AppliedSubsidy = models.PositiveIntegerField()

    @property
    def get_data(self):
        """برای اینکه ویرایش یک سفارش را به صورت لاگ در دیتابیس ثبت کنیم
        نیاز داریم تا اطلاعات قبل و بعد از اصللاح را داشته باشیم بنابراین
        از این برای دریافت دیتا به صورت json برای ثبت در لاگ استفاده می کنیم"""
        ...


class OrderItem(models.Model):
    OrderedItem = models.ForeignKey(Item, on_delete=models.CASCADE)
    Quantity = models.PositiveSmallIntegerField(default=1)
    PricePerOne = models.PositiveIntegerField()
    Order = models.ForeignKey(Order, on_delete=models.CASCADE)


class ItemPriceHistory(models.Model):
    """به توجه به تغییر قسمت ایتم ها در طول زمان وجود این جدول ضروری است
    این جدول تاریخچه تغییر قیمت اقلام را نگه می دارد و لاگ ان در جدول
    جداگانه ذخیره می شود"""

    Item = models.ForeignKey(
        Item, on_delete=models.CASCADE, null=False, blank=False
    )

    Price = models.PositiveIntegerField()
    FromDate = models.CharField(max_length=10)
    UntilDate = models.CharField(max_length=10, null=True, unique=True)

    def __str__(self):
        return f"{self.Item.ItemName} {self.Price}"


class DailyMenuItem(models.Model):
    """
    اطلاعات غذای قابل سفارش در هر روز را مشخص می کند.
     بدیهی است که ارتباط این جدول با ItemPrice است و نه Item
     به این علت که غذای قابل سفارش باید رفرنس به قیمت روز غذا را باید داشته
     باشد
    """

    AvailableDate = models.CharField(max_length=10)
    Item = models.ForeignKey(Item, on_delete=models.CASCADE)
    IsActive = models.BooleanField(default=True)

    @property
    def AvailableYear(self):
        ...

    @property
    def AvailableMonth(self):
        ...

    @property
    def AvailableDay(self):
        ...


# class ActionLog(models.Model):
#     """لاگ هر عملی که در این سیستم انجام شود در این جدول ذخیره  می شود
#     اکشن ها قابل توسعه هستند
#
#     --------------------------
#      برای مثال فرض کنیم که برای تعداد غذا های قابل سفارش در یک روز محدودیت
#      بگذاریم. مثلا 80 تا جوجه و 240 تا کوبیده
#
#      در صورتی که اداری تصمیم بگیرد ظرفیت غذا ها را تغییر دهد عملی به نام
#      تغییر ظرفیت غذا تعریف می شود به شرح زیر
#
#
#      CHANGE_FOOD_LIMITATION = "CFL", "CHANGE FOOD LIMITATION"
#
#      در ویوو مربوط هنگام عوض کردن STATE (دیتا) باید لاگ به صورت زیر ذخیره کنند
#
#      ActionLog.objects.create(
#         User= AuthenticatedUser,
#         ActionCode= ObjectChoices.CHANGE_FOOD_LIMITATION,
#         ActionDesc= "ظرفیت جوجه برای روز 1402/08/15 از 80 به 180 تغییر کرد"
#         AdminActionReason= "طی تماس با رستوران افزایش ظرفیت اعمال شد"
#      )
#
#      --------------------------
#     درباره ActionDesc: توضیح اصلی که  هنگام رخداد این عمل/ این عمل چه
#     دیتایی تغییر کرده است یا به صورت کلی چه اتفاقی افتاده است به صورت کاملا
#     شفاف باید بیان شود و طراحی ساختار پیام به عهده توسعه دهنده است
#
#     --------------------------
#     درباره AdminActionReason: سیستم, مخصوصا  سیستم ثبت / لغو و تغییر سفارش
#     به گونه ای طراحی شده است تا نیازی به دخالت ادمین در این روند نباشد. در
#     صورتی که به هر طریقی ادمین (اداری و یا تیم سامانه های ستادی) در این
#     روند تغییری ایجاد کرده و یابه نحوی دخالت کنند باید دلیل این امر به صورت
#     شفاف در این فیلد ذکر شود
#
#     نکته مهم درباره فیلد AdminActionReason این است که  اجبار برای مقدار گرفتن
#     این فیلد در سطح دیتابیس صورت نمی گیرد(null=True) و توسعه دهنده باید آن را
#     هندل کند(هر جا که ادمین در حال اعمال تغییر بود باید این فیلد required شود)
#
#     --------------------------
#     به صورت خلاصه کنار اکشن هایی که نیاز است در صورت تغییر آن توسط ادمین
#     دلیل آن نیز (AdminActionReason)ثبت شود نوشته REASON_REQUIRED کامنت شده است
#
#
#     """
#
#     class ActionType(models.TextChoices):
#         # crud
#         ...
#
#     # class ActionChoices(models.TextChoices):
#     #     ORDER_CREATION = "ORDER_CREATION", "سفارش جدید"
#     #     ORDER_MODIFICATION = (
#     #         "ORDER_MODIFICATION",
#     #         "تغییر سفارش",
#     #     )  # REASON_REQUIRED
#     #
#     #     # DELETE = "DEL", "DELETE"
#     #     # UPDATE = "UPT", "UPDATE"
#     #     # CANCEL = "CN", "CANCEL"
#     #     # EMAIL_TO_SUPER_ADMIN = ""
#     #     # EMAIL_TO_ADMIN = ""
#
#     ActionAt = models.DateTimeField(auto_now_add=True)
#
#     # در صورتی که سیستم به صورت خودکار اقدام به ثبت لاگ کرده باشد باید کاربر
#     # به صورت "SYSTEM" ثبت شود
#     User = models.CharField(max_length=250)
#     TabelName = models.CharField(max_length=50)
#     ReferencedRecordId = models.PositiveIntegerField()
#     ActionType = models.CharField(choices=ActionType.choices)
#
#     ActionDesc = models.CharField(max_length=1000)
#     AdminActionReason = models.TextField(null=True)  # combo
#     OldData = models.JSONField(...)
#     NewData = models.JSONField(...)
