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
let isSystemOpen = false
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
function convertArrayToIntegers(stringArray) {
    // Using map to convert each string to an integer
    var intArray = stringArray.map(function (str) {
        return parseInt(str, 10); // Using parseInt with base 10
    });

    return intArray;
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

function toShamsiFormat(dateobj) {
    // 1402/08/09
    return `${dateobj.year}/${zfill(dateobj.month, 2)}/${zfill(dateobj.day, 2)}`
}

function zfill(number, width) {
    let numberString = number.toString();
    while (numberString.length < width) {
        numberString = '0' + numberString;
    }
    return numberString;
}

function calendarDayBlock(dayNumberStyle, dayNumber, dayOfWeek, monthNumber, yearNumber, hasMenu) {
    let MenuIcon = "https://www.svgrepo.com/show/383690/food-dish.svg"
    let menuIconHTML = ""
    if (hasMenu === true) {
        menuIconHTML = `<img className="w-8 h-8" src="${MenuIcon}" alt="">`
    }
    let date = toShamsiFormat({
        year: yearNumber,
        month: monthNumber,
        day: dayNumber
    })

    let dayTitle = `${WEEK_DAYS[dayOfWeek]} ${convertToPersianNumber(dayNumber)} ${YEAR_MONTHS[monthNumber]}`

    return `<div data-date="${date}" data-day-title="${dayTitle}" data-day-number="${dayNumber}" class="cd- cursor-pointer flex flex-col items-center justify-between border border-gray-100 p-4 grow hover:bg-gray-200 hover:border-gray-300">
                                <div> 
                                    <span class="text-4xl ${dayNumberStyle}">${convertToPersianNumber(dayNumber)}</span>
                                </div>
                                <div>
                                    ${menuIconHTML}
                                </div>
                            </div>`
}

function menuItemBlock(id, itemName, pic) {
    return `<li data-item-id="${id}" class="flex flex-col cursor-pointer bg-sky-100 border border-sky-700 rounded p-4 shadow-md hover:bg-gray-300 ">
    <div class="flex items-center gap-4">
        <img
                src="${pic}"
                alt=""
                class="h-16 w-16 rounded object-cover self-start"
        />
        <div class="w-8/12">
            <div><h3 class="text-sm text-gray-900">${itemName}</h3>
            </div>
        </div>
        <div class="flex justify-end w-3/12">

            <div class="ml-2">
                <img class="w-6 h-6"
                     src="https://www.svgrepo.com/show/472000/trash-04.svg" alt="">
            </div>
        </div>
    </div>
</li>`
}

function dropDownItemBlock(id, title) {
    return `<a data-item-id="${id}" class="block px-4 py-2 text-gray-700 hover:bg-gray-100 active:bg-blue-100 cursor-pointer rounded-md">${title}</a>`
}

function makeDropDownChoices(items) {
    let HTML = ""
    items.forEach(function (item) {
        HTML += dropDownItemBlock(item.id, item.itemName)
    })
    return HTML
}

function loadMenu(day, month, year, allMenus) {
    // allMenus در واقع همون selectedItems هست

    // منوی قبلی را پاک می کنیم
    $("#menu-items-container").remove()

    let requestedDate = toShamsiFormat({year: year, month: month, day: day})
    let selectedMenu = allMenus.find(function (entry) {
        return entry.date === requestedDate;
    });

    // حالا باید آیتم هارو بگیریم
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


        let dayNumberStyle = ""
        let dayMenuIcon = false

        // در صورتی که روز تعطیل بود اون رو قرمز می کنیم
        if (holidays.includes(dayNumber)) {
            dayNumberStyle = "text-red-500"
        }

        // در صورتی که توسط اداری برای اون روز منو تعیین شده بود آن ایکن را
        // تغییر می دهیم
        if (daysWithMenu.includes(dayNumber)) {
            dayMenuIcon = true
        }


        newCalendarHTML += calendarDayBlock(dayNumberStyle, dayNumber, startDayOfWeek % 8, monthNumber, yearNumber, dayMenuIcon)
        startDayOfWeek++
        if (startDayOfWeek % 8 === 0) {
            startDayOfWeek++
        }
    }
    $("#dayBlocksWrapper").append(newCalendarHTML)


}

function displaySystemIsNotAvailable() {
    $("#system-is-not-available").removeClass("hidden")
}

function blurMainPanel() {
    $("#main-panel").addClass("blur-sm")

}

function addNewItemToMenu(id) {
    let selectedItem = availableItems.find(item => item.id == id);
    $("#menu-items-container").append(
        menuItemBlock(selectedItem.id, selectedItem.itemName, selectedItem.image)
    )

    removeItemFromAvailableItems(id)
}

function removeItemFromMenu(id) {
    $(`#menu-items-container li[data-item-id='${id}']`).remove();
    addItemToAvailableItems(id)
}

function removeItemFromAvailableItems(id) {
    $(`#dropdown-menu a[data-item-id='${id}']`).remove();

}

function addItemToAvailableItems(id) {
    let selectedItem = availableItems.find(item => item.id == id);
    $("#dropdown-menu").append(
        dropDownItemBlock(id, selectedItem.itemName)
    )
}

function loadAvailableItem() {
    // آیتم های قبل را پاک می کنیم
    $("#dropdown-menu a").remove();

    // ایتم های قابل انتخاب جدید رو دریافت می کند
    $.ajax({
        url: `administrative/available-items/`,
        method: 'GET',
        dataType: 'json',
        success: function (data) {
            $("#dropdown-menu").append(makeDropDownChoices(data))
            availableItems = data
        },
        error: function (xhr, status, error) {
            console.error('Available Items cannot be loaded', status, 'and' +
                ' error:', error);
        }
    });
}

function updateSelectedDate(month) {
}

function updateSelectedItems(month, year) {
    $.ajax({
        url: `administrative/calendar/?year=${year}&month=${month}`,
        method: 'GET',
        dataType: 'json',
        success: function (data) {
            selectedItems = data[1]["SelectedItems"]
            daysWithMenu = data[0]["daysWithMenu"]

        },
        error: function (xhr, status, error) {
            console.error('Selected Items cannot be updated!', status, 'and error:', error);
        }
    });
}

function changeMenuDate(dateTitle) {
    $("#menu-date-wrapper").text(dateTitle)
}

function updateItemsCounter(shamsiFormatDate) {
    let len = 0
    if (selectedItems !== undefined) {
        let selectedMenu = selectedItems.find(function (entry) {
            return entry.date === shamsiFormatDate;
        });
        len = selectedMenu.length
    }

    $("#menu-items-counter").text(len)


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
    updateSelectedDayOnCalendar(selectedShamsiDate)
    changeMenuDate(selectedShamsiDateTitle)
    updateItemsCounter(selectedShamsiDate)
    // updateSelectedDate()
    // loadMenu()
}

function getCurrentCalendarMonth() {
    return $("#calSelectedMonth option:selected").attr("value")
}

$(document).ready(function () {




    /* وقتی که صفحه به صورت کامل لود شد کار های زیر را به ترتیب انجام می دهیم
    */


    $.ajax({
        url: `administrative/panel/`,
        method: 'GET',
        dataType: 'json',
        async: false,
        success: function (data) {
            console.log(data)
            isSystemOpen = data["isOpen"]
            currentDate.day = data["currentDate"]["day"]
            currentDate.month = data["currentDate"]["month"]
            currentDate.year = data["currentDate"]["year"]

            selectedDate = currentDate

            // در صورتی که سیستم قابل استفاده نبود و می خواست از دسترس
            // خارج شه
            if (isSystemOpen === false) {
                displaySystemIsNotAvailable()
                blurMainPanel()
                return
            }

            $.ajax({
                url: `administrative/calendar/?year=${currentDate.year}&month=${currentDate.month}`,
                method: 'GET',
                dataType: 'json',
                success: function (data) {
                    console.log(data)
                    firstDayOfWeek = data[0]["firstDayOfWeek"]
                    lastDayOfMonth = data[0]["lastDayOfMonth"]
                    holidays = data[0]["holidays"]
                    daysWithMenu = data[0]["daysWithMenu"]
                    selectedItems = data[1]["SelectedItems"]

                    let requestedYear = data[0]["year"]
                    let requestedMonth = data[0]["month"]

                    // تقویم این ماه به صورت پیشفرض لود می شود
                    makeCalendar(
                        parseInt(firstDayOfWeek),
                        parseInt(lastDayOfMonth),
                        holidays,
                        daysWithMenu,
                        parseInt(requestedMonth),
                        parseInt(requestedYear)
                    )
                    updateSelectedDayOnCalendar(toShamsiFormat(selectedDate))
                    // انتخاب کردن روز فعلی به عنوان پیشفرض
                    let sd = $(`#dayBlocksWrapper div[data-date="${toShamsiFormat(selectedDate)}"]`)
                    selectDayOnCalendar(sd)

                    // منوی غذا امروز نیز نمایش داده میشود
                    // loadMenu(
                    //     currentDate.day,
                    //     currentDate.month,
                    //     currentDate.year
                    // )

                    loadAvailableItem()


                },
                error: function (xhr, status, error) {
                    console.error('Default calendar load failed!', status, 'and error:', error);
                }
            });

        },
        error: function (xhr, status, error) {
            console.error('Administrative is Unreachable', status, 'and' +
                ' error:', error);
        }
    });
    if (isSystemOpen === false) return

    $(document).on('click', '#dropdown-menu a', function () {
        // اضافه کردن یک غذا از منوی دراپ دان به منوی روز انتخاب شده


        let id = parseInt($(this).attr("data-item-id"))
        $.ajax({
            url: `administrative/add-item-to-menu/`,
            method: 'POST',
            dataType: 'json',
            data: {
                "id": id,
                "date": toShamsiFormat(selectedDate)
            },
            success: function (data) {
                addNewItemToMenu(id)
                updateSelectedItems(selectedDate.month, selectedDate.year)
            },
            error: function (xhr, status, error) {
                console.error('Item not added!', status, 'and error:', error);
            }
        });

    });

    $(document).on('click', '#menu-items-container li', function () {
        // حذف کردن یک غذا از منوی روز انتخاب شده
        let id = parseInt($(this).attr("data-item-id"))

        $.ajax({
            url: `administrative/remove-item-from-menu/`,
            method: 'POST',
            dataType: 'json',
            data: {
                "id": id,
                "date": toShamsiFormat(selectedDate)
            },
            success: function (data) {
                removeItemFromMenu(id)
                updateSelectedItems(selectedDate.month, selectedDate.year)
            },
            error: function (xhr, status, error) {
                console.error('Item not removed!', status, 'and error:', error);
            }
        });

    });

    $(document).on('click', '#dayBlocksWrapper div[data-date]', function () {
        selectDayOnCalendar($(this))
    })

    $(document).on('change', '#calSelectedMonth', function () {
        let monthNumber = getCurrentCalendarMonth()
        $.ajax({
            url: `administrative/calendar/?year=1402&month=${monthNumber}`,
            method: 'GET',
            dataType: 'json',

            success: function (data) {
                firstDayOfWeek = data[0]["firstDayOfWeek"]
                lastDayOfMonth = data[0]["lastDayOfMonth"]
                holidays = data[0]["holidays"]
                daysWithMenu = data[0]["daysWithMenu"]
                selectedItems = data[1]["SelectedItems"]
                makeCalendar(
                    parseInt(firstDayOfWeek),
                    parseInt(lastDayOfMonth),
                    holidays,
                    daysWithMenu,
                    monthNumber,
                    1402
                )
            },
            error: function (xhr, status, error) {
                console.error('Item not removed!', status, 'and error:', error);
            }
        });
    })


});

