export const CONFIG = {
  appName: "YouTube Archiver",
  appVersion: "0.1.0",
};

const API_URL_DEV = "http://localhost:8000";
const API_URL_PROD = "";

const isProd = import.meta.env.PROD;

export const API_URL = isProd ? API_URL_PROD : API_URL_DEV;
