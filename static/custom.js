/*
هنگام تغییر تقویم برای دوباره ساختن آن نیازمند این که روز اول ماه چه روزی
 از هفته است می باشیم علاوه بر این باید بدانیم که ماه 29 یا 30 یا 31 روزه است
* @param {Number} startDayOfWeek
* @param {Number} endDayOfMonth
* @param {Array} holidays
* @param {Array} daysWithMenu شماره روز هایی که اداری منوی آنها را ثبت کرده است
* */
function makeCalender(startDayOfWeek, endDayOfMonth, holidays, daysWithMenu) {

// ابتدا باید تقویم قبلی را پاگ کنیم
    $('#dayBlocksWrapper [class^="cd-"]').remove()

    let newCalendarHTML = ""
//     حال باید با توجه به روز این روز اول ماه چند شنبه است بلاک های روز
//     های ما قبل آن خاکستری کنیم
    for (let i = 1; i < startDayOfWeek; i++) {
    newCalendarHTML += '<div class="cd- flex flex-col items-center bg-gray-50 border border-gray-100 p-4 grow"></div>'
}

//     سپس به سراغ ساخت بلاک روز های دیگر می کنیم. در صورتی روز مورد نظر
//     تعطیل بود باید شماره روز را رنگی کنیم و در همچنین وضعیت ثبت منو توسط
//     اداری را در آن روز به نمایش بگذاریم
    for(let dayNumber=1; dayNumber<=endDayOfMonth; dayNumber++){
        startDayOfWeek++
        let dayCode = `cd-${dayNumber}-${startDayOfWeek%7}`
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

        newCalendarHTML += `<div class="${dayCode} flex flex-col items-center justify-between border border-gray-100 p-4 grow hover:bg-gray-200 hover:border-gray-300">
                                <div>
                                    <span class="text-5xl ${dayNumberStyle}">${dayNumber}</span>
                                </div>
                                <div>
                                    <img class="w-10 h-10" src="${dayMenuIcon}" alt="">
                                </div>
                            </div>`
    }


    $("#dayBlocksWrapper").append(newCalendarHTML)


}

$(document).ready(function () {

    $("#calSelectedMonth").change(function () {
        // از این تابع برای تغییر ماه تقویم استفاده می شود در صورتی که
        // داده ای برای ماه مورد نظر وجود نداشته باشد alert عدم وجود دیتا
        // به کاربر نشان داده می شود

        let monthNumber = $("#calSelectedMonth option:selected").attr("value")
        //     ajax call to backend
        makeCalender(3,30,[5,12,19,26],[20])
    })


});