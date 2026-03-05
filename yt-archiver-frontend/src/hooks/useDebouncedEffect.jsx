import React, { useCallback, useEffect } from "react";
import debounce from "lodash/debounce";

const useDebounceEffect = (effect, deps, delay = 300) => {
  const debouncedEffect = useCallback(debounce(effect, delay), deps);

  useEffect(() => {
    debouncedEffect();
    return debouncedEffect.cancel;
  }, deps);
};


export default useDebounceEffect;