import alert from "./x-alert.js";
import heroicon from "./x-heroicon.js";
import modal from "./x-modal.js";
import btnIcon from "./x-btn-icon.js";
import datepicker from "./x-datepicker.js";

export default function (Alpine) {
  Alpine.plugin(alert);
  Alpine.plugin(heroicon);
  Alpine.plugin(modal);
  Alpine.plugin(btnIcon);
  Alpine.plugin(datepicker);
}
