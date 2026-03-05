import Swal from "sweetalert2";
import { jwtDecode } from "jwt-decode";

export const showError = (error) => {
  let errMsg = error?.response?.data?.error || error?.response?.data?.msg || error?.response?.data?.message;

  if (!errMsg) {
    errMsg = error.message;
  }
  if (errMsg == "Token has expired") {
    return;
  }

  Swal.fire({
    title: errMsg,
    icon: "warning",
  });
};

export const showWarning = (title) => {
  Swal.fire({
    icon: "warning",
    title,
  });
};

export const findKeyByValue = (object, value) => {
  return Object.keys(object).find((key) => object[key] === value);
};

export const POPUP_TIME = 1000;

// export const cancelFullScreen = () => {
//   var el = document;
//   var requestMethod = el.cancelFullScreen || el.webkitCancelFullScreen || el.mozCancelFullScreen || el.exitFullscreen || el.webkitExitFullscreen;
//   if (requestMethod) {
//     // cancel full screen.
//     requestMethod.call(el);
//   } else if (typeof window.ActiveXObject !== "undefined") {
//     // Older IE.
//     var wscript = new ActiveXObject("WScript.Shell");
//     if (wscript !== null) {
//       wscript.SendKeys("{F11}");
//     }
//   }
// };

// export const requestFullScreen = (el) => {
//   // Supports most browsers and their versions.
//   var requestMethod = el.requestFullScreen || el.webkitRequestFullScreen || el.mozRequestFullScreen || el.msRequestFullscreen;

//   if (requestMethod) {
//     // Native full screen.
//     requestMethod.call(el);
//   } else if (typeof window.ActiveXObject !== "undefined") {
//     // Older IE.
//     var wscript = new ActiveXObject("WScript.Shell");
//     if (wscript !== null) {
//       wscript.SendKeys("{F11}");
//     }
//   }
//   return false;
// };

// export const toggleFullScreen = (el) => {
//   if (!el) {
//     el = document.body; // Make the body go full screen.
//   }
//   var isInFullScreen = (document.fullScreenElement && document.fullScreenElement !== null) || document.mozFullScreen || document.webkitIsFullScreen;

//   if (isInFullScreen) {
//     cancelFullScreen();
//   } else {
//     requestFullScreen(el);
//   }
//   return false;
// };

export const enterFullscreen = () => {
  const elem = document.documentElement;
  if (elem.requestFullscreen) {
    elem.requestFullscreen();
  } else if (elem.webkitRequestFullscreen) {
    /* Safari */
    elem.webkitRequestFullscreen();
  } else if (elem.msRequestFullscreen) {
    /* IE11 */
    elem.msRequestFullscreen();
  }
};

export const exitFullscreen = () => {
  if (document.exitFullscreen) {
    document.exitFullscreen();
  } else if (document.webkitExitFullscreen) {
    /* Safari */
    document.webkitExitFullscreen();
  } else if (document.msExitFullscreen) {
    /* IE11 */
    document.msExitFullscreen();
  }
};

export const checkExpiredJWT = (token) => {
  if (!token) return true;
  const decoded = jwtDecode(token);
  const current_time = Date.now() / 1000;
  return decoded.exp < current_time;
};
