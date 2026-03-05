export const CameraDropdownOptions = ["camera_1", "camera_2", "camera_3", "camera_4"];
export const LightsDropdownOptions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
export const SideDropdownOptions = ["left", "right"];

export const variantNameDictToStr = (variantData) => {
  return `${variantData.make}_${variantData.product}_${variantData.finish}_${variantData.type}_${variantData.opening}_${variantData.height}_${variantData.orientation}`;
};

export const variantNameStrToDict = (selectedVariant) => {
  const variantData = {
    make: "",
    product: "",
    finish: "",
    type: "",
    opening: "",
    height: "",
    orientation: "",
  };

  if (!selectedVariant) return variantData;

  const [
    make = "",
    product = "",
    finish = "",
    type = "",
    opening = "",
    height = "",
    orientation = "",
  ] = selectedVariant.split("_");

  variantData.make = make;
  variantData.product = product;
  variantData.finish = finish;
  variantData.type = type;
  variantData.opening = opening;
  variantData.height = height;
  variantData.orientation = orientation;

  return variantData;
};

export const getToolName = (name) => {
  if (name == "line") {
    return "create-line";
  } else if (name == "drag_box") {
    return "create-box";
  } else if (name == "point") {
    return "create-point";
  } else {
    return "";
  }
};

export const deleteVariantFromDict = (dbVariants, variant, side, camera, defect) => {
  delete dbVariants[variant][side][camera][defect];

  if (!Object.keys(dbVariants[variant][side][camera]).length) {
    delete dbVariants[variant][side][camera];
  }

  if (!Object.keys(dbVariants[variant][side]).length) {
    delete dbVariants[variant][side];
  }

  if (!Object.keys(dbVariants[variant]).length) {
    delete dbVariants[variant];
  }

  return dbVariants;
};

export const createVariantInDict = (dbVariants, variant, side, camera, defect, data) => {
  if (dbVariants[variant] == undefined) {
    dbVariants[variant] = {};
  }

  if (dbVariants[variant][side] == undefined) {
    dbVariants[variant][side] = {};
  }

  if (dbVariants[variant][side][camera] == undefined) {
    dbVariants[variant][side][camera] = {};
  }

  if (dbVariants[variant][side][camera][defect] == undefined) {
    dbVariants[variant][side][camera][defect] = {};
  }

  dbVariants[variant][side][camera][defect] = data;

  return dbVariants;
};
