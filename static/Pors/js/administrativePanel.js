const URL_PREFIX = "/PersonnelService/Pors/"
const STATIC_PREFIX = "/static/Pors/"

function addPrefixTo(str) {
    return URL_PREFIX+str
}

function addStaticFilePrefixTo(str) {
    return STATIC_PREFIX+str
}



const WEEK_DAYS = {
    1: "شنبه",
    2: "یک‌شنبه",
    3: "دو‌شنبه",
    4: "سه‌شنبه",
    5: "چهارشنبه",
    6: "پنج‌شنبه",
    7: "جمعه",
}
const YEAR_MONTHS = {
    1: "فروردین",
    2: "اردیبهشت",
    3: "خرداد",
    4: "تیر",
    5: "مرداد",
    6: "شهریور",
    7: "مهر",
    8: "آبان",
    9: "آذر",
    10: "دی",
    11: "بهمن",
    12: "اسفند",
}

const DEFAULTITEMIMAGE = addStaticFilePrefixTo("images/placeholder.png")


const DISMISSDURATIONS = {
    "DISPLAY_TIME_SHORT": 2000,
    "DISPLAY_TIME_TEN": 10000,
    "DISPLAY_TIME_LONG": 200000,
    "DISPLAY_TIME_PARAMENT": 999999
}

const DISMISSLEVELS = {
    "SUCCESS": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "INFO": "blue",
    "ANNOUNCEMENT": "purple"
}

let isSystemOpen = false
// منظور از currentDate در واقع currentDate قابل سفارش است
let currentDate = {
    year: undefined,
    month: undefined,
    day: undefined
}
let selectedDate = undefined
let personnelFullName = undefined
let personnelProfileImg = undefined
let firstDayOfWeek = undefined
let lastDayOfMonth = undefined
let holidays = undefined
let daysWithMenu = undefined
let orderedDays = undefined
let selectedItems = undefined
let availableItems = undefined
let allItems = undefined



const REPORTS = [
    {
        "id":1,
        "title": "گزارش سفارش های امروز",
        "fileNameFunction":dailyOrdersReportFileName,
        "api": addPrefixTo("administrative/reports/daily-orders/"),
        "data": dailyOrdersReportRequestBody
    },
    {
        "id":2,
        "title": "گزارش مالی این ماه",
        "fileNameFunction":monthlyFinancialReportFileName,
        "api": addPrefixTo("administrative/reports/monthly-financial/"),
        "data": monthlyFinancialReportRequestBody,
    }
]


function insertCommas(str) {
  let result = '';

  for (let i = str.length - 1; i >= 0; i--) {
    result = str[i] + result;
    if ((str.length - i) % 3 === 0 && i !== 0) {
      result = ',' + result;
    }
  }
  return result
}

function convertToPersianNumber(englishNumber) {
    const persianNumbers = {
        '0': '۰',
        '1': '۱',
        '2': '۲',
        '3': '۳',
        '4': '۴',
        '5': '۵',
        '6': '۶',
        '7': '۷',
        '8': '۸',
        '9': '۹'
    };

    const englishNumberArray = englishNumber.toString().split('');

    const persianNumberArray = englishNumberArray.map(digit => {
        return persianNumbers[digit] || digit;
    });

    return persianNumberArray.join('');
}


function getOrdersNumberForDay(day, ordersList) {
    let order = ordersList.find(order => order.day === day);
    return order ? order.ordersNumber : undefined;
}

function toShamsiFormat(dateobj) {
    // 1402/08/09
    if (dateobj===undefined) return undefined
    return `${dateobj.year}/${zfill(dateobj.month, 2)}/${zfill(dateobj.day, 2)}`
}

function extractIds(items) {
    return items.map(function (item) {
        return item.id;
    });
}

function filterObjectsById(inputArray, idList) {
    return inputArray.filter(function (object) {
        return idList.includes(object.id);
    });
}

function filterObjectsByAttrValue(inputArray, fieldName, value) {
    return inputArray.filter(obj => obj[fieldName] === value);
}

function toObjectFormat(shamsiDate) {
    let dateParts = shamsiDate.split('/');

    let year = parseInt(dateParts[0], 10);
    let month = parseInt(dateParts[1], 10);
    let day = parseInt(dateParts[2], 10);


    return {
        year: year,
        month: month,
        day: day
    };
}

function changeVisibilityAddMenuItemDropDown(hidden) {
    let addItemContainer = $("#dropdown-menu-container")
    if (hidden){
        addItemContainer.addClass("hidden")
    } else {
        addItemContainer.removeClass("hidden")
    }
}

function zfill(number, width) {
    let numberString = number.toString();
    while (numberString.length < width) {
        numberString = '0' + numberString;
    }
    return numberString;
}

function catchResponseMessagesToDisplay(messages) {
    if (messages===undefined) return
    messages.forEach(function (msg){
        displayDismiss(DISMISSLEVELS[msg.level], msg.message, DISMISSDURATIONS[msg.displayDuration])
    })
}
function displayDismiss(color, content, duration) {

    let HTML = `
        <div class="dismiss flex items-center p-4 mb-4 text-${color}-800 border-t-4 border-${color}-300 bg-${color}-50 " role="alert">
    <svg class="flex-shrink-0 w-4 h-4" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
      <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z"/>
    </svg>
    <div class="ms-3 text-xs font-medium">
        ${content}
    </div>
</div>
`
        $("#dismiss").append(HTML)

    let fadingElement = $(".dismiss")
    setTimeout(function() {
                fadingElement.fadeOut(500, function() {
                    fadingElement.remove();
                });
            }, duration);

}

function canAdminChangeMenu() {
    // این تابع کاری به این نداره که ایتمی که ملت سفارش دادن حذف بشه یا
    // نشه؟‌اون در جای دیگری چک میشه
    let can = true
    let currentDateMomentObj = moment(toShamsiFormat(currentDate),'YYYY-MM-DD')
    let selectedDateMomentObj = moment(toShamsiFormat(selectedDate),'YYYY-MM-DD')

    // با تفریق این دو از هم یک عدد بهمون میده اگه که عدد منفی بود یعنی
    // اولی از دومی کوچک تره و برعکس
    if (currentDateMomentObj-selectedDateMomentObj > 0){
            can = false
        }
    return can

}

function calendarDayBlock(dayNumberStyle, dayNumber, dayOfWeek, monthNumber, yearNumber, hasMenu, orderedByCounter) {
    let opacity = ""
    let orderedBy = ""
    let MenuIcon = addStaticFilePrefixTo("images/food-dish.svg")
    let menuIconHTML = `<img class="w-6 h-6 hidden" src="${MenuIcon}" alt="">`
    if (hasMenu === true) {
        menuIconHTML = `<img class="w-6 h-6" src="${MenuIcon}" alt="">`
    }
    let date = toShamsiFormat({
        year: yearNumber,
        month: monthNumber,
        day: dayNumber
    })

    if (date < toShamsiFormat(currentDate)) {
        opacity = "opacity-50"
    }

    if (orderedByCounter > 0 && hasMenu){
        orderedBy = `<span class="text-xs text-slate-500 self-center">${convertToPersianNumber(orderedByCounter)}</span>`
    }


    let dayTitle = `${WEEK_DAYS[dayOfWeek]} ${convertToPersianNumber(dayNumber)} ${YEAR_MONTHS[monthNumber]}`

    return `<div data-date="${date}" data-day-title="${dayTitle}" data-day-number="${dayNumber}" class="cd- ${opacity} cursor-pointer flex flex-col items-center justify-around border border-gray-100 p-4 grow hover:bg-gray-200 hover:border-gray-300">
                                <div> 
                                    <span class="text-2xl ${dayNumberStyle}">${convertToPersianNumber(dayNumber)}</span>
                                </div>
                                <div class="w-6 h-6 flex flex-col">
                                    ${menuIconHTML}
                                    ${orderedBy}
                                </div>
                            </div>`
}

function menuItemBlock(id, itemName, pic, orderedByCount) {
    // چون موقع اضافه کردن یک ایتم به منو هم داریم از این تابع استفاده می
    // کنیم و هنگام اضافه کردن تعداد سفارش داده شده ها اضلا مطرح نیست پس
    // باید undefined  رو مدیریت کنیم
    if (orderedByCount ===undefined) orderedByCount = 0
    let trashcanIcon = `
    <div class="ml-2">
                <img class="w-6 h-6"
                     src="${addStaticFilePrefixTo('images/trash.svg')}" alt="">
            </div>`

    let userIcon = `
    <div class="ml-2">
                <img class="w-6 h-6"
                     src="${addStaticFilePrefixTo('images/users.svg')}" alt="">
            </div>
    `
    return `<li data-item-id="${id}" data-ordered-by="${orderedByCount}" class="flex flex-col cursor-pointer bg-white rounded p-4 shadow-md hover:bg-gray-300 ">
    <div class="flex items-center gap-4">
        <img
                src="${pic}"
                alt=""
                class="h-16 w-16 rounded object-cover self-start"
        />
        <div class="w-8/12">
            <div><h3 class="text-xs text-gray-900">${itemName}</h3>
            </div>
        </div>
        <div class="flex justify-end w-3/12 gap-2">
        <span>${orderedByCount !==0 ? convertToPersianNumber(orderedByCount) : ''}</span>         
        ${orderedByCount !==0 ? userIcon : ''}
        ${canAdminChangeMenu() && orderedByCount ===0 ? trashcanIcon : ''}
         
        </div>
    </div>
</li>`
}

function dropDownItemBlock(id, title, category,mealType) {
    return `<a data-item-id="${id}" class="flex flex-row justify-between text-xs px-4 py-2 text-gray-700 hover:bg-gray-100 active:bg-blue-100 cursor-pointer rounded-md">
    <span>${title}</span>

<span class="float-left">
<span class="italic text-gray-500 text-xs">${category}</span>
<span class="italic text-gray-500 text-xs">${mealType}</span>
</span>
</a>`
}

function makeDropDownChoices(items) {
    let HTML = ""
    items.forEach(function (item) {
        HTML += dropDownItemBlock(
            item.id,
            item.itemName,
            item.category,
            item.mealType
        )
    })
    return HTML
}

function makeSelectedMenu(items) {
    let HTML = ""
    items.forEach(function (itemObj) {
        let selectedMenuItem = allItems.find(item => item.id === itemObj.id);
        HTML += menuItemBlock(selectedMenuItem.id, selectedMenuItem.itemName, selectedMenuItem.image, itemObj.orderedBy)
    })
    return HTML
}

function loadMenu(day, month, year) {

    // allMenus در واقع همون selectedItems هست


    // منوی قبلی را پاک می کنیم
    $("#menu-items-container li").remove()

    if (selectedItems === undefined) return

    let requestedDate = toShamsiFormat({year: year, month: month, day: day})
    let selectedMenu = selectedItems.find(function (entry) {
        return entry.date === requestedDate;
    });

    // حالا باید آیتم هارو بگیریم
    if (selectedMenu !== undefined) {

        // تعداد سفارش ها به ازای هر آیتم در آیتم های selectedMenu هم
        // فرستاده می شود که به صورت زیر است
        // {
        //  1: 12,
        //  5 :26
        // }
        let menuHTML = makeSelectedMenu(selectedMenu.items)
        $("#menu-items-container").append(menuHTML)
    }


}

function makeReportSectionMenu() {
    REPORTS.forEach(function (obj) {
        $("#report-wrapper").append(
            `
             <li>
                    <a href="#" class="block px-4 py-2 hover:bg-gray-100 system-report" data-report-id="${obj.id}">${obj.title}</a>
             </li>
            `
        )
    })
}

function makeCalendar(startDayOfWeek, endDayOfMonth, holidays, daysWithMenu, monthNumber, yearNumber) {

// ابتدا باید تقویم قبلی را پاگ کنیم
    $('#dayBlocksWrapper [class^="cd-"]').remove()

    let newCalendarHTML = ""
//     حال باید با توجه به روز این روز اول ماه چند شنبه است بلاک های روز
//     های ما قبل آن خاکستری کنیم
    for (let i = 1; i < startDayOfWeek; i++) {
        newCalendarHTML += '<div class="cd- flex flex-col items-center' +
            ' bg-gray-50 border border-gray-100 p-4 grow"></div>'
    }


//     سپس به سراغ ساخت بلاک روز های دیگر می کنیم. در صورتی روز مورد نظر
//     تعطیل بود باید شماره روز را رنگی کنیم و در همچنین وضعیت ثبت منو توسط
//     اداری را در آن روز به نمایش بگذاریم
    for (let dayNumber = 1; dayNumber <= endDayOfMonth; dayNumber++) {

        let orderedBy = 0
        let dayNumberStyle = ""
        let dayMenuIcon = false

        // در صورتی که روز تعطیل بود اون رو قرمز می کنیم
        if (holidays.includes(dayNumber)) {
            dayNumberStyle = "text-red-500"
        }

        // در صورتی که توسط اداری برای اون روز منو تعیین شده بود آن ایکن را
        // تغییر می دهیم


        let daysWithMenuDaysNumber = daysWithMenu.map(function (item) {
        return item.day;
    });



        if (daysWithMenuDaysNumber.includes(dayNumber)) {
            dayMenuIcon = true
            orderedBy = getOrdersNumberForDay(dayNumber, daysWithMenu)
        }


        newCalendarHTML += calendarDayBlock(dayNumberStyle, dayNumber, startDayOfWeek % 8, monthNumber, yearNumber, dayMenuIcon,orderedBy)


        startDayOfWeek++
        if (startDayOfWeek % 8 === 0) {
            startDayOfWeek++
        }
    }
    $("#dayBlocksWrapper").append(newCalendarHTML)
    $("#dayBlocksWrapper").attr("data-month", monthNumber)
    $("#dayBlocksWrapper").attr("data-year", yearNumber)


}


function addNewItemToMenu(id) {
    let selectedItem = availableItems.find(item => item.id === id);
    $("#menu-items-container").append(
        menuItemBlock(selectedItem.id, selectedItem.itemName, selectedItem.image)
    )
    updateAvailableItemForThisDay()
}

function finishLoadingDisplay() {
    $("#loading").addClass("hidden")
    $("#main-panel-wrapper").removeClass("hidden")

}
function removeItemFromMenu(id) {
    $(`#menu-items-container li[data-item-id='${id}']`).remove();

    updateAvailableItemForThisDay()
}

function loadAvailableItem() {
    // آیتم های قبل را پاک می کنیم
    $("#dropdown-menu a").remove();

    // ایتم های قابل انتخاب جدید رو دریافت می کند
    $.ajax({
        url: addPrefixTo(`all-items/`),
        method: 'GET',
        dataType: 'json',
        async: false,
        success: function (data) {
            $("#dropdown-menu").append(makeDropDownChoices(data))
            allItems = data
             // همین جا بررسی می کنیم اگه که ایتم عکس نداشت عکس پیشفرض رو
            // قرار می دهیم
            allItems.forEach(function (item) {
                if (item.image==="") item.image = DEFAULTITEMIMAGE
            })
            availableItems = filterObjectsByAttrValue(allItems, "isActive", true)
            catchResponseMessagesToDisplay(data.messages)

        },
        error: function (xhr, status, error) {
            console.error('Available Items cannot be loaded', status, 'and' +
                ' error:', error, 'detail:', xhr.responseJSON);
            catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
        }
    });
}

function updateSelectedDate(shamsiDate) {
    selectedDate = toObjectFormat(shamsiDate)
}

function updateSelectedItems(month, year) {
    $.ajax({
        url: addPrefixTo(`administrative/calendar/?year=${year}&month=${month}`),
        method: 'GET',
        dataType: 'json',
        success: function (data) {
            selectedItems = data["menuItems"]
            daysWithMenu = data["daysWithMenu"]
            catchResponseMessagesToDisplay(data.messages)

        },
        error: function (xhr, status, error) {
            console.error('Selected Items cannot be updated!', status, 'and error:', error, 'detail:', xhr.responseJSON);
            catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
        }
    });
}

function changeMenuDate(dateTitle) {
    $("#menu-date-wrapper").text(dateTitle)
}

function updateItemsCounter() {
    let len = $("#menu-items-container li").length
    $("#menu-items-counter").text(convertToPersianNumber(len))
}

function updateHasMenuCalendarDayBlock() {
    let currentShamsi = toShamsiFormat(selectedDate)
    let len = $("#menu-items-container li").length
    let dishLogo = $(`.cd-[data-date="${currentShamsi}"] img`)
    if (parseInt(len) === 0) {
        dishLogo.addClass("hidden")
        return
    }
    dishLogo.removeClass("hidden")

}

function updateSelectedDayOnCalendar(shamsiFormatDate) {
    let selectedBG = "bg-sky-100"
    let selectedHover = "hover:bg-gray-200"

    //     ابتدا روز انتخاب شده قبلی رو استایلش رو تغییر می دهیم
    let preSelected = $(`#dayBlocksWrapper div[data-date].${selectedBG}`)
    preSelected.removeClass(`${selectedBG}`)
    preSelected.addClass(`${selectedHover}`)

    let currentSelectedDayBlock = $(`#dayBlocksWrapper div[data-date="${shamsiFormatDate}"]`)
    currentSelectedDayBlock.removeClass(`${selectedHover}`)
    currentSelectedDayBlock.addClass(`${selectedBG}`)

}

function updateAvailableItemForThisDay() {
    // اول قبلی ها رو پاک می کنیم
    $("#dropdown-menu a").remove();

    //     ابتدا می بینیم که چه چیز هایی در منوی روز انتخاب شده وجود دارد
    let thisDaySelectedItemIds = []
    $("#menu-items-container li").each(function (index, element) {
        thisDaySelectedItemIds.push(parseInt($(this).attr("data-item-id")))
    })

//     خب حالا هر چیزی که انتخاب نشده باشه رو قابل انتخاب می گذاریم
    let allAvailableItemsIds = extractIds(availableItems)
    let remainingItemsIds = allAvailableItemsIds.filter(function (element) {
        return !thisDaySelectedItemIds.includes(element);
    });

    let data = filterObjectsById(availableItems, remainingItemsIds)
    $("#dropdown-menu").append(makeDropDownChoices(data))

}

function getFirstDayOfCalendar() {
    return $(`#dayBlocksWrapper div[data-date]`).filter(":first")
}

function selectDayOnCalendar(e) {
    let selectedShamsiDate = e.attr("data-date")
    let selectedShamsiDateTitle = e.attr("data-day-title")
    updateSelectedDate(selectedShamsiDate)
    updateSelectedDayOnCalendar(selectedShamsiDate)
    changeMenuDate(selectedShamsiDateTitle)
    loadMenu(selectedDate.day, selectedDate.month, selectedDate.year)
    updateItemsCounter()
    updateHasMenuCalendarDayBlock()

    if (canAdminChangeMenu()){
        changeVisibilityAddMenuItemDropDown(false)
        updateAvailableItemForThisDay()
    } else {
        changeVisibilityAddMenuItemDropDown(true)

    }

}

function preItemsImageLoader() {
    let imageLinks = availableItems.map(function (item) {
        return item.image;
    });

    $.each(imageLinks, function (index, link) {
        // Create an <img> element for each image link
        let imgElement = $('<img>').attr('src', link);

        // Append the <img> element to the container
        $('#dump-image-container').append(imgElement);
    });
}

function updateDropdownCalendarMonth() {
    // این تابع بعد از makeCalendar کال شه چرا که با کال شدن تابع مذکور
    // dayBlocksWrapper دارای دیتای ماه میشه


    //  نمایش ماه قبلی رو متوقف می کنیم
    $("#calSelectedMonth option:selected").removeAttr("selected")

    let currentMonth = $("#dayBlocksWrapper").attr("data-month")

    $(`#calSelectedMonth option[value="${currentMonth}"]`).prop("selected",true)


}
function oneItemOrderedByPersonnelReportFileName(dataNeededForFileName) {
        // گزارش موردی غذا ها به صورت روزانه
        let cd = toShamsiFormat(selectedDate)
        let item = allItems.find(function (obj) {
            return obj.id===dataNeededForFileName.item
        })
        let farsiPrefix = "لیست سفارش دهنده های ایتم"
        return `${farsiPrefix}-${cd}-${item.itemName}.csv`;
}

function dailyOrdersReportFileName(dataNeededForFileName) {
    return `گزارش سفارش های امروز ${toShamsiFormat(selectedDate)}`
}

function dailyOrdersReportRequestBody() {
    return {
        "date" : toShamsiFormat(selectedDate)
    }
}

function monthlyFinancialReportFileName(dataNeededForFileName) {
        return `گزارش مالی ماه ${selectedDate.month} از سال ${selectedDate.year}`
}

function monthlyFinancialReportRequestBody() {
        return {
            "year": selectedDate.year,
            "month": selectedDate.month
        }
}

function startDownloadReport(fileName, csvData) {
    // Create a Blob object from the CSV data
        let blob = new Blob([csvData], {type: 'text/csv;charset=utf-8;'});

        // Create a temporary link element
        let link = document.createElement('a');

        // Set the link's href to a data URL representing the Blob
        link.href = window.URL.createObjectURL(blob);

        // Set the link's download attribute to specify the filename
        link.download = fileName;


        // Append the link to the document
        document.body.appendChild(link);

        // Programmatically click the link to trigger the download
        link.click();

        // Remove the link from the document
        document.body.removeChild(link);

        let dm = `دانلود ${link.download} شروع شد `
        displayDismiss(DISMISSLEVELS.INFO,dm,DISMISSDURATIONS.DISPLAY_TIME_TEN)
}

function getCurrentCalendarMonth() {
    return $("#dayBlocksWrapper").attr("data-month")
}

function getSelectedCalendarMonthDropdown() {
    return $("#calSelectedMonth option:selected").attr("value")
}


function redirectToGateway(){
    window.location.replace(addPrefixTo("auth-gateway/"))
}

function checkErrorRelatedToAuth(errorCode) {
    if (errorCode === 403) redirectToGateway()
}

function imgError(image) {
    image.onerror = "";
    image.src = DEFAULTITEMIMAGE;
    return true;
}

$(document).ready(function () {


    /* وقتی که صفحه به صورت کامل لود شد کار های زیر را به ترتیب انجام می دهیم
    */


    $.ajax({
        url: addPrefixTo(`panel/`),
        method: 'GET',
        dataType: 'json',
        async: false,
        success: function (data) {

            isSystemOpen = data["isOpenForAdmins"]
            currentDate.day = data["firstOrderableDate"]["day"]
            currentDate.month = data["firstOrderableDate"]["month"]
            currentDate.year = data["firstOrderableDate"]["year"]

            selectedDate = currentDate

            // در صورتی که سیستم قابل استفاده نبود و می خواست از دسترس
            // خارج شه
            if (isSystemOpen === false) {
                displayDismiss(
                    DISMISSLEVELS.INFO,
                    "در حال حاضر سیستم در دسترس نمی باشد",
                    DISMISSDURATIONS.DISPLAY_TIME_LONG
                )
                catchResponseMessagesToDisplay(data.messages)
                return
            }

            $.ajax({
                url: addPrefixTo(`administrative/calendar/?year=${currentDate.year}&month=${currentDate.month}`),
                method: 'GET',
                dataType: 'json',
                success: function (data) {

                    firstDayOfWeek = data["firstDayOfWeek"]
                    lastDayOfMonth = data["lastDayOfMonth"]
                    holidays = data["holidays"]
                    daysWithMenu = data["daysWithMenu"]
                    selectedItems = data["menuItems"]

                    let requestedYear = data["year"]
                    let requestedMonth = data["month"]

                    loadAvailableItem()
                    preItemsImageLoader()

                    // تقویم این ماه به صورت پیشفرض لود می شود
                    makeCalendar(
                        parseInt(firstDayOfWeek),
                        parseInt(lastDayOfMonth),
                        holidays,
                        daysWithMenu,
                        parseInt(requestedMonth),
                        parseInt(requestedYear)
                    )
                    updateDropdownCalendarMonth()
                    updateSelectedDayOnCalendar(toShamsiFormat(selectedDate))
                    // انتخاب کردن روز فعلی به عنوان پیشفرض
                    let sd = $(`#dayBlocksWrapper div[data-date="${toShamsiFormat(selectedDate)}"]`)
                    selectDayOnCalendar(sd)


                    // منوی غذا امروز نیز نمایش داده میشود
                    loadMenu(
                        currentDate.day,
                        currentDate.month,
                        currentDate.year
                    )
                    makeReportSectionMenu()
                    finishLoadingDisplay()
                    catchResponseMessagesToDisplay(data.messages)


                },
                error: function (xhr, status, error) {
                    let em = "EXECUTION ERROR: Default calendar load failed!"
                    displayDismiss(DISMISSLEVELS.ERROR, em,DISMISSDURATIONS.DISPLAY_TIME_LONG)
                    catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                }
            });
            catchResponseMessagesToDisplay(data.messages)


        },
        error: function (xhr, status, error) {
            let em = "EXECUTION ERROR: Administrative is Unreachable"
            displayDismiss(DISMISSLEVELS.ERROR, em,DISMISSDURATIONS.DISPLAY_TIME_LONG)
            catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
        }
    });
    if (isSystemOpen === false) return

    $(document).on('click', '#dropdown-menu a', function () {
        // اضافه کردن یک غذا از منوی دراپ دان به منوی روز انتخاب شده


        let id = parseInt($(this).attr("data-item-id"))
        $.ajax({
            url: addPrefixTo(`administrative/add-item-to-menu/`),
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(
                {
                    "item": id,
                    "date": toShamsiFormat(selectedDate)
                }
            ),
            statusCode:{
                200: function (data) {
                    addNewItemToMenu(id)
                    updateSelectedItems(selectedDate.month, selectedDate.year)
                    updateItemsCounter()
                    updateHasMenuCalendarDayBlock()
                    catchResponseMessagesToDisplay(data.messages)
                }
            },
            error: function (xhr, status, error) {
                console.error('Item not added!', status, 'and error:', error, 'detail:', xhr.responseJSON);
                checkErrorRelatedToAuth(xhr.status)
                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
            }
        });

    });

    $(document).on('click', '#menu-items-container li', function () {


        // علاوه بر اون باید بررسی کنیم که آیا غذایی که داره حدف میشه کسی
        // سفارشش رو داده یا نه؟‌درصورتی که سفارش داشته باشه اجازه حذف ندارد
        // برای همین با کلیک روی ایتم می تونه لیست افرادی که این ایتم رو
        // سفارش دادند به صورت قایل csv دریافت کنه
        let orderedBy = parseInt($(this).attr("data-ordered-by"))
        let id = parseInt($(this).attr("data-item-id"))
        if (orderedBy!==0) {
        //     دانلود فایل افراد سفارش دهنده

            $.ajax({
            url: addPrefixTo(`administrative/reports/specific-item/`),
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(
                {
                    "item": id,
                    "date": toShamsiFormat(selectedDate)
                }
            ),
            statusCode:{
                200: function (data) {
                    startDownloadReport(
                    oneItemOrderedByPersonnelReportFileName(
                        {
                            "item": id,
                            "date": toShamsiFormat(selectedDate)
                        }
                    ),data
                )
                }
            },
            error: function (xhr, status, error) {
                console.error('the report didnt downloaded', status, 'and' +
                    ' error:', error, 'detail:', xhr.responseJSON );
                checkErrorRelatedToAuth(xhr.status)
                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
            }
        });
            return
        }


        // قبل از حذف کردن غذا از منو باید بررسی کنیم که ایا ادمین می تونه
        // اصلا دست بزنه به منو ؟ در صورتی که از تاریخ مجاز گذشته باشیم
        // ادمین اجازه دستکاری منو رو نخواهد داشت
        if (!canAdminChangeMenu()) return

        // حذف کردن یک غذا از منوی روز انتخاب شده


        $.ajax({
            url: addPrefixTo(`administrative/remove-item-from-menu/`),
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(
                {
                    "item": id,
                    "date": toShamsiFormat(selectedDate)
                }
            ),
            statusCode:{
                200: function (data) {
                    removeItemFromMenu(id)
                    updateSelectedItems(selectedDate.month, selectedDate.year)
                    updateItemsCounter()
                    updateHasMenuCalendarDayBlock()
                    catchResponseMessagesToDisplay(data.messages)
                }
            },
            error: function (xhr, status, error) {
                console.error('Item not removed!', status, 'and error:', error, 'detail:', xhr.responseJSON );
                checkErrorRelatedToAuth(xhr.status)
                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
            }
        });

    });


    $(document).on('click', '.system-report', function () {
        let report = REPORTS.find(obj => obj.id === parseInt($(this).attr("data-report-id")))
        let fileNameGen = report.fileNameFunction

        $.ajax({
        url: report.api,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(report.data()),
        statusCode: {
            200: function (data) {
                startDownloadReport(
                    fileNameGen(
                        {
                            "date": toShamsiFormat(selectedDate)
                        }
                    ), data
                )
            }
        },
        error: function (xhr, status, error) {
            console.error('the report didnt downloaded', status, 'and' +
                ' error:', error, 'detail:', xhr.responseJSON );
            checkErrorRelatedToAuth(xhr.status)
            catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
        }
    });
    });



    $(document).on('click', '#dayBlocksWrapper div[data-date]', function () {
        selectDayOnCalendar($(this))
    })

    $(document).on('click', '#system-today', function () {

        let currentCalendarMonthNumber = parseInt(getCurrentCalendarMonth())

        if (currentDate.month !== currentCalendarMonthNumber) {
            $.ajax({
                url: addPrefixTo(`administrative/calendar/?year=${currentDate.year}&month=${currentDate.month}`),
                method: 'GET',
                dataType: 'json',

                success: function (data) {
                    firstDayOfWeek = data["firstDayOfWeek"]
                    lastDayOfMonth = data["lastDayOfMonth"]
                    holidays = data["holidays"]
                    daysWithMenu = data["daysWithMenu"]
                    selectedItems = data["menuItems"]
                    makeCalendar(
                        parseInt(firstDayOfWeek),
                        parseInt(lastDayOfMonth),
                        holidays,
                        daysWithMenu,
                        currentDate.month,
                        currentDate.year
                    )
                    updateDropdownCalendarMonth()
                    // بعد از اینکه تغییر تقویم صورت میگیرد باید بلاک روز
                    // فعلی گرفته شود
                    let systemToday = $(`#dayBlocksWrapper div[data-date="${toShamsiFormat(currentDate)}"]`)
                    selectDayOnCalendar(systemToday)
                    updateSelectedDayOnCalendar(toShamsiFormat(selectedDate))
                    catchResponseMessagesToDisplay(data.messages)

                },
                error: function (xhr, status, error) {
                    console.error('Item not removed!', status, 'and error:', error, 'detail:', xhr.responseJSON);
                    catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                }
            });
        } else {
            // بعد از اینکه تغییر تقویم صورت میگیرد باید بلاک روز
            // فعلی گرفته شود
            let systemToday = $(`#dayBlocksWrapper div[data-date="${toShamsiFormat(currentDate)}"]`)
            selectDayOnCalendar(systemToday)
            updateSelectedDayOnCalendar(toShamsiFormat(selectedDate))


        }


    })

    $(document).on('change', '#calSelectedMonth', function () {
        // تغییر دادن ماه تقویم
        let monthNumber = getSelectedCalendarMonthDropdown()
        $.ajax({
            url: addPrefixTo(`administrative/calendar/?year=${currentDate.year}&month=${monthNumber}`),
            method: 'GET',
            dataType: 'json',

            success: function (data) {
                firstDayOfWeek = data["firstDayOfWeek"]
                lastDayOfMonth = data["lastDayOfMonth"]
                holidays = data["holidays"]
                daysWithMenu = data["daysWithMenu"]
                selectedItems = data["menuItems"]
                makeCalendar(
                    parseInt(firstDayOfWeek),
                    parseInt(lastDayOfMonth),
                    holidays,
                    daysWithMenu,
                    monthNumber,
                    currentDate.year
                )
                selectDayOnCalendar(getFirstDayOfCalendar())
                updateSelectedDayOnCalendar(toShamsiFormat(selectedDate))
                catchResponseMessagesToDisplay(data.messages)
            },
            error: function (xhr, status, error) {
                console.error('Item not removed!', status, 'and error:', error, 'detail:', xhr.responseJSON);
                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
            }
        });
    })


});

