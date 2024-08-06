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
let latestDeliveryPlace = undefined
let deliveryPlaces = {}
let tempNewBuilding = undefined
let tempNewFloor = undefined
let queueOrderedItem = undefined
let selectedMenuToDisplay = "LNC"
let godModeEntryReason = undefined
let godModeEntryReasonComment = undefined
let actionReasonObj = {}
let currentDeliveryChangingMealType = "LNC"
let BRFOrderItemsCount = undefined
let LNCOrderItemsCount = undefined
let specificOrderMealType = undefined
const bpUsers = ["padidar.guest@eit", "gandi.guest@eit"]
const displayRemainingWarningAfter = 10

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
    if (englishNumber === null || englishNumber === undefined) {
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

function menuItemBlock(
    selected,
    id,
    serveTime,
    itemName,
    pic,
    itemDesc,
    price,
    itemCount = 0,
    editable = true,
    itemProvider,
    totalLikes,
    totalDisLikes,
    totalComments,
    isLiked,
    isDisLiked,
    isCommented,
    remaining
) {
    // remaining null means is unlimited, 
    if (remaining===null) remaining = 9999

    let foodActions = ""
    let finishedBadge = '<span class="border rounded rounded-md border-red-800 text-red-800 px-3 py-1 font-bold"> تمام شد</span>'
    let $itemRemainingCounter  = $(`<span data-remaining="${remaining}" class="item-remaining justify-self-start bg-red-100 text-red-800 text-xs p-1.5 py-0 rounded rounded-full">${convertToPersianNumber(`باقی مانده: ${remaining}`)}</span>`)
    let feedback = ""
    let $minus = $(`
            <div class="ml-2">
                <img class="!cursor-pointer remove-item w-6 h-6" src="${addStaticFilePrefixTo('images/minus-cirlce.svg')}" alt="">
            </div>`)
    let $add = $(`
            <div class="">
                <img class="!cursor-pointer add-item w-6 h-6" src="${addStaticFilePrefixTo('images/add-circle.svg')}" alt="">
            </div>`)
    
    if (editable && remaining === 0 && selected){
        // do not show add and just show minus and show the baqimande span
        foodActions = `
            ${$minus.prop("outerHTML")}
            <div class="ml-2">
                <span class="item-quantity">${convertToPersianNumber(itemCount)}</span>
            </div>
            ${$add.find("img").addClass("hidden").prop("outerHTML")}
        `
    }

    if (editable && remaining === 0 && !selected){
        // show tamam shod span and hide the baqimander span, hide add remove buttons
        foodActions = `
            ${finishedBadge}
        `
        $itemRemainingCounter.addClass("hidden")
    }

    if (editable && remaining > 0){
        foodActions = `
            ${$minus.prop("outerHTML")}
            <div class="ml-2">
                <span class="item-quantity">${convertToPersianNumber(itemCount)}</span>
            </div>
            ${$add.prop("outerHTML")}
        `
        // check the remaining if > 10 do not show it! else show the baqimande span
        remaining > displayRemainingWarningAfter ? $itemRemainingCounter.addClass("hidden") : $itemRemainingCounter 
    }

    if (!editable){
        foodActions = `
            ${editable ? $minus.prop("outerHTML") : ""}
                <div class="ml-2">
                    <span class="item-quantity">${!editable ? "x" : ""} ${convertToPersianNumber(itemCount)}</span>
                </div>
            ${editable ? $add.prop("outerHTML") : ""}`
        $itemRemainingCounter.addClass("hidden")
    }

    if (!godMode){
        feedback = `<div class="flex flex-row gap-1 items-center">
        <span data-feedback-count="${totalLikes}" data-byme="${isLiked ? 1:0}" class="like-item cursor-pointer flex items-center flex-row gap-0 ${isLiked ? "text-blue-700 scale-110" : "text-gray-500"} py-0.5 text-xs group hover:text-blue-700 hover:scale-110">
            <svg class="${isLiked ? "fill-blue-700 scale-110" : "fill-gray-500"} group-hover:fill-blue-700" width="16px" height="16px" viewBox="-2.4 -2.4 28.80 28.80" xmlns="http://www.w3.org/2000/svg" stroke="#000000" stroke-width="0.00024000000000000003" transform="rotate(0)"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round" stroke="#CCCCCC" stroke-width="0.24000000000000005"></g><g id="SVGRepo_iconCarrier"><path fill-rule="evenodd" clip-rule="evenodd" d="M15.9 4.5C15.9 3 14.418 2 13.26 2c-.806 0-.869.612-.993 1.82-.055.53-.121 1.174-.267 1.93-.386 2.002-1.72 4.56-2.996 5.325V17C9 19.25 9.75 20 13 20h3.773c2.176 0 2.703-1.433 2.899-1.964l.013-.036c.114-.306.358-.547.638-.82.31-.306.664-.653.927-1.18.311-.623.27-1.177.233-1.67-.023-.299-.044-.575.017-.83.064-.27.146-.475.225-.671.143-.356.275-.686.275-1.329 0-1.5-.748-2.498-2.315-2.498H15.5S15.9 6 15.9 4.5zM5.5 10A1.5 1.5 0 0 0 4 11.5v7a1.5 1.5 0 0 0 3 0v-7A1.5 1.5 0 0 0 5.5 10z"></path></g></svg>
            <span class="fb-real-count">${convertToPersianNumber(totalLikes)}</span> 
        </span>    
        <span data-feedback-count="${totalDisLikes}" data-byme="${isDisLiked ? 1:0}" class="dislike-item cursor-pointer  flex items-center  flex-row gap-0 ${isDisLiked ? "text-red-700 scale-110" : "text-gray-500"} py-0.5 text-xs group hover:text-red-700 hover:scale-110">
            <svg width="16px" height="16px" class="${isDisLiked ? "fill-red-700 scale-110" : "fill-gray-500"} group-hover:fill-red-700" viewBox="-2.4 -2.4 28.80 28.80" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path fill-rule="evenodd" clip-rule="evenodd" d="M8.1 20.5c0 1.5 1.482 2.5 2.64 2.5.806 0 .869-.613.993-1.82.055-.53.121-1.174.267-1.93.386-2.002 1.72-4.56 2.996-5.325V8C15 5.75 14.25 5 11 5H7.227C5.051 5 4.524 6.432 4.328 6.964A15.85 15.85 0 0 1 4.315 7c-.114.306-.358.546-.638.82-.31.306-.664.653-.927 1.18-.311.623-.27 1.177-.233 1.67.023.299.044.575-.017.83-.064.27-.146.475-.225.671-.143.356-.275.686-.275 1.329 0 1.5.748 2.498 2.315 2.498H8.5S8.1 19 8.1 20.5zM18.5 15a1.5 1.5 0 0 0 1.5-1.5v-7a1.5 1.5 0 0 0-3 0v7a1.5 1.5 0 0 0 1.5 1.5z"></path></g></svg>
            <span class="fb-real-count">${convertToPersianNumber(totalDisLikes)}</span>   
        </span> 
        <span data-feedback-count="${totalComments}" data-byme="${isCommented ? 1:0}" class="hidden comment-item mr-2 cursor-pointer  flex items-center  flex-row gap-0.5 ${isCommented ? "text-gray-700 scale-110" : "text-gray-500"} py-0.5 text-xs group hover:text-gray-700 hover:scale-110">
        <svg width="16px" height="16px" class="group-hover:fill-blue-900 fill-gray-500" viewBox="0 -0.5 25 25" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M9.0001 8.517C8.58589 8.517 8.2501 8.85279 8.2501 9.267C8.2501 9.68121 8.58589 10.017 9.0001 10.017V8.517ZM16.0001 10.017C16.4143 10.017 16.7501 9.68121 16.7501 9.267C16.7501 8.85279 16.4143 8.517 16.0001 8.517V10.017ZM9.8751 11.076C9.46089 11.076 9.1251 11.4118 9.1251 11.826C9.1251 12.2402 9.46089 12.576 9.8751 12.576V11.076ZM15.1251 12.576C15.5393 12.576 15.8751 12.2402 15.8751 11.826C15.8751 11.4118 15.5393 11.076 15.1251 11.076V12.576ZM9.1631 5V4.24998L9.15763 4.25002L9.1631 5ZM15.8381 5L15.8438 4.25H15.8381V5ZM19.5001 8.717L18.7501 8.71149V8.717H19.5001ZM19.5001 13.23H18.7501L18.7501 13.2355L19.5001 13.23ZM18.4384 15.8472L17.9042 15.3207L17.9042 15.3207L18.4384 15.8472ZM15.8371 16.947V17.697L15.8426 17.697L15.8371 16.947ZM9.1631 16.947V16.197C9.03469 16.197 8.90843 16.23 8.79641 16.2928L9.1631 16.947ZM5.5001 19H4.7501C4.7501 19.2662 4.89125 19.5125 5.12097 19.6471C5.35068 19.7817 5.63454 19.7844 5.86679 19.6542L5.5001 19ZM5.5001 8.717H6.25012L6.25008 8.71149L5.5001 8.717ZM6.56175 6.09984L6.02756 5.5734H6.02756L6.56175 6.09984ZM9.0001 10.017H16.0001V8.517H9.0001V10.017ZM9.8751 12.576H15.1251V11.076H9.8751V12.576ZM9.1631 5.75H15.8381V4.25H9.1631V5.75ZM15.8324 5.74998C17.4559 5.76225 18.762 7.08806 18.7501 8.71149L20.2501 8.72251C20.2681 6.2708 18.2955 4.26856 15.8438 4.25002L15.8324 5.74998ZM18.7501 8.717V13.23H20.2501V8.717H18.7501ZM18.7501 13.2355C18.7558 14.0153 18.4516 14.7653 17.9042 15.3207L18.9726 16.3736C19.7992 15.5348 20.2587 14.4021 20.2501 13.2245L18.7501 13.2355ZM17.9042 15.3207C17.3569 15.8761 16.6114 16.1913 15.8316 16.197L15.8426 17.697C17.0201 17.6884 18.1461 17.2124 18.9726 16.3736L17.9042 15.3207ZM15.8371 16.197H9.1631V17.697H15.8371V16.197ZM8.79641 16.2928L5.13341 18.3458L5.86679 19.6542L9.52979 17.6012L8.79641 16.2928ZM6.2501 19V8.717H4.7501V19H6.2501ZM6.25008 8.71149C6.24435 7.93175 6.54862 7.18167 7.09595 6.62627L6.02756 5.5734C5.20098 6.41216 4.74147 7.54494 4.75012 8.72251L6.25008 8.71149ZM7.09595 6.62627C7.64328 6.07088 8.38882 5.75566 9.16857 5.74998L9.15763 4.25002C7.98006 4.2586 6.85413 4.73464 6.02756 5.5734L7.09595 6.62627Z"></path> </g></svg>
        <span class="fb-real-count">${convertToPersianNumber(totalComments)}</span>  
        </span> 
    </div>   
    `
    }

    return `
    <li data-item-id="${id}" 
    data-item-order-count=${itemCount} 
    data-item-serve-time="${serveTime}"
    data-item-price="${price}"
class="flex flex-col gap-0  ${selected ? "bg-blue-100" : "bg-gray-200"}
    ${serveTime === selectedMenuToDisplay ? "" : "hidden"}
     border ${selected ? "border-blue-500" : ""} rounded p-4 pb-2 shadow-md 
      ${selected ? "hover:bg-blue-200" : "hover:bg-gray-300"}">

            <div class="flex items-center gap-4">
                <img
                        src="${pic || DEFAULTITEMIMAGE}"
                        alt=""
                        onerror="imgError(this);"
                        class="h-16 w-16 rounded object-cover self-start"
                />

                <div class="w-8/12 cursor-default">
                    <div class="flex flex-col">
                        <h3 class="text-sm text-gray-900 flex flex-row">${convertToPersianNumber(itemName)}
                            <span class="text-gray-500 py-0.5 text-xs scale-80 pr-1">
                                ${convertToPersianNumber(itemProvider)}    
                            </span>
                        </h3>
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
                    ${foodActions}
                </div>
            </div>
            <div class="flex justify-between items-center">
            <div class="flex flex-row gap-4 py-2 items-center">
                    <div class="w-16"></div>
                    <div >${feedback}</div>
                </div>    
                <div class="w-full flex flex-row-reverse items-center">
                    ${$itemRemainingCounter.prop("outerHTML")}
                </div>
                <div class="w-3/12 flex flex-row-reverse whitespace-nowrap">
                    <span class="text-sm">${insertCommas(convertToPersianNumber(price))}
                        <span class="text-xs text-gray-600">تومان</span>
                    </span>
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
    
        let selectedMenuItems = menuItems.find(function (entry) {
            return entry.date === toShamsiFormat(selectedDate);
        }).items;

        let selectedMenuItemRemaining = selectedMenuItems.find(function (entry) {
            return entry.id === itemObj.id;
        }).remaining

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
            selectedMenuItem.itemProvider,
            selectedMenuItem.totalLikes,
            selectedMenuItem.totalDisLikes,
            selectedMenuItem.totalComments,
            selectedMenuItem.isLiked,
            selectedMenuItem.isDisLiked,
            selectedMenuItem.isCommented,
            selectedMenuItemRemaining
        )
    })
    return HTML
}

function changeItemFeedback(newDataObj, itemId) {
    // changes all Items data
    let selectedMenuItem = allItems.find(item => item.id === itemId);
    for (const mustChange in newDataObj) {
        selectedMenuItem[mustChange] = newDataObj[mustChange]
    }
}

function changeMenuTypeDisplay(e) {
    let mustAdd = "text-blue-900 bg-blue-100 shadow-md"
    let mustRemove = "text-gray-500 bg-white"

    // با فرض اینکه دوتا منو داریم فعلا اگه چندتا شد باید ارایه شه
    let other = e.attr("id") === "BRF-menu" ? "#LNC-menu" : "#BRF-menu"
    let selectedMenu = e.attr("id") === "BRF-menu" ? "BRF" : "LNC"

    // تغییر منوی انتخابی پیشفرض
    selectedMenuToDisplay = selectedMenu

    e.removeClass(mustRemove).addClass(mustAdd)
    e.find("svg").removeClass("fill-gray-500").addClass("fill-blue-900")
    $(other).removeClass(mustAdd).addClass(mustRemove)
    $(other).find("svg").removeClass("fill-blue-900").addClass("fill-gray-500")

    let sd = $(`#dayBlocksWrapper div[data-date="${toShamsiFormat(selectedDate)}"]`)
    selectDayOnCalendar(sd)
}

function loadOrder(day, month, year) {
    let requestedDate = toShamsiFormat({ year: year, month: month, day: day })
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

    let requestedDate = toShamsiFormat({ year: year, month: month, day: day })
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


function changeFeedbackSectionHighligh(highlight, e, like) {
    let addColor = like === true ? "blue" : "red" 

    if (highlight){ 
        e.addClass(`text-${addColor}-700 scale-110`).removeClass(`text-gray-500`)
        e.find("svg").addClass(`fill-${addColor}-700 scale-110`).removeClass(`fill-gray-500`)
        return
    } 
    e.addClass(`text-gray-500`).removeClass(`text-${addColor}-700 scale-110`)
    e.find("svg").addClass(`fill-gray-500`).removeClass(`fill-${addColor}-700 scale-110`)
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
    return { BRF: day.openForBreakfast, LNC: day.openForLaunch }
}

function orderDeliveryPlace(dateObj, mealType) {
    // other mealtype is LNC btw :) 
    let prefix = mealType === "BRF" ? "breakfast" : "launch"

    let order = orders.find(function (orderObj) {
        return orderObj.orderDate === toShamsiFormat(dateObj)
    })
    if (order === undefined) {
        if (latestDeliveryPlace) {
            return latestDeliveryPlace
        } else return "مشخص نشده"
    }


    if (`${prefix}DeliveryBuilding` in order) {
        let deliveryBuilding = getDeliveryPlaceTitleByCode(order[`${prefix}DeliveryBuilding`])
        let deliveryFloor = getDeliveryPlaceTitleByCode(order[`${prefix}DeliveryFloor`])

        return deliveryBuilding + " " + deliveryFloor
    }
    return latestDeliveryPlace

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

function orderNoteDisplay(show) {
    if (show){
        $("#order-comment").removeClass("hidden")
    } else {
        $("#order-comment").addClass("hidden")
    }
}

function updateOrderNoteExistanceStatus(note) {
    if (note){
        $("#order-has-comment").removeClass("hidden")
    } else {
        $("#order-has-comment").addClass("hidden")
    }
}

function updateOrderBillDetail() {
    let orderItems = $(`#menu-items-container li`)
    let total = 0
    let fanavaran = orderSubsidy
    let debt = 0
    let BRFdeliveryPlace = convertToPersianNumber(orderDeliveryPlace(selectedDate, "BRF"))
    let LNCdeliveryPlace = convertToPersianNumber(orderDeliveryPlace(selectedDate, "LNC"))
    let $BRFDeliveryRow = $("#brf-delivery-place-row")
    let $LNCDeliveryRow = $("#lnc-delivery-place-row")
    let $BRFDeliveryEdit = $("#BRF-location-modal-trigger")
    let $LNCDeliveryEdit = $("#LNC-location-modal-trigger")
    let h = "hidden"


    // check if is editable or not
    let isOpenFor = canPersonnelChangeDeliveryPlace(selectedDate)
    if (BRFOrderItemsCount > 0) {
        $BRFDeliveryRow.removeClass("hidden")
        !isOpenFor.BRF ? $BRFDeliveryEdit.addClass(h) : $BRFDeliveryEdit.removeClass(h)
    } else {
        $BRFDeliveryRow.addClass("hidden")
    }

    if (LNCOrderItemsCount > 0) {
        $LNCDeliveryRow.removeClass("hidden")
        !isOpenFor.LNC ? $LNCDeliveryEdit.addClass(h) : $LNCDeliveryEdit.removeClass(h)
    } else {
        $LNCDeliveryRow.addClass("hidden")
    }

    // admin cannot change delivery place for guest users! 
    // check if user is in bypass users and admin is in god mode, hidden deliveryplace
    if (godMode && bpUsers.includes(userName)) {
        $BRFDeliveryEdit.addClass("hidden")
        $LNCDeliveryEdit.addClass("hidden")
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

    $("#brf-delivery-place").text(BRFdeliveryPlace)
    $("#lnc-delivery-place").text(LNCdeliveryPlace)

    // check order note option visiablity
    if (godMode && bpUsers.includes(userName) && orderTotalItemsQuantity(["BRF", "LNC"])!==0){
        orderNoteDisplay(true)
        
        // check the order has note, 
        let order = orders.find(function (orderObj) {
            return orderObj.orderDate === toShamsiFormat(selectedDate)
        })
        
        if (order===undefined) {
            updateOrderNoteExistanceStatus(note=undefined)
            return 
        }
        updateOrderNoteExistanceStatus(order.note)
        return 
    }
    orderNoteDisplay(false)

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

function updateItemRemaining(addRemaining, id){
    // update item remaining quantity 
    let $changedItem = $(`#menu-items-container li[data-item-id='${id}']`)
    let $remaining = $changedItem.find(".item-remaining")
    let itemRemaining = parseInt($remaining.attr("data-remaining"))
    addRemaining ? itemRemaining++ : itemRemaining--
    $remaining.attr("data-remaining", itemRemaining)
    $remaining.text(`${convertToPersianNumber(`باقی مانده: ${itemRemaining}`)}`)

    // update minus and add visibialty
    if (itemRemaining===0){
        $changedItem.find(".add-item").addClass("hidden")
    } else {
        $changedItem.find(".add-item").removeClass("hidden")
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
function updateOrderItemsQuantity() {
    let sumBRFOrderedItem = 0;
    let sumLNCOrderedItem = 0;
    let $items = $("#menu-items-container li");
    $items.each(function () {
        if ($(this).attr("data-item-serve-time") === "BRF") {
            sumBRFOrderedItem += parseInt($(this).attr("data-item-order-count"));
        } else {
            sumLNCOrderedItem += parseInt($(this).attr("data-item-order-count"));
        }
    });

    BRFOrderItemsCount = sumBRFOrderedItem
    LNCOrderItemsCount = sumLNCOrderedItem
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
    updateOrderItemsQuantity()
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
    if (!godMode) {
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

function orderNewItem(itemId, url) {
    $.ajax({
        url: url,
        method: 'POST',
        contentType: 'application/json',
        async: false,
        data: JSON.stringify(
            Object.assign({}, {
                "item": itemId,
                "date": toShamsiFormat(selectedDate)
            }, actionReasonObj)
        ),
        statusCode: {
            201: function (data) {
                addNewItemToMenu(itemId)
                updateOrders(selectedDate.month, selectedDate.year)
                updateItemsCounter()
                updateOrderItemsQuantity()
                updateHasOrderedCalendarDayBlock()
                updateOrderBillDetail()

                // updates related to item remaining
                updateItemRemaining(false, itemId)

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
    godModeEntryReason = parseInt(localStorage.getItem("godModeEntryReason"))
    godModeEntryReasonComment = localStorage.getItem("godModeEntryReasonComment")


    if (overrideUser) {
        targetURL = addPrefixTo(`panel/?override_username=${overrideUser}`)
        displayDismiss(DISMISSLEVELS.WARNING,
            "ورود به حالت دسترسی بدون محدودیت ادمین",
            DISMISSDURATIONS.DISPLAY_TIME_PARAMENT)

        localStorage.removeItem("nextUsername")
        localStorage.removeItem("godModeEntryReason")
        localStorage.removeItem("godModeEntryReasonComment")

        actionReasonObj = {
            "reason": godModeEntryReason
        }
        if (godModeEntryReasonComment) {
            actionReasonObj["comment"] = godModeEntryReasonComment
        }

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

            // make latest delivery string 
            if (latestFloor != null && latestBuilding != null) {
                latestDeliveryPlace = `${getDeliveryPlaceTitleByCode(latestBuilding)} ${getDeliveryPlaceTitleByCode(latestFloor)}`
            }

            loadUserBasicInfo()
            displayAdminButtonToAdminPersonnel()
            makeDeliveryBuildingModal()

            //  If an order is specified in the query params,
            //  the appropriate calendar should be created instead of default
            //  so we have to check this. 
            let queryParams = new URLSearchParams(window.location.search)
            let orderCode = queryParams.get("order")
            let specificOrderDate = {}
            if (orderCode) {
                specificOrderDate.year = parseInt(orderCode.substring(0, 4))
                specificOrderDate.month = parseInt(orderCode.substring(4, 6))
                specificOrderDate.day = parseInt(orderCode.substring(6, 8))
                specificOrderMealType = orderCode.substring(8)
                
                selectedDate = specificOrderDate
            } else {
                selectedDate = currentDate
            }


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
                        `calendar/?year=${specificOrderDate.year || currentDate.year}&month=${specificOrderDate.month || currentDate.month}`,
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
                    if (specificOrderMealType) changeMenuTypeDisplay($(`#${specificOrderMealType}-menu`))

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

        // check if delivery place specified or not, if both delivery building or floor are undefined, then system
        // displays delivery modal, and the added item is going to store in queue. after the delivery place was selected
        // by user then actual order (which that stored in queue) will be sent to the server.

        // *********** CAUTION **********
        // this if validation must be the last thing is going to check before add item ajax call
        if (latestFloor == undefined || latestBuilding == undefined) {
            // storing item to queue for further process
            // (after choosing place by user, this will be sent to back as and order for better UX)
            queueOrderedItem = { id: id, url: url }
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
                Object.assign({}, {
                    "item": id,
                    "date": toShamsiFormat(selectedDate)
                }, actionReasonObj)
            ),
            statusCode: {
                200: function (data) {
                    removeItemFromMenu(id)
                    updateOrders(selectedDate.month, selectedDate.year)
                    updateItemsCounter()
                    updateOrderItemsQuantity()
                    updateHasOrderedCalendarDayBlock()
                    updateOrderBillDetail()

                    // updates related to item remaining
                    updateItemRemaining(true, id)

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
            url: addPrefixTo(addOverrideUsernameIfIsAdmin(`calendar/?year=${currentDate.year}&month=${monthNumber}`, userName)),
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
    $(document).on('click', '#BRF-location-modal-trigger, #LNC-location-modal-trigger', function () {
        currentDeliveryChangingMealType = $(this).attr("data-meal-type")
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
                Object.assign({}, {
                    "newDeliveryBuilding": tempNewBuilding,
                    "newDeliveryFloor": tempNewFloor,
                    "date": toShamsiFormat(selectedDate),
                    "mealType": currentDeliveryChangingMealType
                }, actionReasonObj)
            ),
            statusCode: {
                200: function (data) {
                    latestBuilding = tempNewBuilding
                    latestFloor = tempNewFloor

                    latestDeliveryPlace = `${getDeliveryPlaceTitleByCode(latestBuilding)} ${getDeliveryPlaceTitleByCode(latestFloor)}`

                    updateOrders(selectedDate.month, selectedDate.year)
                    updateOrderBillDetail()
                    catchResponseMessagesToDisplay(data.messages)

                    // check if anything is in order queue, send to back (this must be happened before closing modal)
                    if (queueOrderedItem != undefined) {
                        orderNewItem(queueOrderedItem.id, queueOrderedItem.url)

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
        changeMenuTypeDisplay($(this))
    })

    $(document).on('click', '.like-item', function () {
        
        let $likeFeedback = $(this)
        let $likeFeedbackCount = $likeFeedback.find(".fb-real-count")
        let $disLikeFeedback = $(this).parent().find(".dislike-item")
        let $dislikeFeedbackCount = $disLikeFeedback.find(".fb-real-count")
        let totalLikes = parseInt($likeFeedback.attr("data-feedback-count"))
        let totalDisLikes = parseInt($disLikeFeedback.attr("data-feedback-count"))
        let isLiked = parseInt($likeFeedback.attr("data-byme"))
        let isDisLiked = parseInt($disLikeFeedback.attr("data-byme")) 
        let itemId = parseInt($likeFeedback.parents("li").attr("data-item-id"))

        if (isLiked===0 && isDisLiked===0){
            // call like
            $.ajax({
                url: addPrefixTo(`items/${itemId}/like/`),
                method: 'POST',
                contentType: 'application/json',
                statusCode: {
                    200: function (data) {
                        ++totalLikes
                        $likeFeedback.attr("data-byme", 1)
                        $likeFeedback.attr("data-feedback-count", totalLikes)
                        changeFeedbackSectionHighligh(true, $likeFeedback, true)
                        $likeFeedbackCount.text(convertToPersianNumber(totalLikes))
                        changeItemFeedback({totalLikes:totalLikes, isLiked:true}, itemId) 
                    }
                },
                error: function (xhr, status, error) {
                    console.error('Like item didnt work !', status, 'and' +
                        ' error:', error, 'detail:', xhr.responseJSON);
                    checkErrorRelatedToAuth(xhr.status)
                    catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                }
            });
            return
        }

        if (isLiked===0 && isDisLiked===1){
            // call reset then like
            $.ajax({
                url: addPrefixTo(`items/${itemId}/reset/`),
                method: 'POST',
                contentType: 'application/json',
                statusCode: {
                    200: function (data) {
                        $.ajax({
                            url: addPrefixTo(`items/${itemId}/like/`),
                            method: 'POST',
                            contentType: 'application/json',
                            statusCode: {
                                200: function (data) {
                                    ++totalLikes
                                    --totalDisLikes
                                    $likeFeedback.attr("data-byme", 1)
                                    $likeFeedback.attr("data-feedback-count", totalLikes)
                                    $disLikeFeedback.attr("data-byme", 0)
                                    $disLikeFeedback.attr("data-feedback-count", totalDisLikes)
                                    
                                    changeFeedbackSectionHighligh(true, $likeFeedback, true)
                                    changeFeedbackSectionHighligh(false, $disLikeFeedback, false)

                                    $likeFeedbackCount.text(convertToPersianNumber(totalLikes))
                                    $dislikeFeedbackCount.text(convertToPersianNumber(totalDisLikes))

                                    changeItemFeedback(
                                        {
                                            totalLikes:totalLikes,
                                            isLiked:true,
                                            totalDisLikes:totalDisLikes,
                                            isDisLiked:false
                                        }
                                        ,itemId) 
                                }
                            },
                            error: function (xhr, status, error) {
                                console.error('Like item didnt work !', status, 'and' +
                                    ' error:', error, 'detail:', xhr.responseJSON);
                                checkErrorRelatedToAuth(xhr.status)
                                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                            }
                        });
                    }
                },
                error: function (xhr, status, error) {
                    console.error('Like item didnt work !', status, 'and' +
                        ' error:', error, 'detail:', xhr.responseJSON);
                    checkErrorRelatedToAuth(xhr.status)
                    catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                }
            });
            return
        }

        if (isLiked===1 && isDisLiked===0){
            // just reset
            $.ajax({
                url: addPrefixTo(`items/${itemId}/reset/`),
                method: 'POST',
                contentType: 'application/json',
                statusCode: {
                    200: function (data) {
                        --totalLikes
                        $likeFeedback.attr("data-byme", 0)
                        $likeFeedback.attr("data-feedback-count", totalLikes)
                        changeFeedbackSectionHighligh(false, $likeFeedback, true)
                        $likeFeedbackCount.text(convertToPersianNumber(totalLikes))
                        changeItemFeedback({totalLikes:totalLikes, isLiked:false}, itemId) 
                    }
                },
                error: function (xhr, status, error) {
                    console.error('Like item didnt work !', status, 'and' +
                        ' error:', error, 'detail:', xhr.responseJSON);
                    checkErrorRelatedToAuth(xhr.status)
                    catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                }
            });
            return
        }
    })
    
    $(document).on('click', '.dislike-item', function () {
        let $likeFeedback =$(this).parent().find(".like-item") 
        let $likeFeedbackCount = $likeFeedback.find(".fb-real-count")
        let $disLikeFeedback = $(this)
        let $dislikeFeedbackCount = $disLikeFeedback.find(".fb-real-count")
        let totalLikes = parseInt($likeFeedback.attr("data-feedback-count"))
        let totalDisLikes = parseInt($disLikeFeedback.attr("data-feedback-count"))
        let isLiked = parseInt($likeFeedback.attr("data-byme"))
        let isDisLiked = parseInt($disLikeFeedback.attr("data-byme")) 
        let itemId = parseInt($likeFeedback.parents("li").attr("data-item-id"))

        if (isLiked===0 && isDisLiked===0){
            // call dislike
            $.ajax({
                url: addPrefixTo(`items/${itemId}/dis-like/`),
                method: 'POST',
                contentType: 'application/json',
                statusCode: {
                    200: function (data) {
                        ++totalDisLikes
                        $disLikeFeedback.attr("data-byme", 1)
                        $disLikeFeedback.attr("data-feedback-count", totalDisLikes)
                        changeFeedbackSectionHighligh(true, $disLikeFeedback, false)
                        $dislikeFeedbackCount.text(convertToPersianNumber(totalDisLikes))
                        changeItemFeedback({totalDisLikes:totalDisLikes, isDisLiked:true}, itemId) 
                    }
                },
                error: function (xhr, status, error) {
                    console.error('Like item didnt work !', status, 'and' +
                        ' error:', error, 'detail:', xhr.responseJSON);
                    checkErrorRelatedToAuth(xhr.status)
                    catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                }
            });
            return
        }

        if (isDisLiked===0 && isLiked===1){
            // call reset then dislike
            $.ajax({
                url: addPrefixTo(`items/${itemId}/reset/`),
                method: 'POST',
                contentType: 'application/json',
                statusCode: {
                    200: function (data) {
                        $.ajax({
                            url: addPrefixTo(`items/${itemId}/dis-like/`),
                            method: 'POST',
                            contentType: 'application/json',
                            statusCode: {
                                200: function (data) {
                                    ++totalDisLikes
                                    --totalLikes
                                    $disLikeFeedback.attr("data-byme", 1)
                                    $disLikeFeedback.attr("data-feedback-count", totalDisLikes)
                                    $likeFeedback.attr("data-byme", 0)
                                    $likeFeedback.attr("data-feedback-count", totalLikes)
                                    
                                    changeFeedbackSectionHighligh(true, $disLikeFeedback, false)
                                    changeFeedbackSectionHighligh(false, $likeFeedback, true)

                                    $likeFeedbackCount.text(convertToPersianNumber(totalLikes))
                                    $dislikeFeedbackCount.text(convertToPersianNumber(totalDisLikes))

                                    changeItemFeedback(
                                        {
                                            totalLikes:totalLikes,
                                            isLiked:false,
                                            totalDisLikes:totalDisLikes,
                                            isDisLiked:true
                                        }
                                        ,itemId) 
                                }
                            },
                            error: function (xhr, status, error) {
                                console.error('Like item didnt work !', status, 'and' +
                                    ' error:', error, 'detail:', xhr.responseJSON);
                                checkErrorRelatedToAuth(xhr.status)
                                catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                            }
                        });
                    }
                },
                error: function (xhr, status, error) {
                    console.error('Like item didnt work !', status, 'and' +
                        ' error:', error, 'detail:', xhr.responseJSON);
                    checkErrorRelatedToAuth(xhr.status)
                    catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                }
            });
            return
        }

        if (isDisLiked===1 && isLiked===0){
            // just reset
            $.ajax({
                url: addPrefixTo(`items/${itemId}/reset/`),
                method: 'POST',
                contentType: 'application/json',
                statusCode: {
                    200: function (data) {
                        --totalDisLikes
                        $disLikeFeedback.attr("data-byme", 0)
                        $disLikeFeedback.attr("data-feedback-count", totalDisLikes)
                        changeFeedbackSectionHighligh(false, $disLikeFeedback, false)
                        $dislikeFeedbackCount.text(convertToPersianNumber(totalDisLikes))
                        changeItemFeedback({totalDisLikes:totalDisLikes, isDisLiked:false}, itemId) 
                    }
                },
                error: function (xhr, status, error) {
                    console.error('Like item didnt work !', status, 'and' +
                        ' error:', error, 'detail:', xhr.responseJSON);
                    checkErrorRelatedToAuth(xhr.status)
                    catchResponseMessagesToDisplay(JSON.parse(xhr.responseText).messages)
                }
            });
            return
        }
    })
    
    $(document).on('click', '.comment-item', function () {
        alert("comment")
    })
    // Order comment modal 
    $(document).on('click', '#order-comment', function () {
        // loading note
        $("#order-comment-textarea").empty()
        let order = orders.find(function (orderObj) {
            return orderObj.orderDate === toShamsiFormat(selectedDate)
        })
        let note = ""
        if (order){
            note = order.note
        }
        $("#order-comment-textarea").val(note)
        $("#order-comment-modal").click()
    })

    $(document).on('click', '#order-comment-submit', function () {
        let note = $("#order-comment-textarea").val().trim() || null
        $.ajax({
            url: addPrefixTo(addOverrideUsernameIfIsAdmin(`administrative/notes/`, userName)),
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(
                Object.assign({}, {
                    "note": note,
                    "date": toShamsiFormat(selectedDate)
                }, actionReasonObj)
            ),
            statusCode:{
                200: function (data) {
                    let em="یادداشت با موفقیت به روزرسانی شد"
                    if (note===null) em="یادداشت پاک شد"
                    displayDismiss(DISMISSLEVELS.SUCCESS, em,DISMISSDURATIONS.DISPLAY_TIME_SHORT) 
                    updateOrders(selectedDate.month, selectedDate.year)
                    
                    // update comment exsistance display
                    updateOrderNoteExistanceStatus(note)
                    
                    $("#order-comment-modal").click()
                    catchResponseMessagesToDisplay(data.messages)
                }
            },
            error: function (xhr, status, error) {
                console.error('Deadline change submission failed!', status, 'and error:', error, 'detail:', xhr.responseJSON);
                checkErrorRelatedToAuth(xhr.status)
                displayDismiss(DISMISSLEVELS.ERROR, "مشکلی در اعمال تغییرات روی یادداشت سفارش پیش آمده است", DISMISSDURATIONS.DISPLAY_TIME_TEN)
            }
        });
    })
    
});
