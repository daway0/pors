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
let userFullName = undefined
let userProfileImg = undefined
let firstDayOfWeek = undefined
let lastDayOfMonth = undefined
let holidays = undefined
let daysWithMenu = undefined
let orderedDays = undefined
let selectedItems = undefined
let availableItems = undefined
let allItems = undefined
let godModeEntryReason = undefined
let godModeEntryReasonComment = undefined
let godModUsername = undefined
let deadlines = undefined




const REPORTS = [
    {
        "id":1,
        "title": "سفارش های روز جاری",
        "fileNameFunction":dailyOrdersReportFileName,
        "api": addPrefixTo("administrative/reports/daily-orders/"),
        "data": dailyOrdersReportRequestBody
    },
    {
        "id":2,
        "title": "سفارش های ماه جاری",
        "fileNameFunction":monthlyOrdersReportFileName,
        "api": addPrefixTo("administrative/reports/monthly-orders/"),
        "data": monthlyOrdersReportRequestBody,
    },
    {
        "id":3,
        "title": "سفارش های امروز به صورت تجمیعی",
        "fileNameFunction":dailyFoodProviderOrderingFileName,
        "api": addPrefixTo("administrative/reports/daily-foodprovider-ordering/"),
        "data": dailyFoodProviderOrderingRequestBody
    },
    
    // {
    //     "id":3,
    //     "title": "گزارش مالی این ماه",
    //     "fileNameFunction":monthlyFinancialReportFileName,
    //     "api": addPrefixTo("administrative/reports/monthly-financial/"),
    //     "data": monthlyFinancialReportRequestBody,
    // }
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
    if (englishNumber===null || englishNumber===undefined){
        console.error("something went wrong, in my input :_)")
        return ""
    }
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
        displayDismiss(DISMISSLEVELS[msg.level], convertToPersianNumber(msg.message), DISMISSDURATIONS[msg.displayDuration])
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

function disableDeadlineSubmitButton() {
    const $btn = $("#deadline-submit")                 
        $btn.attr("disabled")
        $btn.removeClass("bg-green-700 hover:bg-green-800 cursor-pointer") 
        $btn.addClass("bg-gray-500") 
}
function enableDeadlineSubmitButton() {
    const $btn = $("#deadline-submit")                 
        $btn.removeAttr("disabled")
        $btn.removeClass("bg-gray-500") 
        $btn.addClass("bg-green-700 hover:bg-green-800 cursor-pointer") 
}

function canAdminChangeMenu() {
    // این تابع کاری به این نداره که ایتمی که ملت سفارش دادن حذف بشه یا
    // نشه؟‌اون در جای دیگری چک میشه
    let can = true
    let currentDateMomentObj = moment(toShamsiFormat(currentDate),'jYYYY-jM-jD')
    let selectedDateMomentObj = moment(toShamsiFormat(selectedDate),'jYYYY-jM-jD')

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

function menuItemBlock(id, itemName, pic, orderedByCount, itemProvider) {
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
    return `<li data-item-id="${id}" data-ordered-by="${orderedByCount}" class="flex flex-col bg-white rounded p-2 shadow-md hover:bg-zinc-100 ">
    <div class="flex w-full p-2 gap-2">
        <img
            src="${pic || DEFAULTITEMIMAGE}"
            alt=""
            onerror="imgError(this);"
            class="h-16 w-16 rounded object-cover self-start"
        />
        <div class="flex items-center">
            <div class="flex flex-row gap-2">
                <h3 class="text-xs text-gray-900">${convertToPersianNumber(itemName)}
                    <span class="flex flex-row w-fit mt-2 gap-1 text-xs text-gray-400">
                        ${convertToPersianNumber(itemProvider)}    
                    </span>
                </h3>
            </div>
        </div>
    </div>
    <div class="flex flex-row-reverse px-2 justify-between items-center" id="icons-box ">
        <div class="flex flex-row-reverse p-1 overflow-hidden items-center">
            <span class="menu-dot">
                <svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M7 12C7 13.1046 6.10457 14 5 14C3.89543 14 3 13.1046 3 12C3 10.8954 3.89543 10 5 10C6.10457 10 7 10.8954 7 12Z" fill="#9e9e9e"></path> <path d="M14 12C14 13.1046 13.1046 14 12 14C10.8954 14 10 13.1046 10 12C10 10.8954 10.8954 10 12 10C13.1046 10 14 10.8954 14 12Z" fill="#9e9e9e"></path> <path d="M21 12C21 13.1046 20.1046 14 19 14C17.8954 14 17 13.1046 17 12C17 10.8954 17.8954 10 19 10C20.1046 10 21 10.8954 21 12Z" fill="#9e9e9e"></path> </g></svg>
            </span>
            <a class="cursor-pointer op-icon hidden">
                <svg class="hover:fill-blue-400" width="24px" height="24px" viewBox="0 0 76 76" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" baseProfile="full" enable-background="new 0 0 76.00 76.00" xml:space="preserve" ><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill-opacity="1" stroke-width="0.2" stroke-linejoin="round" d="M 19,17L 41.25,17L 54,29.75L 54,37L 50,37L 50,33L 38,33L 38,21L 23,21L 23,55L 34.25,55L 31,59L 19,59L 19,17 Z M 54,56.75L 50,51L 50,47L 54,42L 54,56.75 Z M 40.25,59L 43.235,55.3453L 45.5,59L 40.25,59 Z M 41,22.25L 41,30L 48.75,30L 41,22.25 Z M 32.25,38L 39.5,38L 44.0374,44.4221L 49,38L 55.5,38L 47.0067,48.7036L 57,63L 49.5,63L 43.2223,53.5201L 38,60L 31.5,60L 40.2529,49.2387L 32.25,38 Z "></path> </g></svg>
            </a>
            <a class="cursor-pointer op-icon hidden ">
                <svg class="hover:fill-blue-400" width="18px" height="18px" fill="#000000" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0" class="hover:fill-orange-400"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M20.548,3.452a1.542,1.542,0,0,1,0,2.182L12.912,13.27,9.639,14.361l1.091-3.273,7.636-7.636A1.542,1.542,0,0,1,20.548,3.452ZM4,21H19a1,1,0,0,0,1-1V12a1,1,0,0,0-2,0v7H5V6h7a1,1,0,0,0,0-2H4A1,1,0,0,0,3,5V20A1,1,0,0,0,4,21Z"></path></g></svg>
            </a>
            <a class="ml-1 cursor-pointer op-icon hidden">
                <svg width="16px" height="16px" fill="#000000" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" id="delete-alt-2" class="hover:fill-red-600 icon glyph"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M17,4V5H15V4H9V5H7V4A2,2,0,0,1,9,2h6A2,2,0,0,1,17,4Z"></path><path d="M20,6H4A1,1,0,0,0,4,8H5.07l.87,12.14a2,2,0,0,0,2,1.86h8.14a2,2,0,0,0,2-1.86L18.93,8H20a1,1,0,0,0,0-2ZM13,17a1,1,0,0,1-2,0V11a1,1,0,0,1,2,0Z"></path></g></svg>
            </a>
        </div>
        <div class="flex flex-row items-center gap-2">
            <span class="text-xs text-red-700">${convertToPersianNumber("3 عدد باقی مانده")}</span>

            <a class="cursor-pointer op-icon hidden">
                <svg class="hover:fill-blue-400" width="12px" height="12px" viewBox="0 0 18 18" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:sketch="http://www.bohemiancoding.com/sketch/ns" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <title>icon/18/icon-edit</title> <desc>Created with Sketch.</desc> <defs> </defs> <g id="out" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd" sketch:type="MSPage"> <path d="M2.25,12.9378906 L2.25,15.75 L5.06210943,15.75 L13.3559575,7.45615192 L10.5438481,4.64404249 L2.25,12.9378906 L2.25,12.9378906 L2.25,12.9378906 Z M15.5306555,5.28145396 C15.8231148,4.98899458 15.8231148,4.5165602 15.5306555,4.22410082 L13.7758992,2.46934454 C13.4834398,2.17688515 13.0110054,2.17688515 12.718546,2.46934454 L11.3462366,3.84165394 L14.1583461,6.65376337 L15.5306555,5.28145396 L15.5306555,5.28145396 L15.5306555,5.28145396 Z" id="path" fill="#000000" sketch:type="MSShapeGroup"> </path> </g> </g></svg>    
            </a>
        </div>
    </div>

</li>`
}

function dropDownItemBlock(id, title, category,mealType, itemProvider) {
    return `<a data-item-id="${id}" class="flex flex-row justify-between text-xs px-4 py-2 text-gray-700 hover:bg-gray-100 active:bg-blue-100 cursor-pointer rounded-md">
    <span>${title}</span>

<span class="float-left">
<span class="italic text-gray-500 text-xs">${category}</span>
<span class="italic text-gray-500 text-xs">${mealType}</span>
<span class="italic text-gray-500 text-xs">${itemProvider}</span>

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
            item.mealType,
            item.itemProvider
        )
    })
    return HTML
}

function makeSelectedMenu(items) {
    let HTML = ""
    items.forEach(function (itemObj) {
        let selectedMenuItem = allItems.find(item => item.id === itemObj.id);
        HTML += menuItemBlock(selectedMenuItem.id, selectedMenuItem.itemName, selectedMenuItem.image, itemObj.orderedBy, selectedMenuItem.itemProvider)
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

function makeDeadlineModal(data) {
    let modal = ""
    let $modal = $("#deadlines-modal-body-container .deadlines-container")
    const todayTitle = "امروز"
    const pastDays = "روز قبل"
    data.forEach(function (obj) {
        modal += `<div data-mealtype="${obj.mealType}" class="deadline-row flex flex-row gap-1 items-center bg-slate-100 rounded-md p-2">
                    <p class="w-1/4 text-sm">
                        ${obj.mealType==="LNC" ? "ناهار" : "صبحانه"}
                    </p>
                    <div class="relative max-w-sm w-2/3 text-sm">
                        <div class="absolute inset-y-0 start-0 flex items-center ps-3.5 pointer-events-none">
                        <svg class="w-3 h-3 text-gray-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M20 4a2 2 0 0 0-2-2h-2V1a1 1 0 0 0-2 0v1h-3V1a1 1 0 0 0-2 0v1H6V1a1 1 0 0 0-2 0v1H2a2 2 0 0 0-2 2v2h20V4ZM0 18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8H0v10Zm5-8h10a1 1 0 0 1 0 2H5a1 1 0 0 1 0-2Z"/>
                        </svg>
                        </div>
                        <input disabled value="${obj.days!==0? convertToPersianNumber(obj.days):""} ${obj.days===0 ? todayTitle:pastDays} ساعت ${convertToPersianNumber(obj.hours)} " type="text"  class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pr-8 py-2.5 px-0.5" placeholder="تعداد روز ">
                    </div>
                    <input value="${obj.days}" type="text" data-days="${obj.days}" aria-describedby="helper-text-explanation" class="bg-gray-50 deadline-day border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-1/4 p-2.5 " placeholder="10" required />
                    <input value="${obj.hours}" type="text" data-hours="${obj.hours}" aria-describedby="helper-text-explanation" class="bg-gray-50 deadline-hour  border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-1/4 p-2.5 " placeholder="10" required />
                </div>`
    })
    $modal.empty()
    $modal.append(modal)
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
        menuItemBlock(
            selectedItem.id,
            selectedItem.itemName,
            selectedItem.image,
            0,
            selectedItem.itemProvider)
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
        return `${farsiPrefix}-${cd}-${item.itemName}.xlsx`;
}

function dailyOrdersReportFileName(dataNeededForFileName) {
    return `گزارش سفارش های امروز ${toShamsiFormat(selectedDate)}`
}

function dailyOrdersReportRequestBody() {
    return {
        "date" : toShamsiFormat(selectedDate)
    }
}

function dailyFoodProviderOrderingFileName(dataNeededForFileName) {
    return `گزارش تجمیعی سفارش های امروز ${toShamsiFormat(selectedDate)}`
}

function dailyFoodProviderOrderingRequestBody() {
    return {
        "date" : toShamsiFormat(selectedDate)
    }
}

function monthlyOrdersReportFileName(dataNeededForFileName) {
    return `گزارش سفارش های ماه ${selectedDate.month}`
}

function monthlyOrdersReportRequestBody() {
    return {
        "year" : selectedDate.year,
        "month" : selectedDate.month
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

function startDownloadReport(fileName, xlsxData) {
    // Create a Blob object from the XLSX data
    let blob = new Blob([xlsxData], {type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});

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

    let dm = `دانلود ${link.download} شروع شد `;
    displayDismiss(DISMISSLEVELS.INFO, convertToPersianNumber(dm), DISMISSDURATIONS.DISPLAY_TIME_TEN);
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

function loadUserBasicInfo() {
    $("#user-profile").attr("src", userProfileImg)
    $("#user-fullname").text(userFullName)
}


function imgError(image) {
    image.src = DEFAULTITEMIMAGE;
    return true;
}

function makeUserDropdownChoices() {
        $.ajax({
            url: addPrefixTo(`available-users/`),
            method: 'GET',
            dataType: 'json',
            success: function (data) {
                let choicesHTML = ""
                data.forEach(function(userObj) {
                    let nextURL = `?override_username=${userObj.Personnel}`
                    choicesHTML += `<li class="">
                        <div class="flex items-center ps-2 rounded 
                hover:bg-gray-100 ">
                            <a href="#" 
                            class="user-choice-a flex items-center justify-between w-full py-2
                            text-xs
                           text-gray-900 rounded ">
                                <span class="user-in-search">${userObj.FullName}</span>
                                <span class="flex gap-1">
                            <span class="user-in-search" data-username="${userObj.Personnel}">${userObj.Personnel}</span>
                            <svg class="h-3 w-3" fill="#000000"
                                 width="800px"
                                 height="800px"
                                 viewBox="0 0 24 24"
                                 xmlns="http://www.w3.org/2000/svg"><path
                                d="M12,1a11,11,0,0,0,0,22,1,1,0,0,0,0-2,9,9,0,1,1,9-9v2.857a1.857,1.857,0,0,1-3.714,0V7.714a1,1,0,1,0-2,0v.179A5.234,5.234,0,0,0,12,6.714a5.286,5.286,0,1,0,3.465,9.245A3.847,3.847,0,0,0,23,14.857V12A11.013,11.013,0,0,0,12,1Zm0,14.286A3.286,3.286,0,1,1,15.286,12,3.29,3.29,0,0,1,12,15.286Z"/></svg>
                            </span>
                            </a>
                        </div>
                    </li>`
                })
                $("#users-dropdown-list").append(choicesHTML)
            },
            error: function (xhr, status, error) {
                console.error('ERROR During fetching all users data', status, 'and error:', error, 'detail:', xhr.responseJSON);
                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
            }
        });
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
            userFullName = data["fullName"]
            userProfileImg = data["profile"]

            loadUserBasicInfo()
            makeUserDropdownChoices()

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
            // فچ کردن دلایل مربوط به گاد مود
            $.ajax({
                url: addPrefixTo(`administrative/reasons/`),
                method: 'GET',
                dataType: 'json',
                success: function (data) {
                    data.forEach(function(item) {
                        $("#reason-select").append($('<option>', {
                            value: item.id,
                            text: item.title
                        }).attr('data-reason-code', item.reasonCode));
                    })
                    if ($("#reason-select option:selected").attr("data-reason-code")==="OTHER"){
                        $("#reason-comment").empty()
                        $("#reason-comment").removeClass("hidden")
                    } 
                }
                })

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
                    document.body.style.zoom = "85%"
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
    
    $(document).on('mouseenter', '#menu-items-container li', function () {
        $(this).find(".menu-dot").addClass('hidden')
        $(this).find(".op-icon").removeClass('hidden')
        $(this).find(".op-icon").stop().animate({
            opacity: 1,
        }, 1000 , 'linear');
    })
   

    $(document).on('mouseleave', '#menu-items-container li', function () {
        $(this).find(".menu-dot").removeClass('hidden')
        $(this).find(".op-icon").addClass('hidden')
        $(this).find(".op-icon").stop().animate({
            opacity: 0,
        },500,'linear');
    })

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
            xhrFields: {
                responseType: 'blob'
            },
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
        xhrFields: {
            responseType: 'blob'
        },
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

    // user selection search dropdown by @ and normal form
    $(document).on('input', '#input-group-search', function () {
        $('.user-in-search').each(function () {
            $(this).closest("li").addClass("hidden")
        })

        let searchText = $(this).val().trim().toLowerCase();
        if (searchText === "") return

        searchText = searchText.substring(searchText.indexOf('@') + 1);
        $('.user-in-search').each(function () {
            let userText = $(this).text().trim().toLowerCase();
            if (userText.indexOf(searchText) !== -1) {
                $(this).closest('li').removeClass('hidden');
            }
        });
    });

    $(document).on('change', '#reason-select', function () {
        if ($("#reason-select option:selected").attr("data-reason-code")==="OTHER"){
            $("#reason-comment").empty()
            $("#reason-comment").removeClass("hidden")
        } else {
            $("#reason-comment").addClass("hidden")
        }
    })
    $(document).on('click', '#enter-godmode', function () {
        // validations 
        godModeEntryReason = $("#reason-select").val()
        godModeEntryReasonComment = $("#reason-comment").val()

        if (!godModeEntryReason && !godModeEntryReasonComment){
            console.log("insert reason before you go")
            return 
        }

        if ($("#reason-select option:selected").attr("data-reason-code")==="OTHER"){
            // check has comment or not !
            if (!godModeEntryReasonComment.trim()){
                displayDismiss(DISMISSLEVELS.ERROR, "علت را وارد کنید", DISMISSDURATIONS.DISPLAY_TIME_TEN)
                return
            }
        }
        
        localStorage.setItem("godModeEntryReason", godModeEntryReason)
        localStorage.setItem("godModeEntryReasonComment", godModeEntryReasonComment)
        localStorage.setItem("nextUsername", godModUsername)
        
        let nextURL = addPrefixTo(`?override_username=${godModUsername}`)
        window.open(nextURL, "_blank")

        $("#reason-comment").val("")
        $("#admin-action-reason-modal").click()
    })

    $(document).on('click', '.user-choice-a', function () {
        godModeEntryReason = undefined
        godModeEntryReasonComment = undefined
        godModUsername = $(this).find(".user-in-search[data-username]").text()
        
        $("#admin-action-reason-modal").click()
    })


    $(document).on('click', '#settings-dropdown #s-deadlines', function () {
        // fetching new deadlines and then make it
        $.ajax({
            url: addPrefixTo('administrative/deadlines/'),
            method: 'GET',
            dataType: 'json',
            success: function (data) {
                makeDeadlineModal(data)
                deadlines = data
                disableDeadlineSubmitButton()
                $("#deadline-notification").prop("checked", false)
                $("#deadlines-modal").click()
            },
            error: function (xhr, status, error) {
                console.error('Deadline modal cannot be constructed, data cannot feteched', status, 'and' +
                    ' error:', error, 'detail:', xhr.responseJSON);
                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
            }
        });
    })
    $(document).on('input', ".deadline-day, .deadline-hour" ,function () {
        // check if deadlines changed then deadline submit button get displayed 
        const oldDealine = JSON.stringify(deadlines)
        
        let liveDeadlines = []
        $(".deadline-row").each(function () {
            let mealType = $(this).attr("data-mealtype")
            let days = parseInt($(this).find(".deadline-day").val())
            let hours = parseInt($(this).find(".deadline-hour").val()) 
            liveDeadlines.push({days:days, hours:hours, mealType:mealType})
        })
        const newDealine = JSON.stringify(liveDeadlines)
        if (newDealine === oldDealine){
            disableDeadlineSubmitButton()
            return
        } 
        enableDeadlineSubmitButton()                
    })
    $(document).on('click', '#deadline-submit', function () {
        // gathering data and send to back
        let deadlines = []
        let isValid = true

        $(".deadline-row").each(function () {
            if (!isValid) return

            let mealType = $(this).attr("data-mealtype")
            let days = parseInt($(this).find(".deadline-day").val())
            let hours = parseInt($(this).find(".deadline-hour").val()) 
            
            // lets validate them
            // megative hours and days
            let err
            if (days < 0 || hours < 0) {
                err= "مقادیر نمی توانند منفی باشند"
                displayDismiss(DISMISSLEVELS.ERROR, err,DISMISSDURATIONS.DISPLAY_TIME_SHORT)
                isValid = false
                return 
            }

            
            // check emptyness 
            if ($(this).find(".deadline-day").val()==="" || $(this).find(".deadline-hour").val()==="") {
                err= "مقادیر نمی تواند خالی باشد"
                displayDismiss(DISMISSLEVELS.ERROR, err,DISMISSDURATIONS.DISPLAY_TIME_SHORT)
                isValid = false
                return
            }

            // check numeric value 
            if (isNaN(days) || isNaN(hours)) {
                err= "مقادیر باید به صورت عددی وارد شوند"
                displayDismiss(DISMISSLEVELS.ERROR, err,DISMISSDURATIONS.DISPLAY_TIME_SHORT)
                isValid = false
                return
            }
            
            // check boundry
            if (hours < 0 || hours > 24) {
                err= "ساعت تعیین شده مجاز نیست"
                displayDismiss(DISMISSLEVELS.ERROR, err,DISMISSDURATIONS.DISPLAY_TIME_SHORT)
                isValid = false
                return
            }

            deadlines.push({mealType:mealType, days:days, hours:hours})
        })

        if (!isValid) return

        
        let notifyPersonnel = $("#deadline-notification").prop("checked")   
        let data = {notifyPersonnel:notifyPersonnel, deadlines: deadlines}
        
        $.ajax({
            url: addPrefixTo(`administrative/deadlines/`),
            method: 'PATCH',
            contentType: 'application/json',
            data: JSON.stringify(data),
            statusCode:{
                200: function (data) {
                    let em="تغییرات اعمال شدند"
                    displayDismiss(DISMISSLEVELS.SUCCESS, em,DISMISSDURATIONS.DISPLAY_TIME_SHORT) 
                    $("#deadlines-modal").click()
                    catchResponseMessagesToDisplay(data.messages)
                }
            },
            error: function (xhr, status, error) {
                console.error('Deadline change submission failed!', status, 'and error:', error, 'detail:', xhr.responseJSON);
                checkErrorRelatedToAuth(xhr.status)
                displayDismiss(DISMISSLEVELS.ERROR, "مشکلی در اعمال تغییرات روی مهلت های سیستم پیش آمده است", DISMISSDURATIONS.DISPLAY_TIME_TEN)
            }
        });
    })

    $(document).on('click', '#s-add-new-item-to-system', function () {
        $.ajax({
            url: addPrefixTo('administrative/items/'),
            type: 'GET',
            success: function(response) {
                $('.new-item-form-container').html(response);
                $("#add-new-item-modal").click()
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error fetching HTML content: ' + textStatus, errorThrown);
                alert('Error loading content. Please try again.');
            }
        });
    })


    $(document).on('submit', '#add-item-form', function(event) {
        event.preventDefault();
    
        let formData = new FormData(this);
    
        var fileInput = $('#id_Image')[0];
        var file = fileInput.files[0];
    
        if ($("#id_ItemName").val().trim() === "") {
            em = "لطفا برای آیتم نام مناسب انتخاب کنید";
            displayDismiss(
                DISMISSLEVELS.ERROR,
                em,
                DISMISSDURATIONS.DISPLAY_TIME_TEN
            );
            return;
        }
    
        if ($("#id_ItemDesc").val().trim() === "") {
            em = "لطفا برای آیتم توضیحات مناسب وارد کنید";
            displayDismiss(
                DISMISSLEVELS.ERROR,
                em,
                DISMISSDURATIONS.DISPLAY_TIME_TEN
            );
            return;
        }
    
        if (!file) {
            em = "لطفا برای آیتم عکس انتخاب کنید";
            displayDismiss(
                DISMISSLEVELS.ERROR,
                em,
                DISMISSDURATIONS.DISPLAY_TIME_TEN
            );
            return;
        }
    
        // Check the file extension (must be an image)
        var validExtensions = [
            'image/jpeg',
            'image/png',
            'image/gif'
        ];
        if ($.inArray(file.type, validExtensions) === -1) {
            em = 'فرمت عکس انتخابی شما مجاز نمی باشد. باید از PNG, JPEG و GIF استفاده کنید';
            displayDismiss(
                DISMISSLEVELS.ERROR,
                em,
                DISMISSDURATIONS.DISPLAY_TIME_TEN
            );
            return;
        }
    
        var maxSize = 1 * 1024 * 1024; // 1MB
        if (file.size > maxSize) {
            em = "حجم عکس انتخابی بیشتر از 1 مگابایت است. امکان آپلود وجود ندارد";
            displayDismiss(
                DISMISSLEVELS.ERROR,
                convertToPersianNumber(em),
                DISMISSDURATIONS.DISPLAY_TIME_TEN
            );
            return;
        }
    
        // Create a new file with the current timestamp as the name
        var timestamp = Date.now();
        var newFileName = timestamp + '.' + file.name.split('.').pop();
        var newFile = new File([file], newFileName, { type: file.type });
    
        formData.append('Image', newFile);
        $.ajax({
            url: addPrefixTo('administrative/items/'), 
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(data) {
                loadAvailableItem();
    
                // load New Item Image
                let imgElement = $('<img>').attr('src', data.image);
                $('#dump-image-container').append(imgElement);
    
                $("#add-new-item-modal").click();
                em = "آیتم با موفقیت به لیست غذاهای قابل انتخاب سیستم اضافه شد";
                displayDismiss(
                    DISMISSLEVELS.SUCCESS,
                    convertToPersianNumber(em),
                    DISMISSDURATIONS.DISPLAY_TIME_TEN
                );
            },
            error: function(xhr, status, error) {
                console.error('NEW ITEM ADDITION FAILED', status, 'and error:', error, 'detail:', xhr.responseJSON);
                checkErrorRelatedToAuth(xhr.status);
                displayDismiss(DISMISSLEVELS.ERROR, "مشکلی هنگام افزودن آیتم به سیستم پیش آمده است", DISMISSDURATIONS.DISPLAY_TIME_TEN);
            }
        });
    });
    

    
});

