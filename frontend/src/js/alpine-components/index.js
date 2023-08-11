import alert from "./alert.js";
import heroicon from "./heroicon.js";
import modal from "./modal.js";

export default function (Alpine) {
  Alpine.plugin(alert);
  Alpine.plugin(heroicon);
  Alpine.plugin(modal);
}
