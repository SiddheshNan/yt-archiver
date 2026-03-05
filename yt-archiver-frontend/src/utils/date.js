export const getUtcTime = (...items) => {
  const dt = new Date();
  dt.setUTCHours(...items);
  return dt;
};
