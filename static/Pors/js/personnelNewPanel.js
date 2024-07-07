const URL_PREFIX = "/PersonnelService/Pors/"
const STATIC_PREFIX = "/static/Pors/"

function addPrefixTo(str) {
    return URL_PREFIX + str
}

function addStaticFilePrefixTo(str) {
    return STATIC_PREFIX + str
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
let userName = undefined
let isAdmin = undefined
let godMode = undefined
let firstDayOfWeek = undefined
let lastDayOfMonth = undefined
let holidays = undefined
let daysWithMenu = undefined
let orderedDays = undefined
let menuItems = undefined
let availableItems = undefined
let allItems = undefined
let orderableBreakFastItemCount = undefined
let orders = undefined
let orderSubsidy = undefined
let latestBuilding = null
let latestFloor = null
let deliveryPlaces = {}
let tempNewBuilding = undefined
let tempNewFloor = undefined
let queueOrderedItem = undefined
let selectedMenuToDisplay = "LNC"

function getDeliveryPlaceTitleByCode(code) {
    for (const building of deliveryPlaces) {
        if (building.code === code) {
            return building.title;
        }
        for (const floor of building.floors) {
            if (floor.code === code) {
                return floor.title;
            }
        }
    }
    return "Unknown";
}

function makeDeliveryBuildingModal() {
    let counter = 0
    let buildingChoicesHTML = ""
    for (const building of deliveryPlaces) {
        buildingChoicesHTML += `<li>
        <input type="radio" id="bld-${counter}" name="bld" value="bld-${counter}"
               class="hidden peer" data-place-code="${building.code}" data-place-type="BLD" required>
            <label for="bld-${counter}"
                   class="inline-flex items-center justify-between w-full p-5 text-gray-900 bg-white border border-gray-200 rounded-lg cursor-pointer  peer-checked:border-blue-600 peer-checked:text-blue-600 hover:text-gray-900 hover:bg-gray-100 ">
                <div class="block">
                    <div class="w-full text-base font-semibold">
                        ${convertToPersianNumber(building.title)}
                    </div>
                </div>
                <svg class="w-4 h-4 ms-3 rtl:rotate-180 text-gray-500 "
                     aria-hidden="true"
                     xmlns="http://www.w3.org/2000/svg" fill="none"
                     viewBox="0 0 14 10">
                    <path stroke="currentColor" stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2" d="M1 5h12m0 0L9 1m4 4L9 9"/>
                </svg>
            </label>
    </li>`
        counter++
    }
    $("#building-choices-modal").text("")
    $("#building-choices-modal").append(buildingChoicesHTML)

}

function makeDeliveryFloorModal(buildingCode) {
    let counter = 0
    let buildingChoicesHTML = ""
    for (const building of deliveryPlaces) {
        if (building.code !== buildingCode) continue
        for (const floor of building.floors) {
            buildingChoicesHTML +=
                `<li>
                    <input type="radio" id="flr-${counter}" name="flr"
                           value="flr-${counter}"
                           class="hidden peer" data-place-code="${floor.code}"
                           data-place-type="FLR" required>
                        <label for="flr-${counter}"
                               class="inline-flex items-center justify-between w-full p-5 text-gray-900 bg-white border border-gray-200 rounded-lg cursor-pointer  peer-checked:border-blue-600 peer-checked:text-blue-600 hover:text-gray-900 hover:bg-gray-100 ">
                            <div class="block">
                                <div class="w-full text-base font-semibold">
                                   ${convertToPersianNumber(floor.title)}
                                </div>
                            </div>
                            <svg
                                class="w-4 h-4 ms-3 rtl:rotate-180 text-gray-500 "
                                aria-hidden="true"
                                xmlns="http://www.w3.org/2000/svg" fill="none"
                                viewBox="0 0 14 10">
                                <path stroke="currentColor"
                                      stroke-linecap="round"
                                      stroke-linejoin="round"
                                      stroke-width="2"
                                      d="M1 5h12m0 0L9 1m4 4L9 9"/>
                            </svg>
                        </label>
                </li>`
            counter++
        }

    }
    $("#floor-choices-modal").text("")
    $("#floor-choices-modal").append(buildingChoicesHTML)

}

function insertCommas(str) {

    // برای خوانا تر شدن رقم ها
    // برای مثال عدد 192000 به 192,000 تبدیل می شود
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


function zfill(number, width) {
    let numberString = number.toString();
    while (numberString.length < width) {
        numberString = '0' + numberString;
    }
    return numberString;
}

function catchResponseMessagesToDisplay(messages) {
    if (messages === undefined) return
    messages.forEach(function (msg) {
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
    setTimeout(function () {
        fadingElement.fadeOut(500, function () {
            fadingElement.remove();
        });
    }, duration);

}

function canPersonnelChangeMenuItem(serveTime, openForLaunch, openForBreakfast) {
    if (serveTime === "LNC") return openForLaunch
    return openForBreakfast
}

function calendarDayBlock(dayNumberStyle, dayNumber, dayOfWeek, monthNumber, yearNumber, hasMenu, hasOrder) {
    let opacity = ""
    let MenuIcon = addStaticFilePrefixTo("images/food-dish.svg")
    let menuIconHTML = `<img class="w-6 h-6 hidden" src="${MenuIcon}" alt="">`
    let hasOrderCheckIcon = `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M4 12.6111L8.92308 17.5L20 6.5" stroke="#26a269" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>`
    let hasOrderHTML = `<div class="${hasOrder ? "" : "hidden"} check-logo w-4 h-4">${hasOrderCheckIcon}</div>`
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


    let dayTitle = `${WEEK_DAYS[dayOfWeek]} ${convertToPersianNumber(dayNumber)} ${YEAR_MONTHS[monthNumber]}`

    return `<div data-date="${date}" data-day-title="${dayTitle}" data-day-number="${dayNumber}" class="cd- ${opacity} cursor-pointer flex flex-col items-center justify-around border border-gray-100 p-4 grow hover:bg-gray-200 hover:border-gray-300">
                                <div> 
                                    <span class="text-2xl ${dayNumberStyle}">${convertToPersianNumber(dayNumber)}</span>
                                </div>
                                <div class="w-6 h-6 flex flex-col items-center">
                                    ${menuIconHTML}
                                    ${hasOrderHTML}
                                </div>
                            </div>`
}

function menuItemBlock(selected, id, serveTime, itemName, pic, itemDesc, price, itemCount = 0, editable = true, itemProvider) {
    let minus = `
    <div class="ml-2">
                        <img class="!cursor-pointer remove-item w-6 h-6"
                             src="${addStaticFilePrefixTo('images/minus-cirlce.svg')}" alt="">
                    </div>`
    let add = `<div class="">
                        <img class="!cursor-pointer add-item w-6 h-6"
                             src="${addStaticFilePrefixTo('images/add-circle.svg')}" alt="">
                    </div>
    `

    let breakfastLabel = `<span class="px-1 py-0 text-xs text-white font-bold bg-gray-800 italic rounded-full"> صبحانه </span>`
    return `
    <li data-item-id="${id}" 
    data-item-order-count=${itemCount} 
    data-item-serve-time="${serveTime}"
    data-item-price="${price}"
class="flex flex-col gap-0  ${selected ? "bg-blue-100" : "bg-gray-200"}
    ${serveTime===selectedMenuToDisplay ? "": "hidden"}
     border ${selected ? "border-blue-500" : ""} rounded p-4 shadow-md 
      ${selected ? "hover:bg-blue-200" : "hover:bg-gray-300"}">

            <div class="flex items-center gap-4">
                <img
                        src="${pic}"
                        alt=""
                        class="h-16 w-16 rounded object-cover self-start"
                />

                <div class="w-8/12 cursor-default">
                    <div><h3 class="text-sm text-gray-900">${convertToPersianNumber(itemName)} ${serveTime === "BRF" ? breakfastLabel : ""}</h3>

                        <dl class="mt-1 space-y-px text-xs text-gray-600">
                            <div>
                                <dt class="inline"></dt>

                            </div>

                            <div>
                                <dt class="inline">${convertToPersianNumber(itemDesc)}
                                </dt>

                            </div>
                        </dl>
                    </div>
                </div>
                <div class="flex justify-end w-3/12">

                    ${editable ? minus : ""}
                    <div class="ml-2">
                        <span class="item-quantity">${!editable ? "x" : ""} ${convertToPersianNumber(itemCount)}</span>
                    </div>
                    ${editable ? add : ""}
                    
                </div>
            </div>
            <div class="flex justify-between items-center">
            <div class="flex flex-row gap-2 py-2 items-center">
                <span class="flex flex-row gap-1 bg-gray-300 border border-gray-400 rounded-full px-2 py-0.5 text-xs">
                    <svg class="w-4 h-4 fill-black" viewBox="0 -18.83 122.88 122.88" version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="enable-background:new 0 0 122.88 85.22" xml:space="preserve"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <style type="text/css">.st0{fill-rule:evenodd;clip-rule:evenodd;}</style> <g> <path class="st0" d="M82.08,7.33h35.4c1.35,0,2.46,1.11,2.46,2.46V30.4h0.24c1.49,0,2.7,1.22,2.7,2.7v3.01 c0,1.51-1.24,2.74-2.74,2.74h-19c14.12,1.26,22.19,14.39,21.31,31.46h-12.56c-0.01,8.23-6.69,14.89-14.92,14.89 c-8.23,0-14.91-6.67-14.92-14.89H41.68c-0.01-0.27-0.02-0.53-0.03-0.8c0.03,1.81-0.08,3.73-0.34,5.78L7.87,59.54L0,55.82 c6.32-7.19,13.94-10.21,23.16-8.13c1.42,0.36,2.76,0.78,4.03,1.26c-1.3-0.5-2.67-0.92-4.11-1.28l10.52-34.65l-4.75-0.09l0,0 c-0.98-0.02-2.04,0.25-2.71-0.23c-1.16-0.03-2.17-0.73-2.87-1.83c-0.63-0.98-1.01-2.32-1.01-3.78c0-1.46,0.39-2.8,1.01-3.78 c0.52-0.81,1.2-1.4,1.98-1.67c0.01-0.16,0.02-0.27,0.04-0.3c1.12-1.79,3.3-1.25,5.24-1.25l1.89,0.12c1.37,0.17,2.71,0.62,4,1.36 l2.16,1.21h1.75l5.88,1.14c1.92,0.37,2.2,0.21,1.75,2.58c-0.06,0.3-0.13,0.6-0.23,0.89c-0.58,1.73-1.04,1.09-2.83,0.72l-5.51-1.14 c0.21,2.22-0.49,4.94-1.48,8.12c3.17,2.68,4.59,6.5,2.43,11.53l-5.26,16.21C43.9,49.08,49.2,54.74,49.5,64.03h11.67 c7.19-5.45,6-15.15-1.89-21.35v-3.82h0v-5.84c0.01-1.85,1-2.68,2.84-2.63h17.5V9.79C79.62,8.44,80.73,7.33,82.08,7.33L82.08,7.33z M90.68,26.67h18.21c0.14,0,0.26,0.12,0.26,0.26v0.52c0,0.14-0.12,0.26-0.26,0.26H90.68c-0.14,0-0.26-0.12-0.26-0.26v-0.52 C90.42,26.79,90.53,26.67,90.68,26.67L90.68,26.67z M100.54,15.35c5.33,0.43,9.19,4.44,8.52,9.72H90.5 c-0.65-5.31,3.22-9.33,8.59-9.72v-1.49h-1.48c-0.15,0-0.27-0.12-0.27-0.27v-0.97c0-0.15,0.12-0.27,0.27-0.27h4.37 c0.15,0,0.27,0.12,0.27,0.27v0.97c0,0.15-0.12,0.27-0.27,0.27h-1.45V15.35L100.54,15.35L100.54,15.35z M7.91,59.56l13.3,6.3 l-4.32-1.98c-2.97,0.63-5.19,3.27-5.19,6.42c0,3.63,2.94,6.57,6.57,6.57c3.63,0,6.57-2.94,6.57-6.57c0-1.12-0.28-2.17-0.77-3.1 l9.08,4.3c-0.61,7.68-7.04,13.72-14.87,13.72c-8.24,0-14.92-6.68-14.92-14.92C3.34,66.08,5.09,62.27,7.91,59.56L7.91,59.56 L7.91,59.56z M25.27,4.2c0.06,1.92,0.19,4.39,0.28,6.05c-0.16-0.14-0.32-0.32-0.46-0.55c-0.42-0.65-0.67-1.58-0.67-2.62 s0.26-1.97,0.67-2.62C25.15,4.37,25.21,4.28,25.27,4.2L25.27,4.2z M88.4,70.32h13.14c-0.01,3.62-2.95,6.54-6.57,6.54 C91.35,76.87,88.41,73.94,88.4,70.32L88.4,70.32L88.4,70.32z"></path> </g> </g></svg>
                    ${convertToPersianNumber(itemProvider)}    
                </span>
            </div>
                <div class="">
                                            <span class="text-sm">${insertCommas(convertToPersianNumber(price))}<span
                                                    class="text-xs text-gray-600">تومان</span></span>
                    <span class="text-xs"></span>

                </div>
            </div>


        </li>`

}

function dropDownItemBlock(id, title, category, mealType) {
    return `<a data-item-id="${id}" class="flex flex-row justify-between px-4 py-2 text-gray-700 hover:bg-gray-100 active:bg-blue-100 cursor-pointer rounded-md">
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

function makeSelectedMenu(items, openForLaunch, openForBreakfast, ordered) {
    let HTML = ""
    items.forEach(function (itemObj) {
        let price = 0
        let selectedMenuItem = allItems.find(item => item.id === itemObj.id);
        let quantity = 0
        let editableItem = canPersonnelChangeMenuItem(
            selectedMenuItem.serveTime,
            openForLaunch,
            openForBreakfast)

        if (editableItem && ordered) {
            price = selectedMenuItem.currentPrice
            quantity = itemObj.quantity
        }
        if (editableItem && !ordered) price = selectedMenuItem.currentPrice
        if (!editableItem && ordered) {
            price = itemObj.pricePerItem
            quantity = itemObj.quantity
        }


        if (!editableItem && !ordered) return


        HTML += menuItemBlock(
            ordered,
            selectedMenuItem.id,
            selectedMenuItem.serveTime,
            selectedMenuItem.itemName,
            selectedMenuItem.image,
            selectedMenuItem.itemDesc,
            price,
            quantity,
            editableItem,
            selectedMenuItem.itemProvider
        )
    })
    return HTML
}


function loadOrder(day, month, year) {
    let requestedDate = toShamsiFormat({year: year, month: month, day: day})
    let selectedMenu = menuItems.find(function (entry) {
        return entry.date === requestedDate;
    });
    let order = orders.find(function (orderObj) {
        return orderObj.orderDate === requestedDate
    })
    if (order === undefined) return

    let orderHTML = makeSelectedMenu(
        order.orderItems,
        selectedMenu.openForLaunch,
        selectedMenu.openForBreakfast,
        true
    )
    orderHTML += "</hr>"
    $("#menu-items-container").prepend(orderHTML)


}

function loadMenu(day, month, year) {

    // allMenus در واقع همون selectedItems هست


    // منوی قبلی را پاک می کنیم
    $("#menu-items-container li").remove()

    if (menuItems === undefined) return

    let requestedDate = toShamsiFormat({year: year, month: month, day: day})
    let selectedMenu = menuItems.find(function (entry) {
        return entry.date === requestedDate;
    });

    // حالا باید آیتم هارو بگیریم
    if (selectedMenu !== undefined) {
        // let menuItemsId = extractIds(selectedMenu.items)

        let order = orders.find(function (orderObj) {
            return orderObj.orderDate === requestedDate
        })
        let orderItemsId = []
        if (!(order === undefined)) {
            orderItemsId = extractIds(order.orderItems)

        }

        let justMenu = selectedMenu.items.filter(function (item) {
            return !orderItemsId.includes(item.id);
        });

        // در صورتی که وقتش جفتشون گذشته باشه خب هیچی  منویی لازم نیست که
        // لود بشه
        if (!selectedMenu.openForLaunch && !selectedMenu.openForBreakfast) return
        // تعداد سفارش ها به ازای هر آیتم در آیتم های selectedMenu هم
        // فرستاده می شود که به صورت زیر است
        // {
        //  1: 12,
        //  5 :26
        // }
        let menuHTML = makeSelectedMenu(
            justMenu,
            selectedMenu.openForLaunch,
            selectedMenu.openForBreakfast,
            false
        )
        $("#menu-items-container").append(menuHTML)
    }


}

function makeCalendar(startDayOfWeek, endDayOfMonth, holidays, daysWithMenu, monthNumber, yearNumber, orderedDays) {

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

        let dayNumberStyle = ""
        let dayMenuIcon = false
        let hasOrder = false

        // در صورتی که روز تعطیل بود اون رو قرمز می کنیم
        if (holidays.includes(dayNumber)) {
            dayNumberStyle = "text-red-500"
        }

        // در صورتی که توسط اداری برای اون روز منو تعیین شده بود آن ایکن را
        // تغییر می دهیم


        if (daysWithMenu.includes(dayNumber)) {
            dayMenuIcon = true
        }
        if (orderedDays.includes(dayNumber)) {
            hasOrder = true
        }


        newCalendarHTML += calendarDayBlock(
            dayNumberStyle,
            dayNumber,
            startDayOfWeek % 8,
            monthNumber,
            yearNumber,
            dayMenuIcon,
            hasOrder)


        startDayOfWeek++
        if (startDayOfWeek % 8 === 0) {
            startDayOfWeek++
        }
    }
    $("#dayBlocksWrapper").append(newCalendarHTML)
    $("#dayBlocksWrapper").attr("data-month", monthNumber)
    $("#dayBlocksWrapper").attr("data-year", yearNumber)


}

function getSubsidy() {
//     میره و با توجه به تاریخ سوبسید مورد نظر رو میگیره
    // و برای محاسبات مالی ازش استفاده می شه

    $.ajax({
        url: addPrefixTo(`get-subsidy/?date=${encodeURIComponent(toShamsiFormat(selectedDate))}`),
        method: 'GET',
        dataType: 'json',
        async: false,
        success: function (data) {
            orderSubsidy = data["data"]["subsidy"]
            catchResponseMessagesToDisplay(data.messages)
        },
        error: function (xhr, status, error) {
            console.error('Available Items cannot be loaded', status, 'and' +
                ' error:', error, 'detail:', xhr.responseJSON);
            catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
        }
    });
}

function canPersonnelChangeDeliveryPlace(dateObj) {
    let day = menuItems.find(function (orderObj) {
        return orderObj["date"] === toShamsiFormat(dateObj)
    })
    if (day === undefined) return false
    return day.openForLaunch && day.openForBreakfast
}

function orderDeliveryPlace(dateObj) {
    let order = orders.find(function (orderObj) {
        return orderObj.orderDate === toShamsiFormat(dateObj)
    })
    if (order === undefined) {
        if (latestFloor != null && latestBuilding != null) {
            return getDeliveryPlaceTitleByCode(latestBuilding) +
                " " +
                getDeliveryPlaceTitleByCode(latestFloor)
        } else return "مشخص نشده"
    }
    let deliveryBuilding = getDeliveryPlaceTitleByCode(order["deliveryBuilding"])
    let deliveryFloor = getDeliveryPlaceTitleByCode(order["deliveryFloor"])

    return deliveryBuilding + " " + deliveryFloor
}

function billDisplay(show) {
    let thereIsNoOrderForDay = $("#no-order-for-today")
    let billDetail = $("#day-bill")
    if (show) {
        thereIsNoOrderForDay.addClass("hidden")
        billDetail.removeClass("hidden")
        return
    }
    thereIsNoOrderForDay.removeClass("hidden")
    billDetail.addClass("hidden")
}

function updateOrderBillDetail() {
    let orderItems = $(`#menu-items-container li`)
    let total = 0
    let fanavaran = orderSubsidy
    let debt = 0
    let deliveryPlace = convertToPersianNumber(orderDeliveryPlace(selectedDate))

    if (!canPersonnelChangeDeliveryPlace(selectedDate)) {
        $("#location-modal-trigger").addClass("hidden")
    } else {
        $("#location-modal-trigger").removeClass("hidden")

    }

    if (orderItems.length === 0) {
        billDisplay(false)
        return
    }
    billDisplay(true)

    orderItems.each(function () {
        let itemPrice = parseInt($(this).attr("data-item-price"))
        let itemQuantity = parseInt($(this).attr("data-item-order-count"))
        total += itemPrice * itemQuantity
    })

    debt = total - fanavaran
    if (debt < 0) {
        debt = 0
    }

    $(".total-amount").text(insertCommas(convertToPersianNumber(total)))
    $(".subsidy-amount").text(insertCommas(convertToPersianNumber(fanavaran)))
    $(".debt-amount").text(insertCommas(convertToPersianNumber(debt)))

    $("#delivery-place").text(deliveryPlace)

}

function updateItemMenuDetails(id, quantity) {
    let changedItem = $(`#menu-items-container li[data-item-id='${id}']`)
    if (quantity !== 0) {
        changedItem.removeClass("hover:bg-gray-300")
        changedItem.removeClass("bg-gray-200")

        changedItem.addClass("hover:bg-blue-200")
        changedItem.addClass("border-blue-500")
        changedItem.addClass("bg-blue-100")

    } else {
        changedItem.removeClass("hover:bg-blue-200")
        changedItem.removeClass("border-blue-500")
        changedItem.removeClass("bg-blue-100")

        changedItem.addClass("hover:bg-gray-300")
        changedItem.addClass("bg-gray-200")
    }
    changedItem.find(".item-quantity").text(convertToPersianNumber(quantity))
}

function canAddNewItem(itemId) {
    /*     چک های مرتبط با محدودیت و باقی مانده طرفیت اینجا صورت می گیرد
        برای مثال با توجه به متغیر orderableBreakFastItemCount که از بکند
         دریافت می شود و به صورت پیشفرض 1 بوده است یعنی اینکه مجموع ایتم های
          قابل سفارش صبحانه 1 است

          نکته توالی شروط در اینجا باید رعایت شود چرا که فقط یک ارور مسیج باز
           خواهد گشت
     */

    let item = allItems.find(function (obj) {
        return obj.id === itemId
    })
    let sumBreakfastItems = orderTotalItemsQuantity(["BRF"])
    if (item.serveTime === "BRF" && sumBreakfastItems >= orderableBreakFastItemCount) {
        let x = convertToPersianNumber(orderableBreakFastItemCount)
        return {
            "res": false,
            "msg": `امکان اضافه کردن حداکثر ${x} آیتم به منوی صبحانه روز وجود دارد`
        }
    }
    return {
        "res": true
    }


}

function addNewItemToMenu(id) {
    let changedItem = $(`#menu-items-container li[data-item-id='${id}']`)
    let itemQuantity = parseInt(changedItem.attr("data-item-order-count"))
    itemQuantity++
    changedItem.attr("data-item-order-count", itemQuantity)
    updateItemMenuDetails(id, itemQuantity)
}

function finishLoadingDisplay() {
    $("#loading").addClass("hidden")
    $("#main-panel-wrapper").removeClass("hidden")

}

function removeItemFromMenu(id) {
    let changedItem = $(`#menu-items-container li[data-item-id='${id}']`)
    let itemQuantity = parseInt(changedItem.attr("data-item-order-count"))
    if (itemQuantity !== 0) itemQuantity--

    changedItem.attr("data-item-order-count", itemQuantity)
    updateItemMenuDetails(id, itemQuantity)
}

function loadAvailableItem() {
    // ایتم های قابل انتخاب جدید رو دریافت می کند
    $.ajax({
        url: addPrefixTo(`all-items/`),
        method: 'GET',
        dataType: 'json',
        async: false,
        success: function (data) {
            allItems = data
            // همین جا بررسی می کنیم اگه که ایتم عکس نداشت عکس پیشفرض رو
            // قرار می دهیم
            allItems.forEach(function (item) {
                if (item.image === "") item.image = DEFAULTITEMIMAGE
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

function addOverrideUsernameIfIsAdmin(url, username) {
    return godMode ? addQueryParamToPath(url, "override_username", username) : url;
}

function addQueryParamToPath(path, paramName, paramValue) {
    const urlObject = new URL(`http://dummyhost/${path}`);
    urlObject.searchParams.append(paramName, paramValue);
    let fullPath = urlObject.pathname + urlObject.search
    return fullPath.substring(1);
}

function updateOrders(month, year) {

    $.ajax({
        url: addPrefixTo(addOverrideUsernameIfIsAdmin(`calendar/?year=${year}&month=${month}`, userName)),
        method: 'GET',
        async: false,
        dataType: 'json',
        success: function (data) {
            menuItems = data["menuItems"]
            daysWithMenu = data["daysWithMenu"]
            orders = data["orders"]
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
    $("#menu-items-counter").text(
        convertToPersianNumber(
            orderTotalItemsQuantity(["BRF", "LNC"])
        ))
}

function orderTotalItemsQuantity(serveTime) {
    // serveTime یا BRF یا LNC
    if (serveTime === undefined) serveTime = ["LNC", "BRF"]

    let items = $("#menu-items-container li");
    let sumOrderedItem = 0;

    items.each(function () {
        if (serveTime.includes($(this).attr("data-item-serve-time"))) {
            sumOrderedItem += parseInt($(this).attr("data-item-order-count"));
        }
    });
    return sumOrderedItem
}

function updateHasOrderedCalendarDayBlock() {
    let currentShamsi = toShamsiFormat(selectedDate)
    let sumOrderedItem = orderTotalItemsQuantity()

    let checkLogo = $(`.cd-[data-date="${currentShamsi}"] .check-logo`)
    if (sumOrderedItem === 0) {
        checkLogo.addClass("hidden")
        return
    }
    checkLogo.removeClass("hidden")
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


function selectDayOnCalendar(e) {
    let selectedShamsiDate = e.attr("data-date")
    let selectedShamsiDateTitle = e.attr("data-day-title")
    updateSelectedDate(selectedShamsiDate)
    updateSelectedDayOnCalendar(selectedShamsiDate)
    changeMenuDate(selectedShamsiDateTitle)
    loadMenu(selectedDate.day, selectedDate.month, selectedDate.year)
    loadOrder(selectedDate.day, selectedDate.month, selectedDate.year)
    updateItemsCounter()
    updateHasOrderedCalendarDayBlock()
    getSubsidy()
    updateOrderBillDetail()
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

    $(`#calSelectedMonth option[value="${currentMonth}"]`).prop("selected", true)


}

function getCurrentCalendarMonth() {
    return $("#dayBlocksWrapper").attr("data-month")
}

function getSelectedCalendarMonthDropdown() {
    return $("#calSelectedMonth option:selected").attr("value")
}

function redirectToGateway() {
    window.location.replace(addPrefixTo("auth-gateway/"))
}

function checkErrorRelatedToAuth(errorCode) {
    if (errorCode === 403) redirectToGateway()
}

function loadUserBasicInfo() {
    $("#user-profile").attr("src", userProfileImg)
    $("#user-fullname").text(userFullName)
    if (!godMode){
        $("#god-mode").addClass("hidden")
    }
}

function displayAdminButtonToAdminPersonnel() {
    if (isAdmin) $("#go-to-admin-button").removeClass("hidden")



}

function imgError(image) {
    image.src = DEFAULTITEMIMAGE;
    return true;
}

function orderNewItem(itemId, url){
    $.ajax({
            url: url,
            method: 'POST',
            contentType: 'application/json',
            async: false,
            data: JSON.stringify(
                {
                    "item": itemId,
                    "date": toShamsiFormat(selectedDate)
                }
            ),
            statusCode: {
                201: function (data) {
                    addNewItemToMenu(itemId)
                    updateOrders(selectedDate.month, selectedDate.year)
                    updateItemsCounter()
                    updateHasOrderedCalendarDayBlock()
                    updateOrderBillDetail()
                    catchResponseMessagesToDisplay(data.messages)
                }
            },
            error: function (xhr, status, error) {
                console.error('Item not added!', status, 'and error:', error, 'detail:', xhr.responseJSON);
                checkErrorRelatedToAuth(xhr.status)
                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
            }
        });
}

function isInChangingPlaceProcess() {

}


$(document).ready(function () {


    /* وقتی که صفحه به صورت کامل لود شد کار های زیر را به ترتیب انجام می دهیم
    */

    let targetURL = undefined
    let overrideUser = localStorage.getItem("nextUsername")
    if (overrideUser) {
        targetURL = addPrefixTo(`panel/?override_username=${overrideUser}`)
        displayDismiss(DISMISSLEVELS.WARNING,
            "ورود به حالت دسترسی بدون محدودیت ادمین",
            DISMISSDURATIONS.DISPLAY_TIME_PARAMENT)

        localStorage.removeItem("nextUsername")
    } else {
        targetURL = addPrefixTo(`panel/`)
    }
    $.ajax({
        url: targetURL,
        method: 'GET',
        dataType: 'json',
        async: false,
        success: function (data) {
            isSystemOpen = data["isOpenForPersonnel"]
            orderableBreakFastItemCount = data["totalItemsCanOrderedForBreakfastByPersonnel"]
            currentDate.day = data["firstOrderableDate"]["day"]
            currentDate.month = data["firstOrderableDate"]["month"]
            currentDate.year = data["firstOrderableDate"]["year"]
            latestBuilding = data["latestBuilding"]
            latestFloor = data["latestFloor"]
            deliveryPlaces = data["buildings"]
            userFullName = data["fullName"]
            userProfileImg = data["profile"]
            userName = data["userName"]
            isAdmin = data["isAdmin"]
            godMode = data["godMode"]

            loadUserBasicInfo()
            displayAdminButtonToAdminPersonnel()
            makeDeliveryBuildingModal()

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
                url: addPrefixTo(
                    addOverrideUsernameIfIsAdmin(
                        `calendar/?year=${currentDate.year}&month=${currentDate.month}`,
                        userName
                    )),
                method: 'GET',
                dataType: 'json',
                success: function (data) {
                    firstDayOfWeek = data["firstDayOfWeek"]
                    lastDayOfMonth = data["lastDayOfMonth"]
                    holidays = data["holidays"]
                    daysWithMenu = data["daysWithMenu"]
                    menuItems = data["menuItems"]
                    orderedDays = data["orderedDays"]
                    orders = data["orders"]

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
                        parseInt(requestedYear),
                        orderedDays
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
                    loadOrder(
                        currentDate.day,
                        currentDate.month,
                        currentDate.year
                    )
                    document.body.style.zoom = "85%"
                    finishLoadingDisplay()
                    catchResponseMessagesToDisplay(data.messages)


                },
                error: function (xhr, status, error) {
                    let em = "EXECUTION ERROR: Default calendar load failed!"
                    displayDismiss(DISMISSLEVELS.ERROR, em, DISMISSDURATIONS.DISPLAY_TIME_LONG)
                    catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                }
            });
            catchResponseMessagesToDisplay(data.messages)

        },
        error: function (xhr, status, error) {
            let em = "EXECUTION ERROR: Personnel panel is Unreachable"
            displayDismiss(DISMISSLEVELS.ERROR, em, DISMISSDURATIONS.DISPLAY_TIME_LONG)
            catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
        }
    });
    if (isSystemOpen === false) return

    $(document).on('click', '#menu-items-container li .add-item', function () {
        // اضافه کردن غذا به منو


        let url = undefined
        if ($(this).parent().parent().parent().parent().attr("data-item-serve-time") === "BRF") {
            url = addPrefixTo(addOverrideUsernameIfIsAdmin(`create-breakfast-order/`, userName))
        } else {
            url = addPrefixTo(addOverrideUsernameIfIsAdmin(`create-order/`, userName))
        }
        let id = parseInt($(this).parent().parent().parent().parent().attr("data-item-id"))
        let can = canAddNewItem(id)
        if (!can.res) {
            displayDismiss(
                DISMISSLEVELS.ERROR,
                can.msg,
                DISMISSDURATIONS.DISPLAY_TIME_SHORT
            )
            return
        }

        // check if delivery place specified or not, if both delivery building or floor are undefined, then system
        // displays delivery modal, and the added item is going to store in queue. after the delivery place was selected
        // by user then actual order (which that stored in queue) will be sent to the server.

        // *********** CAUTION **********
        // this if validation must be the last thing is going to check before add item ajax call
        if (latestFloor == undefined || latestBuilding == undefined){
            // storing item to queue for further process
            // (after choosing place by user, this will be sent to back as and order for better UX)
            queueOrderedItem = {id:id, url:url}
            $("#building-place-modal").click()
            return
        }

        orderNewItem(id, url)

    });

    $(document).on('click', '#menu-items-container li .remove-item', function () {
        // حذف کردن یک غذا از منوی روز انتخاب شده
        let id = parseInt($(this).parent().parent().parent().parent().attr("data-item-id"))
        let itemCount = parseInt($(this).parent().parent().parent().parent().attr("data-item-order-count"))

        if (itemCount === 0) return


        $.ajax({
            url: addPrefixTo(addOverrideUsernameIfIsAdmin(`remove-item-from-order/`, userName)),
            method: 'POST',
            contentType: 'application/json',
            async: false,
            data: JSON.stringify(
                {
                    "item": id,
                    "date": toShamsiFormat(selectedDate)
                }
            ),
            statusCode: {
                200: function (data) {
                    removeItemFromMenu(id)
                    updateOrders(selectedDate.month, selectedDate.year)
                    updateItemsCounter()
                    updateHasOrderedCalendarDayBlock()
                    updateOrderBillDetail()
                    catchResponseMessagesToDisplay(data.messages)
                }
            },
            error: function (xhr, status, error) {
                console.error('Item not removed!', status, 'and error:', error, 'detail:', xhr.responseJSON);
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
                url: addPrefixTo(addOverrideUsernameIfIsAdmin(`calendar/?year=${currentDate.year}&month=${currentDate.month}`, userName)),
                method: 'GET',
                dataType: 'json',

                success: function (data) {
                    firstDayOfWeek = data["firstDayOfWeek"]
                    lastDayOfMonth = data["lastDayOfMonth"]
                    holidays = data["holidays"]
                    daysWithMenu = data["daysWithMenu"]
                    menuItems = data["menuItems"]
                    orderedDays = data["orderedDays"]
                    orders = data["orders"]
                    makeCalendar(
                        parseInt(firstDayOfWeek),
                        parseInt(lastDayOfMonth),
                        holidays,
                        daysWithMenu,
                        currentDate.month,
                        currentDate.year,
                        orderedDays
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
            url: addPrefixTo(addOverrideUsernameIfIsAdmin(`calendar/?year=${currentDate.year}&month=${monthNumber}`,userName)),
            method: 'GET',
            dataType: 'json',

            success: function (data) {
                firstDayOfWeek = data["firstDayOfWeek"]
                lastDayOfMonth = data["lastDayOfMonth"]
                holidays = data["holidays"]
                daysWithMenu = data["daysWithMenu"]
                menuItems = data["menuItems"]
                orderedDays = data["orderedDays"]
                orders = data["orders"]
                makeCalendar(
                    parseInt(firstDayOfWeek),
                    parseInt(lastDayOfMonth),
                    holidays,
                    daysWithMenu,
                    monthNumber,
                    currentDate.year,
                    orderedDays
                )
                updateSelectedDayOnCalendar(toShamsiFormat(selectedDate))
                catchResponseMessagesToDisplay(data.messages)
            },
            error: function (xhr, status, error) {
                console.error('Item not removed!', status, 'and error:', error, 'detail:', xhr.responseJSON);
                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
            }
        });
    })

    // دکمه ویرایش مکان تحویل سفارش
    $(document).on('click', '#location-modal-trigger', function () {

        queueOrderedItem = undefined
        $("#building-place-modal").click()
    })

    //دکمه انتخاب یکی از ساختمان ها
    $(document).on('change', '#building-choices-modal input', function () {
        tempNewBuilding = $(this).parent().find("input").attr("data-place-code")

        // for remove the latest user input choice in UI
        makeDeliveryBuildingModal()

        // making appropriate floor modal based on building choice
        makeDeliveryFloorModal(tempNewBuilding)

        //opening floor modal
        $("#floor-place-modal").click()

        // for closing building modal
        $("#building-place-modal").click()
    })

    //دکمه انتخاب یکی از طبقه ها
    $(document).on('change', '#floor-choices-modal input', function () {
        tempNewFloor = $(this).parent().find("input").attr("data-place-code")

        $.ajax({
            url: addPrefixTo(addOverrideUsernameIfIsAdmin(`change_order_delivery_place/`, userName)),
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(
                {
                    "newDeliveryBuilding": tempNewBuilding,
                    "newDeliveryFloor": tempNewFloor,
                    "date": toShamsiFormat(selectedDate)
                }
            ),
            statusCode: {
                200: function (data) {
                    latestBuilding = tempNewBuilding
                    latestFloor = tempNewFloor
                    updateOrders(selectedDate.month, selectedDate.year)
                    updateOrderBillDetail()
                    catchResponseMessagesToDisplay(data.messages)

                    // check if anything is in order queue, send to back (this must be happened before closing modal)
                    if (queueOrderedItem != undefined){
                        orderNewItem(queueOrderedItem.id,queueOrderedItem.url)

                        // flush order queue after modal, no matter it will succeed or not!
                        queueOrderedItem = undefined
                    }

                    tempNewBuilding = undefined
                    tempNewFloor = undefined
                }
            },
            error: function (xhr, status, error) {
                console.error('Delivery place manipulation not applied!', status, 'and' +
                    ' error:', error, 'detail:', xhr.responseJSON);
                checkErrorRelatedToAuth(xhr.status)
                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
            }
        });

        // for closing floor modal
        $("#floor-place-modal").click()
    })



    // دکمه انتخاب منو برای نمایش منوی انتخابی (فعلا ناهار و صبحانه رو داریم)
    $(document).on('click', '.separate-menu', function () {
        let mustAdd = "text-blue-900 bg-blue-100"
        let mustRemove = "text-black bg-white"

        // با فرض اینکه دوتا منو داریم فعلا اگه چندتا شد باید ارایه شه
        let other = $(this).attr("id") === "BRF-menu" ? "#LNC-menu" : "#BRF-menu"
        let selectedMenu = $(this).attr("id") === "BRF-menu" ? "BRF" : "LNC"

        // تغییر منوی انتخابی پیشفرض
        selectedMenuToDisplay = selectedMenu

        $(this).removeClass(mustRemove).addClass(mustAdd)
        $(this).find("svg").removeClass("fill-black").addClass("fill-blue-900")
        $(other).removeClass(mustAdd)
        $(other).find("svg").removeClass("fill-blue-900").addClass("fill-black")

        let sd = $(`#dayBlocksWrapper div[data-date="${toShamsiFormat(selectedDate)}"]`)
        selectDayOnCalendar(sd)
    })


});
