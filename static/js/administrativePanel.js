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

function calendarDayBlock(dayCode, dayNumberStyle, dayNumber, dayMenuIcon) {
    return `<div class="${dayCode} flex flex-col items-center justify-between border border-gray-100 p-4 grow hover:bg-gray-200 hover:border-gray-300">
                                <div> 
                                    <span class="text-5xl ${dayNumberStyle}">${dayNumber}</span>
                                </div>
                                <div>
                                    <img class="w-10 h-10" src="${dayMenuIcon}" alt="">
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
        HTML += dropDownItemBlock(item.id, item.ItemName)
    })
    return HTML
}

function loadAdministrativeProfile() {

}


function loadMenu(day, month, year, allMenus) {
    // منوی قبلی را پاک می کنیم
    $("#menu-items-container").remove()

    let requestedDate = `${year}/${month}/${day}`
    let selectedMenu = allMenus.find(function (entry) {
        return entry.date === requestedDate;
    });

    // حالا باید آیتم هارو بگیریم
}

function makeCalendar(startDayOfWeek, endDayOfMonth, holidays, daysWithMenu) {

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
        startDayOfWeek++
        let dayCode = `cd-${dayNumber}-${startDayOfWeek % 7}`
        let dayNumberStyle = ""
        let dayMenuIcon = "https://www.svgrepo.com/show/383690/food-dish.svg"

        // در صورتی که روز تعطیل بود اون رو قرمز می کنیم
        if (holidays.includes(dayNumber)) {
            dayNumberStyle = "text-red-500"
        }

        // در صورتی که توسط اداری برای اون روز منو تعیین شده بود آن ایکن را
        // تغییر می دهیم
        if (daysWithMenu.includes(dayNumber)) {
            dayMenuIcon = "https://www.svgrepo.com/show/390075/food-dish.svg"
        }

        newCalendarHTML += calendarDayBlock(dayCode, dayNumberStyle, dayNumber, dayMenuIcon)
    }
    $("#dayBlocksWrapper").append(newCalendarHTML)
}

function displaySystemIsNotAvailable() {

}

function blurMainPanel() {

}

function addNewItemToMenu(id) {
    let selectedItem = availableItems.find(item => item.id == id);
    $("#menu-items-container").append(
        menuItemBlock(selectedItem.id, selectedItem.ItemName, selectedItem.Image)
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
        dropDownItemBlock(id, selectedItem.ItemName)
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

function updateSelectedDate() {

}
function getCurrentCalendarMonth() {
    return $("#calSelectedMonth option:selected").attr("value")
}

$(document).ready(function () {
    let isSystemOpen = undefined
    let currentDate = {
        year: undefined,
        month: undefined,
        day: undefined
    }
    let selectedDate = {
        year: 1402,
        month: 12,
        day: 1
    }
    let personnelFullName = undefined
    let personnelProfileImg = undefined
    let firstDayOfWeek = undefined
    let lastDayOfMonth = undefined
    let holidays = undefined
    let daysWithMenu = undefined
    let orderedDays = undefined
    let selectedItems = undefined
    let availableItems = undefined


    /* وقتی که صفحه به صورت کامل لود شد کار های زیر را به ترتیب انجام می دهیم
    */


    $.ajax({
        url: `administrative/panel/`,
        method: 'GET',
        dataType: 'json',
        async: false,
        success: function (data) {
            console.log(data)
            isSystemOpen = data["is_open"]
            currentDate.day = data["current_date"]["day"]
            currentDate.month = data["current_date"]["month"]
            currentDate.year = data["current_date"]["year"]

            // در صورتی که سیستم قابل استفاده نبود و می خواست از دسترس
            // خارج شه
            if (isSystemOpen === false) {
                displaySystemIsNotAvailable()
                blurMainPanel()
                return
            }

            $.ajax({
                url: `administrative/calendar/?month=${currentDate.month}`,
                method: 'GET',
                dataType: 'json',
                success: function (data) {
                    console.log(data)
                    firstDayOfWeek = data[0]["firstDayOfWeek"]
                    lastDayOfMonth = data[0]["lastDayOfMonth"]
                    holidays = data[0]["holidays"]
                    daysWithMenu = data[0]["daysWithMenu"]
                    selectedItems = data[1]["SelectedItems"]

                    // تقویم این ماه به صورت پیشفرض لود می شود
                    makeCalendar(
                        firstDayOfWeek,
                        lastDayOfMonth,
                        holidays,
                        daysWithMenu
                    )

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

    $(document).on('click', '#dropdown-menu a', function () {
        let id = $(this).attr("data-item-id")
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
            },
            error: function (xhr, status, error) {
                console.error('Item not added!', status, 'and error:', error);
            }
        });

    });

    $(document).on('click', '#menu-items-container li', function () {
        let id = $(this).attr("data-item-id")

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
            },
            error: function (xhr, status, error) {
                console.error('Item not removed!', status, 'and error:', error);
            }
        });

    });




});