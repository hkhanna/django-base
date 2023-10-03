export default function (Alpine) {
  Alpine.directive(
    "datepicker",
    (el, { value, modifiers, expression }, { effect, evaluateLater }) => {
      const evaluate = evaluateLater(expression || "{}");
      const fixed = modifiers.includes("fixed"); // Forces it open unconditionally
      const submit = modifiers.includes("submit"); // Submit on selection

      effect(() => {
        evaluate((expression) => {
          const inputName = expression.inputName || "";
          const initial = expression.initial || "";
          const min = expression.min || "";
          const max = expression.max || "";

          el.innerHTML = `
<div x-data="datepicker({fixed: ${fixed}, submit: ${submit}, initial: '${initial}', min: '${min}', max: '${max}'})" x-on:click.outside="datePickerOpen = false">
  <div class="w-full">
    <div class="relative w-[17rem]">
      <input
        x-ref="datePickerInput"
        type="text"
        ${inputName ? `name="${inputName}"` : ""}
        @click="datePickerOpen=!datePickerOpen"
        x-on:input="datePickerOpen=true"
        x-model="datePickerValue"
        x-on:keydown.escape="datePickerOpen=false"
        class="flex w-full h-10 px-3 py-2 text-sm bg-white border rounded-md text-neutral-600 border-neutral-300 ring-offset-background placeholder:text-neutral-400 focus:border-neutral-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-neutral-400 disabled:cursor-not-allowed disabled:opacity-50"
        placeholder="Select date"
      />
      <div @click="datePickerOpen=!datePickerOpen; if(datePickerOpen){ $refs.datePickerInput.focus() }" class="absolute top-0 right-0 px-3 py-2 cursor-pointer text-neutral-400 hover:text-neutral-500">
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <div class="text-red-600 text-xs mt-2" x-show="datePickerError" x-text="datePickerError"></div>
      <div
        x-show="datePickerOpen"
        x-transition
        x-bind:class="{
          'absolute top-0 left-0 mt-12': ${!fixed} && !datePickerError,
          'absolute top-0 left-0 mt-16': ${!fixed} && datePickerError,
          'mt-2': ${fixed},
          '${expression.datePickerOpenClass}': true
        }"
        class="max-w-lg w-[17rem] antialiased"
      >
        <div class="flex items-center justify-between mb-2">
          <div>
            <span x-text="datePickerMonthNames[datePickerMonth]" class="text-lg font-bold text-gray-800"></span>
            <span x-text="datePickerYear" class="ml-1 text-lg font-normal text-gray-600"></span>
          </div>
          <div>
            <button @click="datePickerPreviousMonth()" type="button" class="inline-flex p-1 transition duration-100 ease-in-out rounded-full cursor-pointer focus:outline-none focus:shadow-outline hover:bg-gray-100">
              <svg class="inline-flex w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
            </button>
            <button @click="datePickerNextMonth()" type="button" class="inline-flex p-1 transition duration-100 ease-in-out rounded-full cursor-pointer focus:outline-none focus:shadow-outline hover:bg-gray-100">
              <svg class="inline-flex w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
            </button>
          </div>
        </div>
        <div class="grid grid-cols-7 mb-3">
          <template x-for="(day, index) in datePickerDays" :key="index">
            <div class="px-0.5">
              <div x-text="day" class="text-xs font-medium text-center text-gray-800"></div>
            </div>
          </template>
        </div>
        <div class="grid grid-cols-7">
          <template x-for="blankDay in datePickerBlankDaysInMonth">
            <div class="p-1 text-sm text-center border border-transparent"></div>
          </template>
          <template x-for="(day, dayIndex) in datePickerDaysInMonth" :key="dayIndex">
            <div class="px-0.5 mb-1 aspect-square">
              <button
                type=${submit ? "submit" : "button"}
                x-text="day"
                @click="datePickerDayClicked(day)"
                :class="{
                                        'bg-neutral-200': datePickerIsToday(day) == true, 
                                        'text-gray-600 hover:bg-neutral-200': datePickerIsToday(day) == false && datePickerIsSelectedDate(day) == false,
                                        'bg-neutral-800 text-white hover:bg-opacity-75': datePickerIsSelectedDate(day) == true
                                    }"
                class="flex items-center justify-center text-sm leading-none text-center rounded-full h-7 w-7"
              ></button>
            </div>
          </template>
        </div>
        <div class="flex justify-end">
        <button type="button" class="btn btn-white btn-xs" x-on:click="datePickerSelectToday()">Today</button>
        </div>
      </div>
    </div>
  </div>
</div>
        `;
        });
      });
    }
  );

  Alpine.data("datepicker", ({ fixed, submit, initial, min, max }) => {
    return {
      _datePickerOpen: fixed || false,
      get datePickerOpen() {
        return this._datePickerOpen;
      },
      set datePickerOpen(value) {
        if (fixed) {
          this._datePickerOpen = true;
          return;
        }
        this._datePickerOpen = value;
      },
      datePickerValue: "",
      datePickerFormat: "M d, Y",
      datePickerMonth: "",
      datePickerYear: "",
      datePickerDay: "",
      datePickerDaysInMonth: [],
      datePickerBlankDaysInMonth: [],
      datePickerMonthNames: [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
      ],
      datePickerError: "",
      datePickerDays: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
      datePickerValueMin: "2023-01-01",
      get datePickerMin() {
        // Ensure the datestring is in the local timezone
        const [year, month, day] = this.datePickerValueMin
          .split("-")
          .map(Number);
        return new Date(year, month - 1, day);
      },
      datePickerValueMax: "2099-12-31",
      get datePickerMax() {
        // Ensure the datestring is in the local timezone
        const [year, month, day] = this.datePickerValueMax
          .split("-")
          .map(Number);
        return new Date(year, month - 1, day);
      },
      datePickerDayClicked(day) {
        let selectedDate = new Date(
          this.datePickerYear,
          this.datePickerMonth,
          day
        );

        if (selectedDate < this.datePickerMin) {
          this.datePickerError = `Please pick a date on or after ${this.datePickerFormatDate(
            this.datePickerMin
          )}.`;
          return;
        } else if (selectedDate > this.datePickerMax) {
          this.datePickerError = `Please pick a date on or before ${this.datePickerFormatDate(
            this.datePickerMax
          )}.`;
          return;
        }
        this.datePickerDay = day;
        this.datePickerValue = this.datePickerFormatDate(selectedDate);
        this.datePickerOpen = false;
      },
      datePickerPreviousMonth() {
        if (this.datePickerMonth == 0) {
          this.datePickerYear--;
          this.datePickerMonth = 12;
        }
        this.datePickerMonth--;
        this.datePickerCalculateDays();
      },
      datePickerNextMonth() {
        if (this.datePickerMonth == 11) {
          this.datePickerMonth = 0;
          this.datePickerYear++;
        } else {
          this.datePickerMonth++;
        }
        this.datePickerCalculateDays();
      },
      datePickerIsSelectedDate(day) {
        const d = new Date(this.datePickerYear, this.datePickerMonth, day);
        return this.datePickerValue === this.datePickerFormatDate(d)
          ? true
          : false;
      },
      datePickerIsToday(day) {
        const today = new Date();
        const d = new Date(this.datePickerYear, this.datePickerMonth, day);
        return today.toDateString() === d.toDateString() ? true : false;
      },
      datePickerCalculateDays() {
        let daysInMonth = new Date(
          this.datePickerYear,
          this.datePickerMonth + 1,
          0
        ).getDate();
        // find where to start calendar day of week
        let dayOfWeek = new Date(
          this.datePickerYear,
          this.datePickerMonth
        ).getDay();
        let blankdaysArray = [];
        for (var i = 1; i <= dayOfWeek; i++) {
          blankdaysArray.push(i);
        }
        let daysArray = [];
        for (var i = 1; i <= daysInMonth; i++) {
          daysArray.push(i);
        }
        this.datePickerBlankDaysInMonth = blankdaysArray;
        this.datePickerDaysInMonth = daysArray;
      },
      datePickerFormatDate(date) {
        let formattedDay = this.datePickerDays[date.getDay()];
        let formattedDate = ("0" + date.getDate()).slice(-2); // appends 0 (zero) in single digit date
        let formattedMonth = this.datePickerMonthNames[date.getMonth()];
        let formattedMonthShortName = this.datePickerMonthNames[
          date.getMonth()
        ].substring(0, 3);
        let formattedMonthInNumber = (
          "0" +
          (parseInt(date.getMonth()) + 1)
        ).slice(-2);
        let formattedYear = date.getFullYear();

        if (this.datePickerFormat === "M d, Y") {
          return `${formattedMonthShortName} ${formattedDate}, ${formattedYear}`;
        }
        if (this.datePickerFormat === "MM-DD-YYYY") {
          return `${formattedMonthInNumber}-${formattedDate}-${formattedYear}`;
        }
        if (this.datePickerFormat === "DD-MM-YYYY") {
          return `${formattedDate}-${formattedMonthInNumber}-${formattedYear}`;
        }
        if (this.datePickerFormat === "YYYY-MM-DD") {
          return `${formattedYear}-${formattedMonthInNumber}-${formattedDate}`;
        }
        if (this.datePickerFormat === "D d M, Y") {
          return `${formattedDay} ${formattedDate} ${formattedMonthShortName} ${formattedYear}`;
        }

        return `${formattedMonth} ${formattedDate}, ${formattedYear}`;
      },
      datePickerConformSelectionToValue(value) {
        this.datePickerMonth = value.getMonth();
        this.datePickerYear = value.getFullYear();
        this.datePickerDay = value.getDay();
        this.datePickerValue = this.datePickerFormatDate(value);
        this.datePickerCalculateDays();
      },
      datePickerSelectToday() {
        const today = new Date();
        if (this.datePickerValue === this.datePickerFormatDate(today)) {
          this.datePickerConformSelectionToValue(today);
        } else {
          this.datePickerValue = this.datePickerFormatDate(today);
        }
      },
      isValidDate(value) {
        const d = new Date(value);
        if (isNaN(d)) {
          return false;
        }
        if (d < this.datePickerMin || d > this.datePickerMax) {
          return false;
        }
        return true;
      },
      init() {
        let value = new Date();
        if (this.datePickerValue) {
          value = new Date(Date.parse(this.datePickerValue));
        }
        if (initial) {
          value = new Date(Date.parse(initial));
        }
        if (min) {
          this.datePickerValueMin = min;
        }
        if (max) {
          this.datePickerValueMax = max;
        }

        this.datePickerConformSelectionToValue(value);

        this.$watch("datePickerValue", (value) => {
          if (this.isValidDate(value)) {
            this.datePickerError = "";
            this.datePickerConformSelectionToValue(new Date(value));
          } else {
            this.datePickerError = "Please enter a valid date.";
          }
        });
      },
    };
  });
}
