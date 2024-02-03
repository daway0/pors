import datetime
import json
from os import getenv

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db import models





def ConstValueChoice(ConstType):
    ParentId = ConstValue.objects.filter(Code=ConstType)
    choice = {"IsActive": True}  # , "Parent_Id": ParentId[0].id}
    return choice


class Province(models.Model):
    """استان های ایران"""
    class Meta:
        verbose_name = "استان"
        verbose_name_plural = "استان ها"

    ProvinceTitle = models.CharField(max_length=50, verbose_name="نام استان", unique=True)
    AbbreviationCode = models.CharField(max_length=2, verbose_name="کد استان", null=True, blank=True)
    PhoneCode = models.IntegerField(verbose_name="پیش شماره استان", null=True, blank=True)



class City(models.Model):
    """شهر های استان"""
    class Meta:
        verbose_name = "شهر"
        verbose_name_plural = "شهرها"

    Province = models.ForeignKey("Province", verbose_name="استان مربوطه", on_delete=models.CASCADE, default=8)
    CityTitle = models.CharField(max_length=100, verbose_name="نام شهر")

    IsCapital = models.BooleanField(verbose_name="مرکز استان است؟", default=False)
    CityCode = models.CharField(max_length=4, verbose_name="کد شهر", null=True, blank=True)



class CityDistrict(models.Model):
    """مناطق شهری، برای مثال تهران دارای مناطق 22 گانه است"""
    class Meta:
        verbose_name = "ناحیه شهری"
        verbose_name_plural = "نواحی شهری"

    City = models.ForeignKey("City", verbose_name="شهر مربوطه",
                             on_delete=models.CASCADE)
    DistrictTitle = models.CharField(max_length=50, verbose_name="نام منطقه")


# class MilitaryService(models.Model):
#     class Meta:
#         verbose_name = 'وضعیت پایان خدمت'
#         verbose_name_plural = 'وضعیت های پایان خدمت'
#
#     MilitaryService = models.CharField(max_length=300, verbose_name='وضعیت')



class Users(models.Model):
    """جدول اطلاعات پرسنل که شامل تمامی پرسنل حال و گذشته است"""
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        db_table = 'Users'

    # username = None
    # AuthLoginKey = models.CharField(max_length=300, null=True, blank=True)
    # AuthLoginDate = models.CharField(default=None, null=True, max_length=100, blank=True)
    UserName = models.CharField(primary_key=True, max_length=100, verbose_name='نام کاربری')
    # password = models.CharField(max_length=300,null=True,blank=True)
    FirstName = models.CharField(max_length=200, verbose_name='نام')
    LastName = models.CharField(max_length=200, verbose_name='نام خانوادگی')
    FirstNameEnglish = models.CharField(max_length=80, verbose_name="نام لاتین", null=True, blank=True)
    LastNameEnglish = models.CharField(max_length=100, verbose_name="نام خانوادگی لاتین", null=True, blank=True)
    FatherName = models.CharField(max_length=200, null=True, blank=True, verbose_name='نام پدر')
    ContractDate = models.DateField(null=True, blank=True, verbose_name='تاریخ شروع همکاری')
    ContractEndDate = models.DateField(null=True, blank=True, verbose_name='تاریخ پایان همکاری')
    ContractType = models.ForeignKey(to='ConstValue', on_delete=models.SET_NULL, null=True, related_name='ContractType'
                                     ,verbose_name='نوع قرارداد')
    About = models.CharField(max_length=1000, verbose_name="درباره من", null=True, blank=True)
    Gender = models.BooleanField(default=False, verbose_name='جنسیت')
    LivingAddress = models.ForeignKey("PostalAddress", verbose_name="آدرس محل سکونت", on_delete=models.SET_NULL,
                                      null=True, blank=True)
    # is_staff = models.BooleanField(default=True)
    # is_active = models.BooleanField(default=True)
    # is_superuser = models.BooleanField(default=False)

    # NotEducated = 0
    # ElementarySchool = 1
    # PreHighSchool = 2
    # Diploma = 3
    # Collage = 4
    # Bachelor = 5
    # Master = 6
    # Phd = 7
    # Education_Choices = [(NotEducated, "بی سواد"), (ElementarySchool, "ابتدایی"), (PreHighSchool, "دبیرستان"),
    #                      (Diploma, "دیپلم"), (Collage, "کاردانی"), (Bachelor, "کارشناسی"), (Master, "کارشناسی ارشد"),
    #                      (Phd, "دکتری")]
    # DegreeType = models.IntegerField(choices=Education_Choices, null=True, blank=True, verbose_name='آخرین مقطع تحصیلی')
    DegreeType = models.ForeignKey('ConstValue', on_delete=models.PROTECT, null=True, blank=True,
                                    verbose_name='آخرین مقطع تحصیلی')
    CVFile = models.FileField(verbose_name="فایل رزومه", null=True, blank=True)
    # Address = models.CharField(max_length=2000, null=True, blank=True, verbose_name='آدرس')
    # Marriage_Single = 1
    # Marriage_Married = 2
    # Marriage_Divorced = 3
    # Marriage_Widow = 4
    # Marriage_Choices = ((Marriage_Single, "مجرد"), (Marriage_Married, "متاهل"), (Marriage_Divorced, "جدا شده"),
    #                     (Marriage_Widow, "فوت شده"))
    # MarriageStatus = models.PositiveSmallIntegerField(choices=Marriage_Choices, verbose_name="وضعیت تاهل",
    #                                                   default=Marriage_Single, blank=True, null=True)
    MarriageStatus = models.ForeignKey("ConstValue", verbose_name="وضعیت تاهل", on_delete=models.PROTECT,
                                        related_name='UsersMarriageStatus', null=True, blank=True)
    NumberOfChildren = models.PositiveSmallIntegerField(verbose_name="تعداد فرزند", default=0, null=True, blank=True)
    # MilitaryStatus = models.ForeignKey('MilitaryService', null=True, blank=True, on_delete=models.PROTECT,
    #                                    verbose_name='وضعیت خدمت')
    MilitaryStatus = models.ForeignKey("ConstValue", verbose_name='وضعیت خدمت', on_delete=models.PROTECT,
                                        related_name='UsersMilitaryStatus', null=True, blank=True)
    NationalCode = models.CharField(max_length=10, null=True, unique=True, blank=True,

                                    verbose_name="کد ملی")
    BirthDate = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')
    BirthCity = models.ForeignKey("City", verbose_name="شهر محل تولد",
                                  on_delete=models.CASCADE, null=True)
    IdentityNumber = models.CharField(max_length=10,null=True, blank=True, verbose_name='شماره شناسنامه')
    IdentityCity = models.ForeignKey("City", verbose_name="شهر محل صدور شناسنامه",
                                  on_delete=models.CASCADE, related_name='IdentityCity',null=True)
    IdentityRegisterDate = models.DateField(verbose_name='تاریخ صدور شناسنامه', null=True)
    IdentitySerialNumber = models.CharField(max_length=20,null=True, blank=True, verbose_name='سریال شناسنامه')
    InsuranceNumber = models.CharField(max_length=20 ,null=True, blank=True, verbose_name='شماره بیمه')
    Religion = models.ForeignKey("ConstValue", verbose_name="دین", on_delete=models.PROTECT,
                                 related_name='UsersReligion', null=True, blank=True)
    UserStatus = models.ForeignKey("ConstValue", verbose_name='وضعیت کاربر', null=True, on_delete=models.CASCADE,
                                   related_name="UserStatus")
    IsActive = models.BooleanField(default=True, verbose_name='کاربر فعال است؟')
    # USERNAME_FIELD = 'UserName'
    # objects = CustomUserManager()
    #
    # @property
    # def groups(self):
    #     cursor = connections['default'].cursor()
    #     try:
    #         cursor.execute("select * from auth_user where username=%s ", (self.UserName,))
    #         row = cursor.fetchone()
    #         user_id = row[0]
    #         cursor.execute("select * from auth_user_groups where user_id=%s", (user_id,))
    #         row = cursor.fetchall()
    #         if row is not None:
    #             rows = [item[2] for item in row]
    #             return Group.objects.filter(id__in=rows)
    #     except:
    #         cursor.close()
    #     finally:
    #         cursor.close()
    #
    #     return Group.objects.none()

    def __str__(self):
        return self.FirstName + ' ' + self.LastName



class PostalAddress(models.Model):
    """آدرس پرسنل"""
    class Meta:
        verbose_name = "آدرس پستی"
        verbose_name_plural = "آدرس های پستی"

    Title = models.CharField(max_length=100, verbose_name="عنوان", null=True, blank=True)
    City = models.ForeignKey("City", verbose_name="شهر محل زندگی",
                             on_delete=models.CASCADE)
    CityDistrict = models.ForeignKey("CityDistrict", verbose_name="منطقه", blank=True, null=True,
                                     on_delete=models.SET_NULL)
    AddressText = models.CharField(max_length=500, verbose_name="آدرس",  # validators=[jv.MinLengthValidator(20)],
                                   null=True, blank=True)
    No = models.CharField(max_length=20, verbose_name="پلاک", null=True, blank=True)
    UnitNo = models.PositiveSmallIntegerField(verbose_name="شماره واحد", null=True, blank=True)
    PostalCode = models.BigIntegerField(verbose_name="کد پستی", null=True, blank=True
                                        )

    Person = models.ForeignKey("Users", verbose_name="فرد", blank=True, null=True, on_delete=models.CASCADE)
    IsDefault = models.BooleanField(default=False, verbose_name='آدرس پیش فرض است؟')

    # موقعیت جغرافیایی اضافه شود
    # اصلاح شود که در صورت نال بودن هر قسمت آورده نشود. همچنین کلمه کد پستی در خروجی نمایش داده شود


class EmailAddress(models.Model):
    """ایمیل پرسنل"""
    class Meta:
        verbose_name = "آدرس پست الکترونیکی"
        verbose_name_plural = "آدرس های پست الکترونیکی"

    Email = models.EmailField(verbose_name="ادرس ایمیل")
    Title = models.CharField(max_length=100, verbose_name="عنوان", null=True, blank=True)
    Person = models.ForeignKey("Users", verbose_name="فرد", null=True, blank=True, on_delete=models.CASCADE)
    IsDefault = models.BooleanField(default=False, verbose_name='آدرس ایمیل پیشفرض است؟')





class PhoneNumber(models.Model):
    """شماره تماس پرسنل که می تواند شماره تماس همراه، محل سکونت و شماره تماس مواقع ضروری باشد"""
    class Meta:
        verbose_name = "شماره تماس"
        verbose_name_plural = "شماره های تماس"

    # City = models.ForeignKey("City", verbose_name="پیش شماره شهرستان", default=d.City,
    #                          null=True, blank=True, on_delete=models.SET_NULL)
    Province = models.ForeignKey("Province", verbose_name="استان",
                                 null=True, blank=True, on_delete=models.SET_NULL, help_text="این فیلد زمانی پر می شود که تلفن خط ثابت باشد")
    TelNumber = models.BigIntegerField(verbose_name="شماره تماس",
                                       help_text=" شماره ثابت بدون داخلی وارد شود. (مثلا : 87654321) شماره موبایل بدون صفر وارد شود مثلاً 9121234567",
                                       )
    # TelType_Mobile = 1
    # TelType_Home = 2
    # TelType_Work = 3
    # TelType_Emergency = 4
    # TelTypeChoices = ((TelType_Mobile, "تلفن همراه"), (TelType_Home, "منزل"), (TelType_Work, "محل کار"),
    #                   (TelType_Emergency, "ضروری"))
    # TelType2 = models.PositiveSmallIntegerField(choices=TelTypeChoices, verbose_name="نوع", null=True, blank=True)
    TelType = models.ForeignKey("ConstValue", verbose_name="نوع", on_delete=models.PROTECT, help_text="منظور از نوع این است که می تواند، محل زندگی، همراه، ضروری و... باشد")
    Title = models.CharField(max_length=50, verbose_name="توضیحات", blank=True, null=True)
    Person = models.ForeignKey("Users", verbose_name="فرد", blank=True, null=True, on_delete=models.CASCADE, related_name= 'phone_number')
    IsDefault = models.BooleanField(default=False, verbose_name='پیش فرض')

    # باید کنترل شود که اگر شماره تماس موبایل بود کد شهرستان وارد نشود
    # تعداد ارقام شماره موبایل چک شود
    # چک شود که شماره موبال با 9 شروع شود
    # تعداد ارقام شماره تلفن چک شود



class ConstValue(models.Model):
    """جدول مقادیر ثابت حاوی مقادیر کمکی است برای جداول دیگر برای مثال اطلاعات انواع آدرس ویا انواع قرارداد در این جدول قرار می گیرد و صرفا آیدی آنها به عنولن کلید خارجی استفاده می شود."""
    class Meta:
        verbose_name = "مقدار ثابت"
        verbose_name_plural = "مقادیر ثابت"
        ordering = ["Parent_id", "OrderNumber"]

    Caption = models.CharField(max_length=50, verbose_name="عنوان")
    Code = models.CharField(max_length=100, verbose_name="کد")
    Parent = models.ForeignKey("ConstValue", verbose_name="شناسه پدر", on_delete=models.CASCADE, null=True, blank=True)
    IsActive = models.BooleanField(verbose_name="فعال است؟", default=True)
    OrderNumber = models.PositiveSmallIntegerField(verbose_name="شماره ترتیب", null=True, blank=True, default=1)
    ConstValue = models.IntegerField(verbose_name="مقدار مربوطه"  # , validators=[jv.MinValueValidator(1)]
                                     , null=True,
                                     blank=True)



class University(models.Model):
    """دانشگاه محل تحصیل"""
    class Meta:
        verbose_name = "دانشگاه"
        verbose_name_plural = "دانشگاه ها"

    Title = models.CharField(max_length=150, verbose_name="نام دانشگاه")
    PublicUniversity = 1
    IslamicAzadUniversity = 2
    NoneProfit = 3
    UAST = 4
    PNU = 5
    Virtual = 6
    UniversityTypeChoice = ((PublicUniversity, "دولتی"), (IslamicAzadUniversity, "دانشگاه آزاد اسلامی"),
                            (NoneProfit, "غیرانتفاعی"), (UAST, "علمی و کاربردی"), (PNU, "پیام نور"), (Virtual, "مجازی"))
    UniversityType = models.PositiveSmallIntegerField(choices=UniversityTypeChoice, verbose_name="نوع دانشگاه",
                                                      null=True, blank=True, help_text="دیگر از این فیلد برای تعیین نوع دانشگاه استفاده نمی کنیم")
    University_Type = models.ForeignKey("ConstValue", verbose_name="نوع دانشگاه", on_delete=models.PROTECT,
                                        limit_choices_to=ConstValueChoice("UniversityType")
                                        , null=True, blank=True)
    UniversityCity = models.ForeignKey("City", verbose_name="شهر محل دانشگاه",
                                       on_delete=models.CASCADE)




class FieldOfStudy(models.Model):
    """رشته های تحصیلی"""
    class Meta:
        verbose_name = "رشته تحصیلی"
        verbose_name_plural = "رشته های تحصیلی"
        ordering = ("Title",)

    Title = models.CharField(max_length=150, verbose_name="رشته")

    def __str__(self):
        return self.Title


class Tendency(models.Model):
    """گرایش های رشته های تحصیلی"""
    class Meta:
        verbose_name = "گرایش تحصیلی"
        verbose_name_plural = "گرایش های تحصیلی"

    Title = models.CharField(max_length=150, verbose_name="گرایش")
    FieldOfStudy = models.ForeignKey("FieldOfStudy", verbose_name="گرایش تحصیلی", on_delete=models.CASCADE)




class EducationHistory(models.Model):
    """سوابق تحصیلی پرسنل"""
    class Meta:
        verbose_name = "سابقه تحصیلی"
        verbose_name_plural = "سوابق تحصیلی"

    Person = models.ForeignKey("Users", verbose_name="پرسنل", on_delete=models.CASCADE,
                               related_name="education_history")

    PrimarySchool = 1
    HighSchool = 2
    Associate = 3
    Bachelor = 4
    Master = 5
    Doctoral = 6
    DegreeChoice = ((PrimarySchool, 'زیر دیپلم'), (HighSchool, 'دیپلم'), (Associate, 'کاردانی'), (Bachelor, 'کارشناسی')
                    , (Master, 'فوق کارشناسی')
                    , (Doctoral, 'دکترا'))
    DegreeType = models.IntegerField(choices=DegreeChoice, null=True, blank=True, verbose_name='مقطع تحصیلی', help_text="دیگر از این فیلد برای نوع مقطع مدرک تحصیلی استفاده نمی کنیم.")
    Degree_Type = models.ForeignKey('ConstValue', on_delete=models.PROTECT,
                                    verbose_name=' مقطع تحصیلی')
    University = models.ForeignKey("University", verbose_name="دانشگاه محل تحصیل",
                                   null=True, blank=True, on_delete=models.SET_NULL)
    StartDate = models.DateField(verbose_name="تاریخ شروع", blank=True, null=True)
    EndDate = models.DateField(verbose_name="تاریخ خاتمه", blank=True, null=True)
    StartYear = models.PositiveSmallIntegerField(verbose_name="سال ورود",
                                                 blank=True, null=True
                                                 , help_text="تاریخ شمسی")
    EndYear = models.PositiveSmallIntegerField(verbose_name="سال فراغت از تحصیل",
                                               blank=True, null=True
                                               , help_text="تاریخ شمسی")
    IsStudent = models.BooleanField(verbose_name="دانشجو است؟", default=False)
    EducationTendency = models.ForeignKey("Tendency", verbose_name="گرایش تحصیلی",
                                          on_delete=models.PROTECT)
    GPA = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="معدل", null=True, blank=True)





#
# class Users(models.Model):
#     class Meta:
#         verbose_name = 'کاربر'
#         verbose_name_plural = 'کاربران'
#         db_table = 'Users'
#
#     UserName = models.CharField(primary_key=True, max_length=100, verbose_name='نام کاربری')
#     FirstName = models.CharField(max_length=200, verbose_name='نام')
#     LastName = models.CharField(max_length=200, verbose_name='نام خانوادگی')
#     BirthDate = models.DateField (null=True,blank=True ,verbose_name='تاریخ تولد')
#     ContractDate = models.DateField (null=True,blank=True, verbose_name='تاریخ استخدام')
#     FieldOfStudy = models.CharField(max_length=300, null=True, blank=True, verbose_name='رشته تحصیلی')
#     PrimarySchool = 1
#     HighSchool = 2
#     Associate = 3
#     Bachelor = 4
#     Master = 5
#     Doctoral = 6
#     DegreeChoice= ((PrimarySchool,'زیر دیپلم'),(HighSchool,'دیپلم'),(Associate,'کاردانی'),(Bachelor,'کارشناسی')
#                    ,(Master,'فوق کارشناسی')
#                    , (Doctoral ,'دکترا'))
#     DegreeType = models.IntegerField(choices=DegreeChoice, null=True, blank=True, verbose_name='مقطع تحصیلی')


class Team(models.Model):
    class Meta:
        db_table = 'Team'
        verbose_name = 'تیم'
        verbose_name_plural = 'تیم ها'

    TeamCode = models.CharField(primary_key=True, max_length=3, verbose_name='کدتیم')
    TeamName = models.CharField(max_length=100, verbose_name='نام تیم')
    ActiveInService = models.BooleanField(null=True,default=True,
                                          verbose_name=' '
                                                                        'کتاب')
    ActiveInEvaluation = models.BooleanField(null=True,default=True, verbose_name='ارزیابی')
    GeneralManager = models.ForeignKey(to='Users', related_name='TeamGeneralManager', on_delete=models.SET_NULL,
                                       null=True, verbose_name='مدیر عمومی',
                                       help_text='مدیر عمومی می تواند، مدیر پروژه یا مدیر اداری، یا  مدیر اداری یا کلا هر مدیری باشد')
    SupportManager = models.ForeignKey(to='Users', related_name='TeamSupportManager', on_delete=models.SET_NULL,
                                       null=True, verbose_name='مدیر پشتیبانی',
                                       help_text='برای تیم های عملیانی مشخص می شود و برای غیر عملیاتی ها نال است')
    TestManager = models.ForeignKey(to='Users', related_name='TeamTestManager', on_delete=models.SET_NULL, null=True,
                                    verbose_name='مدیر تست',
                                    help_text='برای تیم های عملیانی مشخص می شود و برای غیر عملیاتی ها نال است')
    IsActive = models.BooleanField(null=True,default=True, verbose_name='آیا تیم '
                                                                'فعال است؟')



class Role(models.Model):
    class Meta:
        db_table = 'Role'
        verbose_name = 'سمت'
        verbose_name_plural = 'سمت ها'

    RoleId = models.IntegerField(primary_key=True, verbose_name='کد سمت')
    RoleName = models.CharField(max_length=100, verbose_name='نام سمت')
    HasLevel = models.BooleanField(default=False, verbose_name='دارای سطح')
    HasSuperior = models.BooleanField(default=False, verbose_name='ارشد دارد')


class UserTeamRole(models.Model):
    class Meta:
        db_table = 'UserTeamRole'
        verbose_name = 'اطلاعات پرسنل'
        verbose_name_plural = 'اطلاعات همه ی پرسنل'

    UserName = models.ForeignKey("Users", verbose_name='نام کاربری', related_name='UserTeamRoleUserNames',
                                 db_column='UserName', on_delete=models.CASCADE)
    TeamCode = models.ForeignKey("Team", db_column='TeamCode', on_delete=models.CASCADE, verbose_name='کدتیم')
    RoleId = models.ForeignKey("Role", db_column='RoleId', on_delete=models.CASCADE, verbose_name='کد سمت')
    LevelId = models.ForeignKey('RoleLevel', null=True, blank=True, on_delete=models.CASCADE, verbose_name='سطح')
    Superior = models.BooleanField(verbose_name='ارشد', default=False, null=True)
    ManagerUserName = models.ForeignKey("Users", null=True, blank=True, verbose_name='نام مدیر',
                                        related_name='UserTeamRoleManagerUserNames', on_delete=models.CASCADE)
    StartDate = models.CharField(null=True, max_length=10, verbose_name=(
        'تاریخ '
                                                                    'شروع'))
    EndDate = models.CharField(max_length=10, null=True, blank=True, verbose_name='تاریخ پایان')

class RoleLevel(models.Model):
    LevelName = models.CharField(verbose_name='نام سطح', max_length=20)

    class Meta:
        db_table = 'RoleLevel'
        verbose_name = 'سطح'
        verbose_name_plural = 'سطوح'

    def __str__(self):
        return self.LevelName

class ChangeRole(models.Model):
    class Meta:
        verbose_name = 'اطلاعات تغییر سمت'
        verbose_name_plural = 'اطلاعات تغییر سمت ها'

    RoleID = models.ForeignKey('Role', related_name='ChangeRoleRoleIDs', on_delete=models.CASCADE,
                               verbose_name='سمت فعلی')
    LevelId = models.ForeignKey('RoleLevel', related_name='ChangeRoleRoleLevels', null=True, blank=True,
                                on_delete=models.CASCADE, verbose_name='سطح فعلی')
    Superior = models.BooleanField(verbose_name='وضعیت فعلی ارشد', default=False)
    RoleIdTarget = models.ForeignKey('Role', related_name='ChangeRoleRoleIdTargets', on_delete=models.CASCADE,
                                     verbose_name='سمت جدید')
    LevelIdTarget = models.ForeignKey('RoleLevel', related_name='ChangeRoleLevelIdTargets', null=True, blank=True,
                                      on_delete=models.CASCADE, verbose_name='سطح جدید')
    SuperiorTarget = models.BooleanField(verbose_name='وضعیت جدید ارشد', default=False)
    Education = models.BooleanField(default=True, verbose_name='آموزش نیاز دارد؟')
    Educator = models.CharField(max_length=100, null=True, blank=True, verbose_name='آموزش دهنده')
    Evaluation = models.BooleanField(default=True, verbose_name='ارزیابی نیاز دارد؟')
    Assessor = models.CharField(max_length=100, null=True, blank=True, verbose_name='ارزیابی کننده')
    RequestGap = models.IntegerField(null=True, blank=True, verbose_name='مدت زمان')
    Assessor2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='ارزیابی کننده دوم')
    ReEvaluation = models.BooleanField(default=True, verbose_name='ارزیابی  دوم نیاز دارد؟')
    PmChange = models.BooleanField(default=True, verbose_name='تغیرات PM؟')
    ITChange = models.BooleanField(default=True, verbose_name='تغیرات IT؟')




class RoleGroup(models.Model):
    class Meta:
        verbose_name = 'گروه سمت'
        verbose_name_plural = 'گروه های سمت ها'

    RoleID = models.ForeignKey('Role', related_name='RoleGroupRoleIDs', on_delete=models.CASCADE,
                               verbose_name='سمت فعلی')
    RoleGroup = models.CharField(max_length=50, verbose_name='گروه')
    RoleGroupName = models.CharField(max_length=100, null=True, blank=True, verbose_name=' نام گروه')


class RoleGroupTargetException(models.Model):
    class Meta:
        verbose_name = 'گروه سمت'
        verbose_name_plural = 'گروه های سمت ها'

    RoleGroup = models.CharField(max_length=100,
                                 verbose_name='گروه مبدا')
    RoleGroupTarget = models.CharField(max_length=100,
                                       verbose_name='گروه مقصد')



class AccessPersonnel(models.Model):
    class Meta:
        verbose_name = 'دسترسی انتخاب  سمت'
        verbose_name_plural = 'دسترسی های انتخاب همه سمت ها'

    UserName = models.ForeignKey("Users", verbose_name='نام کاربری', related_name='AccessPersonnelUserNames',
                                 on_delete=models.CASCADE)


class OrganizationChartRole(models.Model):
    class Meta:
        verbose_name = 'سمت و سطح'
        verbose_name_plural = 'سمت ها و سطح ها'

    RoleId = models.ForeignKey('Role', related_name='OrganizationChartRoleRoleIDs', on_delete=models.CASCADE,
                               verbose_name='سمت')
    LevelId = models.ForeignKey('RoleLevel', related_name='OrganizationChartRoleRoleLevels', null=True, blank=True,
                                on_delete=models.CASCADE, verbose_name='سطح ')



class OrganizationChartTeamRole(models.Model):
    class Meta:
        verbose_name = 'سمت  تیم'
        verbose_name_plural = 'سمت های تیم های عملیاتی'

    TeamCode = models.ForeignKey('Team', related_name='OrganizationChartTeamRoleTeamCodes', on_delete=models.CASCADE,
                                 verbose_name='نام تیم')
    RoleCount = models.IntegerField(verbose_name='ظرفیت سمت', null=True, blank=True)
    ManagerUserName = models.ForeignKey("Users", null=True, blank=True, verbose_name='نام مدیر',
                                        related_name='OrganizationChartTeamRoleManagerUserNames',
                                        on_delete=models.CASCADE)
    OrganizationChartRole = models.ForeignKey('OrganizationChartRole', on_delete=models.CASCADE,
                                              verbose_name='مدیر تیم و سمت')


class UserHistory(models.Model):
    UserName = models.CharField(max_length=300)
    AppName = models.CharField(max_length=100, default=None, null=True)
    AuthLoginKey = models.CharField(max_length=300, null=True)
    RequestDate = models.DateTimeField(default=None)
    EnterDate = models.DateTimeField(default=None, null=True)
    RequestUrl = models.CharField(max_length=300, null=True)
    EnterUrl = models.CharField(max_length=300, null=True)
    IP = models.GenericIPAddressField(null=True)
    UserAgent = models.CharField(max_length=300, null=True)
    ChangedUserInfo = models.BooleanField(default=None, null=True)



class PreviousUserTeamRole(models.Model):
    class Meta:
        db_table = 'PreviousUserTeamRole'
        verbose_name = 'اطلاعات پرسنل'
        verbose_name_plural = 'اطلاعات همه ی پرسنل'

    UserName = models.ForeignKey("Users", verbose_name='نام کاربری', related_name='UserNames', db_column='UserName',
                                 on_delete=models.CASCADE)
    TeamCode = models.ForeignKey("Team", db_column='TeamCode', on_delete=models.CASCADE, verbose_name='کدتیم')
    RoleId = models.ForeignKey("Role", db_column='RoleId', on_delete=models.CASCADE, verbose_name='کد سمت')
    LevelId = models.ForeignKey('RoleLevel', null=True, blank=True, on_delete=models.CASCADE, verbose_name='سطح')
    Superior = models.BooleanField(verbose_name='ارشد', default=False)
    ManagerUserName = models.ForeignKey("Users", null=True, blank=True, verbose_name='نام مدیر',
                                        related_name='ManagerUserNames', on_delete=models.CASCADE)
    StartDate = models.CharField(max_length=10, verbose_name='تاریخ شروع')
    EndDate = models.CharField(max_length=10, null=True, blank=True, verbose_name='تاریخ پایان')


class SlipField(models.Model):
    class Meta:
        abstract = True
    YearNumber = models.IntegerField(verbose_name='سال')
    MonthNumber = models.IntegerField(verbose_name='ماه')
    ItemValue = models.BigIntegerField(verbose_name='مقدار مربوطه')
    Code = models.CharField(max_length=200, verbose_name="کد مورد مربوطه")





class PaymentField(models.Model):
    class Meta:
        abstract = True
    YearNumber = models.IntegerField(verbose_name='سال')
    Payment = models.BigIntegerField(null=True, blank=True, verbose_name='خالص دریافتی',
                                     help_text='این مبلغ خالص دریافتی کاربر است'
                                   )
    TotalPayment = models.BigIntegerField(null=True, blank=True, verbose_name='حقوق ناخالص',
                                          help_text='کل پرداختی ها شامل حقوق پایه، اضافه کار، پاداش و ...')
    OtherPayment = models.BigIntegerField(null=True, blank=True, verbose_name='سایر هزینه های کارفرما',
                                          help_text="مثلا سوبسید ناهار تایم یا بیمه تکمیلی"
                                                    " که شرکت برای این فرد پرداخت می کند")
    PaymentCost = models.BigIntegerField(null=True, blank=True, verbose_name='بهای تمام شده این فرد',
                                         help_text='بهای تمام شده فرد شامل کل حقوق دریافتی'
                                                   ' + بیمه کارفرما + سایر هزینه های پرداختی کارفرما است')
    BasePayment = models.BigIntegerField(null=True, blank=True, verbose_name='پایه حقوق',
                                         help_text='حقوق پایه یعنی مبلغ ناخالص قرارداد فرد')
    OverTimePayment = models.BigIntegerField(null=True, blank=True, verbose_name='هزینه اضافه کاری',
                                             help_text='مبلغی که فرد بابت اضافه کار در ماه دریافت کرده است')
    OverTime = models.IntegerField(null=True, blank=True, verbose_name='ساعت اضافه کاری',
                                   help_text='میزان اضافه کاری فرد بر حسب دقیقه')
    Reward = models.BigIntegerField(null=True, blank=True, verbose_name='مبلغ پاداش ماهانه',
                                    help_text='مبلغی که فرد به عنوان پاداش در آن ماه دریافت کرده است')





class PageInformation(models.Model):
    class Meta:
        verbose_name = "اطلاعات صفحه"
        verbose_name_plural = "اطلاعات صفحات"

    PageName = models.CharField(max_length=30, verbose_name='نام صفحه')
    EnglishName = models.CharField(max_length=30, verbose_name='نام لاتین صفحه', )
    ColorSet = models.CharField(max_length=30, verbose_name='رنگ آیکون صفحه', )
    IconName = models.CharField(max_length=30, verbose_name='آیکون صفحه', )
    ShowDetail = models.BooleanField(default=False, verbose_name="جزییات نمایش داده شود؟")
    OrderNumber = models.PositiveSmallIntegerField(default=10, verbose_name='ترتیب نمایش')



class PagePermission(models.Model):
    class Meta:
        verbose_name = "دسترسی صفحه"
        verbose_name_plural = "دسترسی های صفحات"

    Page = models.ForeignKey(verbose_name="نام صفحه", on_delete=models.CASCADE, to="PageInformation", null=True)
    GroupId = models.PositiveIntegerField(verbose_name='شناسه گروه')
    Editable = models.BooleanField(default=False, verbose_name='قابل ویرایش')
